import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from tqdm import tqdm
import matplotlib.pyplot as plt

from galaxy_source.galaxy_cnn import GalaxyCNN


class GalaxyTrainer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def train(self, train_dataset, test_dataset, num_epochs=50, batch_size=64):
        # -------------------------
        # 1. Get labels safely
        # -------------------------
        labels = torch.tensor(
            [train_dataset[i][1] for i in range(len(train_dataset))],
            dtype=torch.long
        )

        # -------------------------
        # 2. Class balancing (Sampler)
        # -------------------------
        num_classes = 4

        class_sample_count = torch.tensor(
            [(labels == i).sum() for i in range(num_classes)],
            dtype=torch.float
        )

        class_sample_count = torch.clamp(class_sample_count, min=1)
        class_weights = 1.0 / class_sample_count
        samples_weight = class_weights[labels]

        sampler = WeightedRandomSampler(
            weights=samples_weight,
            num_samples=len(samples_weight),
            replacement=True
        )

        # -------------------------
        # 3. DataLoaders
        # -------------------------
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,
            num_workers=2,
            pin_memory=True
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True
        )

        # -------------------------
        # 4. Model
        # -------------------------
        model = GalaxyCNN(num_classes=num_classes).to(self.device)

        if torch.cuda.device_count() > 1:
            print("Using", torch.cuda.device_count(), "GPUs")
            model = nn.DataParallel(model)

        # -------------------------
        # 5. Loss (без class weights!)
        # -------------------------
        self.criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=2e-4,
            weight_decay=1e-4
        )

        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=num_epochs
        )

        scaler = torch.cuda.amp.GradScaler(enabled=(self.device.type == "cuda"))

        # -------------------------
        # 6. Metrics
        # -------------------------
        best_val_acc = 0
        self.train_losses, self.train_accuracies = [], []
        self.val_losses, self.val_accuracies = [], []

        # -------------------------
        # 7. Training loop
        # -------------------------
        for epoch in range(num_epochs):
            model.train()
            train_loss, correct, total = 0, 0, 0

            for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
                images = images.to(self.device)
                labels = labels.to(self.device)

                self.optimizer.zero_grad()

                with torch.cuda.amp.autocast(enabled=(self.device.type == "cuda")):
                    outputs = model(images)
                    loss = self.criterion(outputs, labels)

                scaler.scale(loss).backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(self.optimizer)
                scaler.update()

                train_loss += loss.item() * images.size(0)
                predicted = outputs.argmax(dim=1)
                correct += predicted.eq(labels).sum().item()
                total += labels.size(0)

            train_loss /= total
            train_acc = correct / total

            # -------------------------
            # Validation
            # -------------------------
            model.eval()
            val_loss, val_correct, val_total = 0, 0, 0

            with torch.no_grad():
                for images, labels in test_loader:
                    images = images.to(self.device)
                    labels = labels.to(self.device)

                    with torch.cuda.amp.autocast(enabled=(self.device.type == "cuda")):
                        outputs = model(images)
                        loss = self.criterion(outputs, labels)

                    val_loss += loss.item() * images.size(0)
                    predicted = outputs.argmax(dim=1)
                    val_correct += predicted.eq(labels).sum().item()
                    val_total += labels.size(0)

            val_loss /= val_total
            val_acc = val_correct / val_total

            self.scheduler.step()

            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(model.state_dict(), f"../models/best_{best_val_acc:.4f}.pth")

            # Save metrics
            self.train_losses.append(train_loss)
            self.train_accuracies.append(train_acc)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)

            print(
                f"Epoch {epoch+1}/{num_epochs} | "
                f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f} | "
                f"Best: {best_val_acc:.4f}"
            )

        return model

    # -------------------------
    # Evaluation
    # -------------------------
    def evaluate(self, model, test_loader):
        model.eval()
        val_loss, val_correct, val_total = 0, 0, 0

        with torch.no_grad():
            for images, labels in test_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                with torch.cuda.amp.autocast(enabled=(self.device.type == "cuda")):
                    outputs = model(images)
                    loss = self.criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                predicted = outputs.argmax(dim=1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)

        val_loss /= val_total
        val_acc = val_correct / val_total
        return val_loss, val_acc

    # -------------------------
    # Plot
    # -------------------------
    def plot_metrics(self):
        epochs = range(1, len(self.train_losses) + 1)

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.plot(epochs, self.train_losses, label="Train Loss")
        plt.plot(epochs, self.val_losses, label="Val Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        plt.title("Loss")

        plt.subplot(1, 2, 2)
        plt.plot(epochs, self.train_accuracies, label="Train Acc")
        plt.plot(epochs, self.val_accuracies, label="Val Acc")
        plt.xlabel("Epoch")
        plt.ylabel("Accuracy")
        plt.legend()
        plt.title("Accuracy")

        plt.tight_layout()
        plt.show()

    # -------------------------
    # Predict
    # -------------------------
    def predict(self, model, image):
        model.eval()
        with torch.no_grad():
            image = image.unsqueeze(0).to(self.device)
            output = model(image)
            predicted_class = output.argmax(dim=1).item()
        return predicted_class
