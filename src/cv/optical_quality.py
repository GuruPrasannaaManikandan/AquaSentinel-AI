import os
import io
import json
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union, Tuple
from PIL import Image

@dataclass
class VisualQualityResult:
    """
    V6 Deterministic Visual Quality Contract.
    Encapsulates optical quality metrics, physical degradation reasons, and frame freshness.
    """
    q_visual: float
    sharpness: float
    brightness: float
    contrast: float
    glare: bool
    freshness: str
    degradation_reasons: List[str]
    valid: bool
    quality_state: str = "RELIABLE"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpticalQualityResult:
    """
    Structured outcome of optical quality assessment on a single image frame.
    Produces deterministic Q_visual in [0.0, 1.0], sharpness, exposure, contrast,
    and traceable fault flags.
    """
    q_visual: float
    quality_state: str  # "RELIABLE", "ACCEPTABLE", "DEGRADED", "UNRELIABLE", "CORRUPTED"
    sharpness_score: float
    exposure_score: float
    contrast_score: float
    entropy_score: float
    sharpness_variance: float
    mean_luminance: float
    luminance_std: float
    quality_flags: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_visual_quality_result(self, freshness: str = "FRESH") -> VisualQualityResult:
        """Converts to V6 VisualQualityResult schema."""
        has_glare = any("GLARE" in f for f in self.quality_flags + self.reason_codes)
        is_valid = self.quality_state in ["RELIABLE", "ACCEPTABLE"] and self.q_visual >= 0.40
        return VisualQualityResult(
            q_visual=round(float(self.q_visual), 4),
            sharpness=round(float(self.sharpness_score), 4),
            brightness=round(float(self.mean_luminance), 2),
            contrast=round(float(self.contrast_score), 4),
            glare=has_glare,
            freshness=self.metadata.get("freshness", freshness),
            degradation_reasons=list(self.reason_codes),
            valid=is_valid,
            quality_state=self.quality_state,
            metadata=dict(self.metadata)
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sharpness"] = round(float(self.sharpness_score), 4)
        d["brightness"] = round(float(self.mean_luminance), 2)
        d["contrast"] = round(float(self.contrast_score), 4)
        d["glare"] = any("GLARE" in f for f in self.quality_flags + self.reason_codes)
        d["freshness"] = self.metadata.get("freshness", "FRESH")
        d["degradation_reasons"] = list(self.reason_codes)
        d["valid"] = self.quality_state in ["RELIABLE", "ACCEPTABLE"] and self.q_visual >= 0.40
        return d

    def format_summary(self) -> str:
        lines = [
            "==================================================",
            "        V5.2 OPTICAL QUALITY REPORT               ",
            "==================================================",
            f"Overall Visual Quality (Q_visual): {self.q_visual:.4f}",
            f"Quality State:                    {self.quality_state}",
            f"Sharpness Variance:               {self.sharpness_variance:.2f} (score: {self.sharpness_score:.2f})",
            f"Mean Luminance:                   {self.mean_luminance:.2f} (score: {self.exposure_score:.2f})",
            f"Entropy / Contrast:               {self.entropy_score:.2f} bits (score: {self.contrast_score:.2f})",
            f"Quality Flags:                    {', '.join(self.quality_flags) if self.quality_flags else 'NONE'}",
        ]
        if self.reason_codes:
            lines.append("Degradation Explanations:")
            for code in self.reason_codes:
                lines.append(f"  • {code}")
        lines.append("==================================================")
        return "\n".join(lines)


class OpticalQualityEvaluator:
    """
    Hardware-independent, deterministic optical quality assessment engine.
    Evaluates frame integrity, Laplacian blur, luminance exposure histograms,
    and Shannon information entropy to produce a bounded Q_visual in [0.0, 1.0].
    """
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "config",
                "optical_quality_config.json"
            )
        self.config_path = config_path
        self.config = self._load_config(config_path)

        sharp = self.config.get("sharpness", {})
        self.blur_threshold = sharp.get("blur_threshold_variance", 100.0)
        self.sharp_threshold = sharp.get("sharp_threshold_variance", 300.0)

        expo = self.config.get("exposure", {})
        self.dark_threshold = expo.get("dark_mean_luminance_threshold", 30.0)
        self.overexposed_threshold = expo.get("overexposed_mean_luminance_threshold", 225.0)
        self.sat_threshold = expo.get("saturation_fraction_threshold", 0.60)

        cont = self.config.get("contrast", {})
        self.min_std_dev = cont.get("min_std_dev", 15.0)
        self.min_entropy = cont.get("min_shannon_entropy", 3.5)

        weights = self.config.get("scoring_weights", {})
        self.w_sharp = weights.get("sharpness", 0.40)
        self.w_exp = weights.get("exposure", 0.35)
        self.w_cont = weights.get("contrast", 0.25)

        states = self.config.get("quality_state_thresholds", {})
        self.thresh_reliable = states.get("reliable", 0.85)
        self.thresh_acceptable = states.get("acceptable", 0.65)
        self.thresh_degraded = states.get("degraded", 0.40)

    def _load_config(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load optical config from {path}: {e}")
        return {}

    def evaluate_image(
        self,
        image_input: Union[bytes, Image.Image, np.ndarray],
        frame_id: Optional[str] = None
    ) -> OpticalQualityResult:
        """
        Main entry point for optical quality evaluation.
        Accepts raw JPEG bytes, PIL Image, or NumPy array.
        Returns OpticalQualityResult. Never raises exceptions to the caller.
        """
        # Step 1: Decode and Validate Integrity
        pil_img, err_flag, err_msg = self._decode_and_validate(image_input)
        if pil_img is None:
            return OpticalQualityResult(
                q_visual=0.0,
                quality_state="CORRUPTED",
                sharpness_score=0.0,
                exposure_score=0.0,
                contrast_score=0.0,
                entropy_score=0.0,
                sharpness_variance=0.0,
                mean_luminance=0.0,
                luminance_std=0.0,
                quality_flags=[err_flag or "CORRUPTED"],
                reason_codes=[err_msg or "Image decode failure / corrupted payload"],
                metadata={"frame_id": frame_id, "error": err_msg}
            )

        # Convert to Grayscale Luminance
        try:
            gray_img = pil_img.convert("L")
            gray_arr = np.array(gray_img, dtype=np.float32)
        except Exception as e:
            return OpticalQualityResult(
                q_visual=0.0,
                quality_state="CORRUPTED",
                sharpness_score=0.0,
                exposure_score=0.0,
                contrast_score=0.0,
                entropy_score=0.0,
                sharpness_variance=0.0,
                mean_luminance=0.0,
                luminance_std=0.0,
                quality_flags=["ARRAY_CONVERSION_ERROR"],
                reason_codes=[f"Failed to convert image to array: {e}"],
                metadata={"frame_id": frame_id}
            )

        quality_flags: List[str] = []
        reason_codes: List[str] = []

        # Step 2: Sharpness / Blur Evaluation via Variance of Laplacian
        sharp_score, sharp_var, sharp_flags, sharp_reasons = self._evaluate_sharpness(gray_arr)
        quality_flags.extend(sharp_flags)
        reason_codes.extend(sharp_reasons)

        # Step 3: Exposure & Lighting Evaluation
        exp_score, mean_lum, exp_flags, exp_reasons = self._evaluate_exposure(gray_arr)
        quality_flags.extend(exp_flags)
        reason_codes.extend(exp_reasons)

        # Step 4: Contrast & Information Content (Shannon Entropy)
        cont_score, ent_score, lum_std, cont_flags, cont_reasons = self._evaluate_contrast_and_entropy(gray_arr)
        quality_flags.extend(cont_flags)
        reason_codes.extend(cont_reasons)

        # Step 5: Composite Q_visual Calculation
        q_vis, q_state = self._compute_composite_q(
            sharp_score=sharp_score,
            exp_score=exp_score,
            cont_score=cont_score,
            flags=quality_flags
        )

        return OpticalQualityResult(
            q_visual=q_vis,
            quality_state=q_state,
            sharpness_score=round(sharp_score, 4),
            exposure_score=round(exp_score, 4),
            contrast_score=round(cont_score, 4),
            entropy_score=round(ent_score, 4),
            sharpness_variance=round(sharp_var, 2),
            mean_luminance=round(mean_lum, 2),
            luminance_std=round(lum_std, 2),
            quality_flags=quality_flags,
            reason_codes=reason_codes,
            metadata={
                "frame_id": frame_id,
                "image_width": pil_img.width,
                "image_height": pil_img.height,
                "components": {
                    "sharpness": round(sharp_score, 4),
                    "exposure": round(exp_score, 4),
                    "contrast": round(cont_score, 4)
                }
            }
        )

    def _decode_and_validate(
        self,
        inp: Union[bytes, Image.Image, np.ndarray]
    ) -> Tuple[Optional[Image.Image], Optional[str], Optional[str]]:
        """Validates payload and decodes into a PIL Image."""
        if inp is None:
            return None, "NULL_INPUT", "Image input is None"

        if isinstance(inp, bytes):
            if len(inp) == 0:
                return None, "EMPTY_PAYLOAD", "Zero-length image bytes"
            try:
                img = Image.open(io.BytesIO(inp))
                img.verify()  # verify integrity
                # Image.verify leaves the stream at the end, re-open for decoding
                img = Image.open(io.BytesIO(inp))
                img.load()
            except Exception as e:
                return None, "CORRUPTED", f"Corrupt or invalid image stream: {e}"
        elif isinstance(inp, Image.Image):
            img = inp
            try:
                img.load()
            except Exception as e:
                return None, "CORRUPTED", f"Failed to load PIL image: {e}"
        elif isinstance(inp, np.ndarray):
            if inp.size == 0:
                return None, "EMPTY_ARRAY", "Zero-sized NumPy array"
            try:
                if inp.dtype != np.uint8 and np.max(inp) <= 1.0:
                    inp = (inp * 255.0).astype(np.uint8)
                else:
                    inp = inp.astype(np.uint8)
                img = Image.fromarray(inp)
            except Exception as e:
                return None, "ARRAY_ERROR", f"Failed to create PIL Image from array: {e}"
        else:
            return None, "UNSUPPORTED_TYPE", f"Unsupported image input type: {type(inp)}"

        if img.width <= 0 or img.height <= 0:
            return None, "INVALID_DIMENSIONS", f"Invalid dimensions: {img.size}"

        return img, None, None

    def _evaluate_sharpness(self, gray: np.ndarray) -> Tuple[float, float, List[str], List[str]]:
        """
        Computes sharpness via discrete Laplacian convolution variance:
        Kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        """
        h, w = gray.shape
        if h < 3 or w < 3:
            return 0.20, 0.0, ["LOW_RESOLUTION"], ["Image dimensions too small for Laplacian filter"]

        # Fast 2D discrete Laplacian convolution using NumPy vector slicing
        laplacian = (
            gray[0:-2, 1:-1] +
            gray[2:, 1:-1] +
            gray[1:-1, 0:-2] +
            gray[1:-1, 2:] -
            4.0 * gray[1:-1, 1:-1]
        )

        sharp_var = float(np.var(laplacian))
        flags = []
        reasons = []

        if sharp_var < self.blur_threshold:
            flags.append("BLURRED")
            reasons.append(f"Image sharpness variance is low ({sharp_var:.1f} < {self.blur_threshold:.1f}): frame is blurred")
            score = max(0.10, min(0.60, (sharp_var / self.blur_threshold) * 0.60))
        elif sharp_var >= self.sharp_threshold:
            score = 1.0
        else:
            # Linear scale between blur_threshold (0.60) and sharp_threshold (1.0)
            norm = (sharp_var - self.blur_threshold) / (self.sharp_threshold - self.blur_threshold)
            score = 0.60 + (0.40 * norm)

        return float(score), sharp_var, flags, reasons

    def _evaluate_exposure(self, gray: np.ndarray) -> Tuple[float, float, List[str], List[str]]:
        """
        Evaluates exposure via mean luminance and extreme saturation fractions.
        """
        mean_lum = float(np.mean(gray))
        flags = []
        reasons = []

        if mean_lum < self.dark_threshold:
            flags.append("DARK")
            reasons.append(f"Severe underexposure: mean luminance is dark ({mean_lum:.1f} < {self.dark_threshold:.1f})")
            score = max(0.05, (mean_lum / self.dark_threshold) * 0.40)
        elif mean_lum > self.overexposed_threshold:
            flags.append("OVEREXPOSED")
            reasons.append(f"Severe overexposure: mean luminance is saturated ({mean_lum:.1f} > {self.overexposed_threshold:.1f})")
            over_delta = 255.0 - mean_lum
            score = max(0.05, (over_delta / (255.0 - self.overexposed_threshold)) * 0.40)
        else:
            # Check saturation proportion
            sat_count = np.sum((gray < 10.0) | (gray > 245.0))
            sat_fraction = float(sat_count / gray.size)

            # Localized specular highlight / glare check (bright spot: gray >= 250)
            glare_count = np.sum(gray >= 250.0)
            glare_fraction = float(glare_count / gray.size)

            if sat_fraction > self.sat_threshold:
                flags.append("HIGH_SATURATION")
                reasons.append(f"High pixel saturation fraction ({sat_fraction*100.0:.1f}% > {self.sat_threshold*100.0:.1f}%)")
                score = max(0.20, 1.0 - sat_fraction)
            elif glare_fraction >= 0.08:
                flags.append("GLARE_DETECTED")
                reasons.append(f"Specular reflection/sunlight glare detected ({glare_fraction*100.0:.1f}% saturated highlights)")
                score = max(0.40, 1.0 - (glare_fraction * 1.5))
            else:
                # Normal balanced exposure: distance from ideal midpoint (128.0)
                deviation = abs(mean_lum - 128.0) / 128.0
                score = max(0.70, 1.0 - (deviation * 0.30))

        return float(score), mean_lum, flags, reasons

    def _evaluate_contrast_and_entropy(self, gray: np.ndarray) -> Tuple[float, float, float, List[str], List[str]]:
        """
        Evaluates information richness using Shannon entropy and luminance standard deviation.
        """
        lum_std = float(np.std(gray))
        flags = []
        reasons = []

        # Shannon entropy of 8-bit histogram
        counts, _ = np.histogram(gray, bins=256, range=(0, 256))
        total_px = gray.size
        probs = counts[counts > 0] / total_px
        entropy = float(-np.sum(probs * np.log2(probs)))

        if entropy < self.min_entropy:
            flags.append("LOW_INFORMATION")
            reasons.append(f"Low information content: Shannon entropy is {entropy:.2f} bits (< {self.min_entropy:.2f} bits)")
            score = max(0.05, (entropy / self.min_entropy) * 0.50)
        elif lum_std < self.min_std_dev:
            flags.append("LOW_CONTRAST")
            reasons.append(f"Low contrast: luminance standard deviation is {lum_std:.1f} (< {self.min_std_dev:.1f})")
            score = max(0.20, (lum_std / self.min_std_dev) * 0.60)
        else:
            # Normal contrast: scaled up to 1.0 based on entropy
            score = min(1.0, 0.60 + 0.40 * min(1.0, entropy / 6.0))

        return float(score), entropy, lum_std, flags, reasons

    def _compute_composite_q(
        self,
        sharp_score: float,
        exp_score: float,
        cont_score: float,
        flags: List[str]
    ) -> Tuple[float, str]:
        """
        Computes composite, bounded Q_visual in [0.0, 1.0] with critical discounts.
        """
        base_q = (self.w_sharp * sharp_score) + (self.w_exp * exp_score) + (self.w_cont * cont_score)

        # Multiplicative penalty for severe optical lighting/corruption faults
        if "DARK" in flags or "OVEREXPOSED" in flags:
            base_q *= 0.60
        elif "GLARE_DETECTED" in flags:
            base_q *= 0.85
        if "CORRUPTED" in flags:
            base_q = 0.0

        q_vis = round(float(max(0.0, min(1.0, base_q))), 4)

        if q_vis >= self.thresh_reliable:
            state = "RELIABLE"
        elif q_vis >= self.thresh_acceptable:
            state = "ACCEPTABLE"
        elif q_vis >= self.thresh_degraded:
            state = "DEGRADED"
        else:
            state = "UNRELIABLE"

        return q_vis, state
