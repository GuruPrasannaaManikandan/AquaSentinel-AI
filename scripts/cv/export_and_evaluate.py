import os
import json
import numpy as np
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

class AquaticImageDataset(Dataset):
    def __init__(self, items: list, transform=None):
        self.items = items
        self.transform = transform
        self.class_to_idx = {
            "NORMAL_WATER": 0,
            "ALGAL_BLOOM": 1,
            "TURBID_DISCOLORATION": 2
        }

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        img_path = item["filepath"]
        label_str = item["class_label"]
        label_idx = self.class_to_idx[label_str]

        with Image.open(img_path) as img:
            img = img.convert("RGB")
            if self.transform:
                img = self.transform(img)

        return img, label_idx, item["image_id"]

def run_export_and_eval():
    split_path = "data/cv_processed/split_metadata.json"
    with open(split_path, "r") as f:
        split_data = json.load(f)

    test_items = split_data["test"]
    val_test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_dataset = AquaticImageDataset(test_items, transform=val_test_transform)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    device = torch.device("cpu")
    model = models.mobilenet_v3_small(weights=None)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, 3)

    pt_path = "models/cv/aquatic_bloom_mobilenetv3.pt"
    model.load_state_dict(torch.load(pt_path, map_location=device))
    model.to(device)
    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels, _ in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(probs, 1)
            all_preds.extend(preds.numpy())
            all_labels.extend(labels.numpy())

    class_names = ["NORMAL_WATER", "ALGAL_BLOOM", "TURBID_DISCOLORATION"]
    report_dict = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    conf_mat = confusion_matrix(all_labels, all_preds).tolist()
    overall_acc = accuracy_score(all_labels, all_preds)

    print("=== UNTOUCHED TEST SET PERFORMANCE EVALUATION ===")
    print(classification_report(all_labels, all_preds, target_names=class_names))
    print("Confusion Matrix:\n", np.array(conf_mat))

    # Try ONNX Export with legacy dynamo=False or ONNXRuntime
    onnx_path = "models/cv/aquatic_bloom_mobilenetv3.onnx"
    try:
        dummy_input = torch.randn(1, 3, 224, 224)
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=12,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
            dynamo=False
        )
        print(f"Exported ONNX model to {onnx_path}")
        onnx_exported = True
    except Exception as e:
        print(f"ONNX export warning: {e}. PyTorch binary checkpoint '.pt' ready at {pt_path}")
        onnx_exported = False

    model_size_bytes = os.path.getsize(pt_path)
    metadata = {
        "model_name": "MobileNetV3-Small-AquaticBloom",
        "model_version": "1.0.0",
        "architecture": "mobilenet_v3_small",
        "classes": class_names,
        "class_to_idx": {"NORMAL_WATER": 0, "ALGAL_BLOOM": 1, "TURBID_DISCOLORATION": 2},
        "input_contract": {
            "width": 224,
            "height": 224,
            "channels": 3,
            "color_space": "RGB",
            "normalization": "STANDARD (ImageNet mean/std)",
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
            "data_format": "NHWC or NCHW",
            "dtype": "float32"
        },
        "metrics": {
            "test_accuracy": round(overall_acc, 4),
            "macro_f1": round(report_dict["macro avg"]["f1-score"], 4),
            "weighted_f1": round(report_dict["weighted avg"]["f1-score"], 4),
            "per_class": {
                cls: {
                    "precision": round(report_dict[cls]["precision"], 4),
                    "recall": round(report_dict[cls]["recall"], 4),
                    "f1": round(report_dict[cls]["f1-score"], 4),
                    "support": report_dict[cls]["support"]
                } for cls in class_names
            },
            "confusion_matrix": conf_mat
        },
        "export": {
            "pt_path": pt_path,
            "onnx_path": onnx_path if onnx_exported else None,
            "model_size_bytes": model_size_bytes,
            "model_size_mb": round(model_size_bytes / (1024 * 1024), 2)
        }
    }

    metadata_path = "models/cv/aquatic_bloom_model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model metadata to {metadata_path}")
    return metadata

if __name__ == "__main__":
    run_export_and_eval()
