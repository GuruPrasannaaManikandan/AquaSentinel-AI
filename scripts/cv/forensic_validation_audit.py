import os
import time
import json
import hashlib
import numpy as np
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
import torch.nn as nn
from torchvision import models, transforms

def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of an image file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_forensic_audit():
    print("=== STARTING V4.3 MODEL & DATASET FORENSIC AUDIT ===")
    split_path = "data/cv_processed/split_metadata.json"
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split metadata not found at {split_path}")

    with open(split_path, "r") as f:
        split_data = json.load(f)

    train_items = split_data["train"]
    val_items = split_data["val"]
    test_items = split_data["test"]

    # 1. Grouping & Split Isolation Audit
    train_obs = set(x["observation_id"] for x in train_items)
    val_obs = set(x["observation_id"] for x in val_items)
    test_obs = set(x["observation_id"] for x in test_items)

    overlap_train_val = train_obs.intersection(val_obs)
    overlap_train_test = train_obs.intersection(test_obs)
    overlap_val_test = val_obs.intersection(test_obs)

    group_leakage = len(overlap_train_val) + len(overlap_train_test) + len(overlap_val_test)

    # 2. Duplicate SHA-256 Hash Audit Across Splits
    hashes = {}
    duplicate_leakage_count = 0
    duplicate_details = []

    for split_name, items in [("train", train_items), ("val", val_items), ("test", test_items)]:
        for item in items:
            f_hash = compute_file_hash(item["filepath"])
            if f_hash in hashes:
                prev_split, prev_id = hashes[f_hash]
                duplicate_details.append({
                    "hash": f_hash,
                    "image1": (prev_split, prev_id),
                    "image2": (split_name, item["image_id"])
                })
                if prev_split != split_name:
                    duplicate_leakage_count += 1
            else:
                hashes[f_hash] = (split_name, item["image_id"])

    # 3. Class Counts Breakdown
    def get_class_counts(items):
        counts = {"NORMAL_WATER": 0, "ALGAL_BLOOM": 0, "TURBID_DISCOLORATION": 0}
        for it in items:
            cls = it["class_label"]
            counts[cls] = counts.get(cls, 0) + 1
        return counts

    train_counts = get_class_counts(train_items)
    val_counts = get_class_counts(val_items)
    test_counts = get_class_counts(test_items)

    # 4. Fresh PyTorch Model Inference Audit on Untouched Test Set
    device = torch.device("cpu")
    model = models.mobilenet_v3_small(weights=None)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, 3)

    pt_path = "models/cv/aquatic_bloom_mobilenetv3.pt"
    if not os.path.exists(pt_path):
        raise FileNotFoundError(f"Model weight file not found at {pt_path}")

    model.load_state_dict(torch.load(pt_path, map_location=device))
    model.eval()

    val_test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    class_names = ["NORMAL_WATER", "ALGAL_BLOOM", "TURBID_DISCOLORATION"]
    test_predictions = []
    confidences_per_class = {cls: [] for cls in class_names}
    all_confidences = []
    conf_matrix = np.zeros((3, 3), dtype=int)

    correct_predictions = 0

    with torch.no_grad():
        for item in test_items:
            img_path = item["filepath"]
            true_cls = item["class_label"]
            true_idx = class_names.index(true_cls)

            with Image.open(img_path) as img:
                img_rgb = img.convert("RGB")
                inp_tensor = val_test_transform(img_rgb).unsqueeze(0)

            logits = model(inp_tensor)
            probs = torch.softmax(logits, dim=1).numpy()[0]
            pred_idx = int(np.argmax(probs))
            pred_cls = class_names[pred_idx]
            conf = float(probs[pred_idx])

            is_correct = (pred_cls == true_cls)
            if is_correct:
                correct_predictions += 1

            conf_matrix[true_idx, pred_idx] += 1
            confidences_per_class[pred_cls].append(conf)
            all_confidences.append(conf)

            test_predictions.append({
                "image_id": item["image_id"],
                "observation_id": item["observation_id"],
                "true_class": true_cls,
                "predicted_class": pred_cls,
                "confidence": round(conf, 4),
                "correct": is_correct,
                "probabilities": {class_names[i]: round(float(probs[i]), 4) for i in range(3)}
            })

    test_accuracy = round(correct_predictions / len(test_items), 4)

    # Confidence Statistics
    conf_stats = {
        "overall": {
            "mean": round(float(np.mean(all_confidences)), 4),
            "median": round(float(np.median(all_confidences)), 4),
            "min": round(float(np.min(all_confidences)), 4),
            "max": round(float(np.max(all_confidences)), 4)
        },
        "per_class": {
            cls: {
                "mean": round(float(np.mean(confidences_per_class[cls])), 4) if len(confidences_per_class[cls]) > 0 else 0.0,
                "min": round(float(np.min(confidences_per_class[cls])), 4) if len(confidences_per_class[cls]) > 0 else 0.0,
                "count": len(confidences_per_class[cls])
            } for cls in class_names
        }
    }

    # 5. Hardware Latency Audit (100 Benchmark Runs)
    latencies_preproc = []
    latencies_infer = []
    latencies_total = []

    # Benchmark test image
    bench_item = test_items[0]
    with Image.open(bench_item["filepath"]) as img:
        bench_img = img.convert("RGB")

    for _ in range(100):
        t0 = time.perf_counter()
        inp_t = val_test_transform(bench_img).unsqueeze(0)
        t1 = time.perf_counter()
        with torch.no_grad():
            _ = model(inp_t)
        t2 = time.perf_counter()

        pre_ms = (t1 - t0) * 1000.0
        inf_ms = (t2 - t1) * 1000.0
        latencies_preproc.append(pre_ms)
        latencies_infer.append(inf_ms)
        latencies_total.append(pre_ms + inf_ms)

    latency_report = {
        "preprocessing_ms": {
            "mean": round(float(np.mean(latencies_preproc)), 3),
            "median": round(float(np.median(latencies_preproc)), 3),
            "p95": round(float(np.percentile(latencies_preproc, 95)), 3)
        },
        "inference_ms": {
            "mean": round(float(np.mean(latencies_infer)), 3),
            "median": round(float(np.median(latencies_infer)), 3),
            "p95": round(float(np.percentile(latencies_infer, 95)), 3)
        },
        "total_pipeline_ms": {
            "mean": round(float(np.mean(latencies_total)), 3),
            "median": round(float(np.median(latencies_total)), 3),
            "p95": round(float(np.percentile(latencies_total, 95)), 3)
        }
    }

    forensic_summary = {
        "group_leakage": {
            "overlap_train_val_count": len(overlap_train_val),
            "overlap_train_test_count": len(overlap_train_test),
            "overlap_val_test_count": len(overlap_val_test),
            "has_group_leakage": group_leakage > 0
        },
        "duplicate_hash_leakage": {
            "duplicate_count_across_splits": duplicate_leakage_count,
            "has_hash_leakage": duplicate_leakage_count > 0
        },
        "split_counts": {
            "train": train_counts,
            "val": val_counts,
            "test": test_counts
        },
        "test_performance": {
            "test_accuracy": test_accuracy,
            "confusion_matrix": conf_matrix.tolist()
        },
        "confidence_statistics": conf_stats,
        "latency_statistics": latency_report,
        "external_generalization": "External generalization dataset unavailable",
        "test_predictions_sample": test_predictions[:10]
    }

    out_file = "models/cv/forensic_audit_summary.json"
    with open(out_file, "w") as f:
        json.dump(forensic_summary, f, indent=2)

    print("=== V4.3 FORENSIC AUDIT COMPLETED ===")
    print(f"Group Leakage Check: {'LEAKAGE FOUND' if group_leakage > 0 else 'ZERO LEAKAGE (PASS)'}")
    print(f"Duplicate Hash Leakage Check: {'LEAKAGE FOUND' if duplicate_leakage_count > 0 else 'ZERO LEAKAGE (PASS)'}")
    print(f"Fresh Test Set Accuracy: {test_accuracy * 100:.2f}%")
    print(f"Confidence Stats: Mean={conf_stats['overall']['mean']}, Median={conf_stats['overall']['median']}")
    print(f"Inference Latency: Mean={latency_report['inference_ms']['mean']}ms, P95={latency_report['inference_ms']['p95']}ms")
    print(f"Audit summary saved to {out_file}")

    return forensic_summary

if __name__ == "__main__":
    run_forensic_audit()
