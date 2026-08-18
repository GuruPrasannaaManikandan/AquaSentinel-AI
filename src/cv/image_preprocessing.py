import io
import time
import logging
import datetime
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List
from PIL import Image, ImageOps

from src.cv.camera_driver import CameraFrame

@dataclass
class PreprocessedImage:
    """
    Structured container for preprocessed image tensors.
    Carries model-ready array/tensor data ready for CV inference along with complete provenance.
    """
    frame_id: str
    timestamp: str  # ISO-8601 string linked to original CameraFrame
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    channels: int
    color_space: str  # "RGB", "BGR"
    data_format: str  # "HWC", "NHWC"
    dtype: str        # "float32", "uint8"
    tensor_data: Optional[np.ndarray] = None
    valid: bool = True
    status: str = "OK"  # "OK", "NULL_FRAME", "EMPTY_PAYLOAD", "DECODE_FAILURE", "UNSUPPORTED_FORMAT", "CORRUPTED", "CAMERA_OFFLINE", "PREPROCESSING_ERROR"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImagePreprocessor:
    """
    Hardware-independent, model-ready image preprocessing pipeline.
    Accepts generic CameraFrame instances (from physical ESP32-CAM or VirtualCameraDriver)
    and produces standardized PreprocessedImage outputs for CV model consumption.
    """
    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),  # (width, height)
        color_space: str = "RGB",
        aspect_ratio_mode: str = "STRETCH",  # "STRETCH", "LETTERBOX", "CROP"
        normalization_type: str = "RESCALE",  # "RESCALE" (0..1), "STANDARD" (mean/std), "NONE" (0..255)
        mean: Optional[List[float]] = None,    # e.g., [0.485, 0.456, 0.406]
        std: Optional[List[float]] = None,     # e.g., [0.229, 0.224, 0.225]
        expand_batch_dim: bool = False,
        config: Optional[dict] = None
    ):
        self.target_size = target_size
        self.color_space = color_space.upper()
        self.aspect_ratio_mode = aspect_ratio_mode.upper()
        self.normalization_type = normalization_type.upper()
        self.mean = np.array(mean if mean is not None else [0.0, 0.0, 0.0], dtype=np.float32)
        self.std = np.array(std if std is not None else [1.0, 1.0, 1.0], dtype=np.float32)
        self.expand_batch_dim = expand_batch_dim
        self.config = config or {}

    def validate_input(self, frame: CameraFrame) -> Tuple[bool, str]:
        """
        Validates the input CameraFrame quality, status, and byte payload.
        Returns (is_valid, status_code).
        """
        if frame is None:
            return False, "NULL_FRAME"
        if not frame.quality_valid:
            return False, frame.status or "INVALID_FRAME"
        if not frame.image_bytes or len(frame.image_bytes) == 0:
            return False, "EMPTY_PAYLOAD"
        if frame.status not in ["OK", "SUCCESS"]:
            return False, frame.status
        return True, "OK"

    def _apply_aspect_ratio_resize(self, pil_img: Image.Image) -> Image.Image:
        """Applies configured aspect ratio strategy (STRETCH, LETTERBOX, or CROP)."""
        target_w, target_h = self.target_size
        orig_w, orig_h = pil_img.size

        if (orig_w, orig_h) == (target_w, target_h):
            return pil_img

        if self.aspect_ratio_mode == "LETTERBOX":
            # Scale image maintaining aspect ratio and pad borders with neutral gray
            ratio = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            resized_img = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)

            # Create padded background container
            padded_img = Image.new("RGB", (target_w, target_h), color=(128, 128, 128))
            pad_x = (target_w - new_w) // 2
            pad_y = (target_h - new_h) // 2
            padded_img.paste(resized_img, (pad_x, pad_y))
            return padded_img

        elif self.aspect_ratio_mode == "CROP":
            # Center crop preserving aspect ratio
            ratio = max(target_w / orig_w, target_h / orig_h)
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
            resized_img = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            return resized_img.crop((left, top, left + target_w, top + target_h))

        else: # STRETCH
            return pil_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

    def process(self, frame: CameraFrame) -> PreprocessedImage:
        """
        Executes complete preprocessing pipeline on a CameraFrame.
        Measures processing latency, applies color conversion and normalization,
        and returns a structured PreprocessedImage linked to the source frame.
        """
        start_time = time.perf_counter()

        # Step 1: Input Validation
        is_valid, validation_status = self.validate_input(frame)
        if not is_valid:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return PreprocessedImage(
                frame_id=frame.frame_id if frame else "UNKNOWN",
                timestamp=frame.timestamp if frame else datetime.datetime.now().isoformat(),
                original_width=frame.width if frame else 0,
                original_height=frame.height if frame else 0,
                processed_width=self.target_size[0],
                processed_height=self.target_size[1],
                channels=3,
                color_space=self.color_space,
                data_format="NHWC" if self.expand_batch_dim else "HWC",
                dtype="float32" if self.normalization_type != "NONE" else "uint8",
                tensor_data=None,
                valid=False,
                status=validation_status,
                metadata={
                    "preprocessing_time_ms": duration_ms,
                    "source_metadata": frame.metadata if frame else {}
                }
            )

        # Step 2: Image Decoding
        pil_img = frame.to_pil_image()
        if pil_img is None:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return PreprocessedImage(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                original_width=frame.width,
                original_height=frame.height,
                processed_width=self.target_size[0],
                processed_height=self.target_size[1],
                channels=3,
                color_space=self.color_space,
                data_format="NHWC" if self.expand_batch_dim else "HWC",
                dtype="float32" if self.normalization_type != "NONE" else "uint8",
                tensor_data=None,
                valid=False,
                status="DECODE_FAILURE",
                metadata={
                    "preprocessing_time_ms": duration_ms,
                    "source_metadata": frame.metadata
                }
            )

        try:
            orig_w, orig_h = pil_img.size

            # Ensure 3-channel RGB format
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            # Step 3: Aspect Ratio Resize
            pil_img = self._apply_aspect_ratio_resize(pil_img)
            target_w, target_h = self.target_size

            # Step 4: Color Space Conversion & NumPy Formatting
            arr = np.array(pil_img) # (H, W, C)

            if self.color_space == "BGR":
                arr = arr[:, :, ::-1]  # RGB to BGR

            # Step 5: Normalization Pipeline
            if self.normalization_type == "RESCALE":
                arr = arr.astype(np.float32) / 255.0
                dtype_str = "float32"
            elif self.normalization_type == "STANDARD":
                arr = arr.astype(np.float32) / 255.0
                arr = (arr - self.mean) / self.std
                dtype_str = "float32"
            else: # NONE
                dtype_str = "uint8"

            # Step 6: Batch Dimension Formatting
            data_fmt = "HWC"
            if self.expand_batch_dim:
                arr = np.expand_dims(arr, axis=0) # (1, H, W, C)
                data_fmt = "NHWC"

            # Step 7: Latency Measurement & Metadata Output
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            meta = {
                "preprocessing_time_ms": round(duration_ms, 3),
                "normalization_type": self.normalization_type,
                "color_space": self.color_space,
                "aspect_ratio_mode": self.aspect_ratio_mode,
                "target_size": self.target_size,
                "source_metadata": frame.metadata
            }

            return PreprocessedImage(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                original_width=orig_w,
                original_height=orig_h,
                processed_width=target_w,
                processed_height=target_h,
                channels=3,
                color_space=self.color_space,
                data_format=data_fmt,
                dtype=dtype_str,
                tensor_data=arr,
                valid=True,
                status="OK",
                metadata=meta
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logging.error(f"Image preprocessing failure: {e}")
            return PreprocessedImage(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                original_width=frame.width,
                original_height=frame.height,
                processed_width=self.target_size[0],
                processed_height=self.target_size[1],
                channels=3,
                color_space=self.color_space,
                data_format="NHWC" if self.expand_batch_dim else "HWC",
                dtype="float32" if self.normalization_type != "NONE" else "uint8",
                tensor_data=None,
                valid=False,
                status="PREPROCESSING_ERROR",
                metadata={
                    "error": str(e),
                    "preprocessing_time_ms": round(duration_ms, 3),
                    "source_metadata": frame.metadata
                }
            )
