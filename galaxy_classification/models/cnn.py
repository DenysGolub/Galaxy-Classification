import torch
import torch.nn as nn


class GalaxyCNN(nn.Module):
    def __init__(self, num_classes=4):
        super(GalaxyCNN, self).__init__()

        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 256 → 128

            # Block 2
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 128 → 64

            # Block 3
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 64 → 32

            # Block 4
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 32 → 16

            # Block 5
            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))  # Global pooling
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),   # тільки тут
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

    def load_model(self, path, device="cpu"):
        self.load_state_dict(torch.load(path, map_location=device))
        self.eval()

    def predict(self, image, device="cpu"):
        self.eval()
        
        image = image.unsqueeze(0).to(device)

        with torch.no_grad():
            output = self(image)   
            predicted_class = output.argmax(dim=1).item()

        return predicted_class

class GalaxyMultimodalNet(nn.Module):
    def __init__(self, num_classes=4, num_tabular_features=15):
        super(GalaxyMultimodalNet, self).__init__()

        # --- BRANCH 1: CNN (Your original architecture for images) ---
        self.cnn_branch = nn.Sequential(
            # Block 1: 256 -> 128
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # Block 2: 128 -> 64
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # Block 3: 64 -> 32
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # Block 4: 32 -> 16
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # Block 5: Global Feature Extraction
            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten()  # Output: 512 features
        )

        # --- BRANCH 2: Tabular MLP (For redshift, velDisp, magnitudes) ---
        # We project metadata into 64 dimensions to balance it with CNN features
        self.tabular_branch = nn.Sequential(
            nn.Linear(num_tabular_features, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU()
        )

        # --- FUSION: Combined Classifier ---
        # Input size = 512 (CNN) + 64 (Tabular) = 576
        self.classifier = nn.Sequential(
            nn.Linear(512 + 64, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )

    def forward(self, image, tabular):
        # image shape: [Batch, 3, H, W]
        # tabular shape: [Batch, num_tabular_features]
        
        img_features = self.cnn_branch(image)       # [Batch, 512]
        tab_features = self.tabular_branch(tabular) # [Batch, 64]
        
        # Late Fusion: Concatenate the feature vectors
        combined = torch.cat((img_features, tab_features), dim=1) # [Batch, 576]
        
        output = self.classifier(combined)
        return output

    def load_model(self, path, device="cpu"):
        self.load_state_dict(torch.load(path, map_location=device))
        self.to(device)
        self.eval()

    def predict(self, image, tabular, device="cpu"):
        """
        Predicts the class of a single galaxy.
        image: torch.Tensor [3, H, W]
        tabular: torch.Tensor [num_tabular_features]
        """
        self.eval()
        
        # Add batch dimension [1, ...] and move to device
        image = image.unsqueeze(0).to(device)
        tabular = tabular.unsqueeze(0).to(device)

        with torch.no_grad():
            output = self.forward(image, tabular)
            # Apply softmax to get probabilities
            probs = torch.softmax(output, dim=1)
            predicted_class = output.argmax(dim=1).item()
            confidence = probs[0][predicted_class].item()

        return predicted_class, confidence