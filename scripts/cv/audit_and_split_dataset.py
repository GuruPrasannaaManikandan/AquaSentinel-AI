import os
import json
import random
from PIL import Image
from typing import Dict, Any, List

def audit_and_split_dataset(raw_manifest_path: str = "data/cv_raw/dataset_manifest.json", output_dir: str = "data/cv_processed"):
    """
    Performs comprehensive dataset quality audit (corruption check, class balance, resolutions)
    and executes anti-leakage grouped splitting by observation_id (70% Train / 15% Val / 15% Test).
    """
    if not os.path.exists(raw_manifest_path):
        raise FileNotFoundError(f"Raw manifest not found at {raw_manifest_path}")

    with open(raw_manifest_path, "r") as f:
        items = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Quality Audit & Corruption Check
    audited_items = []
    corrupted_count = 0
    class_counts = {}
    resolution_counts = {}

    for item in items:
        filepath = item["filepath"]
        cls = item["class_label"]
        try:
            with Image.open(filepath) as img:
                img.verify()  # Verify JPEG integrity
            audited_items.append(item)
            class_counts[cls] = class_counts.get(cls, 0) + 1
            res_str = f"{item['width']}x{item['height']}"
            resolution_counts[res_str] = resolution_counts.get(res_str, 0) + 1
        except Exception as e:
            print(f"Corrupted image detected and removed: {filepath} ({e})")
            corrupted_count += 1

    # Step 2: Grouped Anti-Leakage Split by observation_id
    obs_to_items = {}
    for item in audited_items:
        obs_id = item["observation_id"]
        if obs_id not in obs_to_items:
            obs_to_items[obs_id] = []
        obs_to_items[obs_id].append(item)

    unique_obs = list(obs_to_items.keys())
    random.seed(42)
    random.shuffle(unique_obs)

    num_obs = len(unique_obs)
    train_end = int(num_obs * 0.70)
    val_end = train_end + int(num_obs * 0.15)

    train_obs = set(unique_obs[:train_end])
    val_obs = set(unique_obs[train_end:val_end])
    test_obs = set(unique_obs[val_end:])

    train_items, val_items, test_items = [], [], []

    for item in audited_items:
        obs_id = item["observation_id"]
        if obs_id in train_obs:
            train_items.append(item)
        elif obs_id in val_obs:
            val_items.append(item)
        else:
            test_items.append(item)

    split_manifest = {
        "audit_summary": {
            "total_images_processed": len(items),
            "valid_images": len(audited_items),
            "corrupted_images": corrupted_count,
            "class_distribution": class_counts,
            "resolution_distribution": resolution_counts,
            "total_observations": num_obs
        },
        "split_counts": {
            "train_images": len(train_items),
            "val_images": len(val_items),
            "test_images": len(test_items),
            "train_observations": len(train_obs),
            "val_observations": len(val_obs),
            "test_observations": len(test_obs)
        },
        "train": train_items,
        "val": val_items,
        "test": test_items
    }

    out_file = os.path.join(output_dir, "split_metadata.json")
    with open(out_file, "w") as f:
        json.dump(split_manifest, f, indent=2)

    print("=== DATASET AUDIT & GROUPED SPLIT SUMMARY ===")
    print(f"Total Valid Images: {len(audited_items)} across {num_obs} unique observation events")
    print(f"Class Distribution: {class_counts}")
    print(f"Train Split: {len(train_items)} images ({len(train_obs)} observations)")
    print(f"Val Split:   {len(val_items)} images ({len(val_obs)} observations)")
    print(f"Test Split:  {len(test_items)} images ({len(test_obs)} observations)")
    print(f"Split metadata saved to {out_file}")

    return out_file

if __name__ == "__main__":
    audit_and_split_dataset()
