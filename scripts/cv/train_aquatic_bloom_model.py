import os
import time
import json
import numpy as np
from PIL import Image

# Handle OpenMP library initialization on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
import onnxruntime as ort
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, accuracy_score

class AquaticImageDataset(Dataset):
    """Dataset loader for Aquatic Bloom CV images."""
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


def train_and_evaluate_model():
    print("=== STARTING AQUATIC CV MODEL TRAINING & FINE-TUNING ===")
    split_path = "data/cv_processed/split_metadata.json"
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split metadata not found at {split_path}")

    with open(split_path, "r") as f:
        split_data = json.load(f)

    train_items = split_data["train"]
    val_items = split_data["val"]
    test_items = split_data["test"]

    # Preprocessing & Data Augmentations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = AquaticImageDataset(train_items, transform=train_transform)
    val_dataset = AquaticImageDataset(val_items, transform=val_test_transform)
    test_dataset = AquaticImageDataset(test_items, transform=val_test_transform)

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    # Initialize MobileNetV3-Small classifier
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, 3)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    os.makedirs("models/cv", exist_ok=True)
    best_val_acc = 0.0
    best_model_path = "models/cv/aquatic_bloom_mobilenetv3.pt"

    # Training Loop
    epochs = 15
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels, _ in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc = correct / total

        # Validation Loop
        model.eval()
        val_running_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels, _ in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_running_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_loss = val_running_loss / val_total
        val_acc = val_correct / val_total

        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_model_path)

    print(f"\nBest Validation Accuracy: {best_val_acc:.4f}. Best model saved to {best_model_path}")

    # Step 3: Evaluation on Untouched Test Set
    model.load_state_dict(torch.load(best_model_path))
    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels, _ in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(probs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    class_names = ["NORMAL_WATER", "ALGAL_BLOOM", "TURBID_DISCOLORATION"]
    report_dict = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    conf_mat = confusion_matrix(all_labels, all_preds).tolist()
    overall_acc = accuracy_score(all_labels, all_preds)

    print("\n=== TEST SET PERFORMANCE EVALUATION ===")
    print(classification_report(all_labels, all_preds, target_names=class_names))
    print("Confusion Matrix:\n", np.array(conf_mat))

    # Step 4: ONNX Model Export
    onnx_path = "models/cv/aquatic_bloom_mobilenetv3.onnx"
    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    model.eval()
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
    )
    print(f"Exported ONNX model to {onnx_path}")

    # Step 5: ONNX Runtime Inference Validation
    ort_session = ort.InferenceSession(onnx_path)
    sample_input = dummy_input.cpu().numpy()
    ort_inputs = {ort_session.get_inputs()[0].name: sample_input}
    ort_outs = ort_session.run(None, ort_inputs)

    torch_out = model(dummy_input).detach().cpu().numpy()
    np.testing.assert_allclose(torch_out, ort_outs[0], rtol=1e-03, atol=1e-04)
    print("ONNX model output numerical validation PASSED!")

    # Step 6: Save Complete Model Metadata
    model_size_bytes = os.path.getsize(onnx_path)
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
            "pt_path": best_model_path,
            "onnx_path": onnx_path,
            "onnx_size_bytes": model_size_bytes,
            "onnx_size_mb": round(model_size_bytes / (1024 * 1024), 2)
        }
    }

    metadata_path = "models/cv/aquatic_bloom_model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model metadata to {metadata_path}")
    return metadata

if __name__ == "__main__":
    train_and_evaluate_model()
