# ============================================================
# Farm Wise AI - Plant Disease PyTorch Training Pipeline
# Handles nested crop directories (e.g. archive/crops/Tomato/Tomato_Late_blight)
# Uses PyTorch CUDA Mixed Precision & MobileNetV3 Transfer Learning
# ============================================================

import os
import sys
import json
import argparse
import time
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models

BASE_DIR = Path(__file__).resolve().parent
MODEL_SAVE_PATH = BASE_DIR / "plant_disease_model.pth"
CLASSES_SAVE_PATH = BASE_DIR / "disease_classes.json"

class NestedPlantDiseaseDataset(Dataset):
    """Custom Dataset that recursively scans subdirectories to collect image files and their disease folder class names."""
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        self.classes = []

        class_set = set()
        temp_samples = []

        # Find folders containing images
        for root, _, files in os.walk(self.root_dir):
            img_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
            if img_files:
                class_name = os.path.basename(root)
                class_set.add(class_name)
                for f in img_files:
                    temp_samples.append((os.path.join(root, f), class_name))

        self.classes = sorted(list(class_set))
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
        self.samples = [(filepath, self.class_to_idx[cls_name]) for filepath, cls_name in temp_samples]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        filepath, target = self.samples[idx]
        try:
            image = Image.open(filepath).convert("RGB")
        except Exception:
            # Fallback for corrupted images
            image = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform:
            image = self.transform(image)
        return image, target

def get_data_transforms():
    """Returns PyTorch image transforms for training and validation."""
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return train_transform, val_transform

def train_model(data_dir, epochs=5, batch_size=64, lr=0.001):
    data_dir = Path(data_dir)
    if not data_dir.exists():
        print(f"Error: Dataset directory '{data_dir}' does not exist.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 65)
    print(f"  FARM WISE AI - HIGH PERFORMANCE PLANT DISEASE TRAINING")
    print(f"  Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"  Dataset path: {data_dir}")
    print("=" * 65)

    train_tf, val_tf = get_data_transforms()

    # Load dataset using custom recursive scanner
    full_dataset = NestedPlantDiseaseDataset(root_dir=data_dir, transform=train_tf)
    num_classes = len(full_dataset.classes)
    class_names = full_dataset.classes

    if num_classes <= 1:
        print(f"Error: Found only {num_classes} classes. Please check the dataset folder path.")
        return

    print(f"Successfully discovered {len(full_dataset)} images across {num_classes} distinct disease classes!")

    # Save class mapping to JSON
    class_map = {idx: cls_name for idx, cls_name in enumerate(class_names)}
    with open(CLASSES_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(class_map, f, indent=2)
    print(f"Saved class index mapping ({num_classes} classes) to {CLASSES_SAVE_PATH}")

    # Split train/val (80% train, 20% val)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    num_workers = min(4, os.cpu_count() or 2)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    # Initialize MobileNetV3-Small (Pre-trained on ImageNet)
    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)

    # Replace classifier head for dataset classes
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    # Mixed precision scaler for fast GPU acceleration
    use_amp = device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    best_acc = 0.0
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        print(f"\nEpoch {epoch}/{epochs}")
        print("-" * 35)

        # Train phase
        model.train()
        running_loss, running_corrects = 0.0, 0
        total_batches = len(train_loader)

        for step, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
            optimizer.zero_grad()

            with torch.cuda.amp.autocast(enabled=use_amp):
                outputs = model(inputs)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            _, preds = torch.max(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

            if (step + 1) % 200 == 0 or (step + 1) == total_batches:
                curr_acc = (running_corrects.double() / ((step + 1) * batch_size)) * 100
                print(f"  Batch {step+1}/{total_batches} - Train Loss: {loss.item():.4f} - Running Acc: {curr_acc:.2f}%")

        epoch_loss = running_loss / train_size
        epoch_acc = running_corrects.double() / train_size
        print(f"-> Epoch {epoch} Train Summary: Loss={epoch_loss:.4f}, Accuracy={epoch_acc * 100:.2f}%")

        # Val phase
        model.eval()
        val_loss, val_corrects = 0.0, 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
                with torch.cuda.amp.autocast(enabled=use_amp):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                _, preds = torch.max(outputs, 1)
                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data)

        val_loss = val_loss / val_size
        val_acc = val_corrects.double() / val_size
        print(f"-> Epoch {epoch} Val Summary:   Loss={val_loss:.4f}, Accuracy={val_acc * 100:.2f}%")

        # Save best model checkpoint
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"  [Checkpoint Saved] New best validation accuracy: {best_acc * 100:.2f}%")

    total_time = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"  TRAINING COMPLETE in {total_time // 60:.0f}m {total_time % 60:.0f}s")
    print(f"  Total Classes Trained: {num_classes}")
    print(f"  Best Validation Accuracy: {best_acc * 100:.2f}%")
    print(f"  Model saved to: {MODEL_SAVE_PATH}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Plant Disease Classifier")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to unzipped plant disease dataset folder")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs to train (default: 5)")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size (default: 64)")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate (default: 0.001)")
    args = parser.parse_args()

    train_model(args.data_dir, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
