from sklearn.model_selection import train_test_split
from data_manager import DataManager
import numpy as np
import os
import matplotlib.pyplot as plt
import keras
import tensorflow as tf
from tensorflow.keras import layers, models

METADATA_INCLUDED = False
images_path = "data\\Galaxy10_DECals.h5"
data_manager = DataManager(images_path)
dataset = data_manager.load_from_hdf5()

images = np.array([item["image"] for item in dataset])
labels = np.array([item["label"] for item in dataset])

train_idx, test_idx = train_test_split(np.arange(labels.shape[0]), test_size=0.1)
train_images, train_labels, test_images, test_labels = images[train_idx], labels[train_idx], images[test_idx], labels[test_idx]

print(f"Train set: {train_images.shape}, {train_labels.shape}")
print(f"Test set: {test_images.shape}, {test_labels.shape}")

model = models.Sequential([
    # Feature Extraction
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    # Classification
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax') # 10 classes for digits 0-9
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Training for 5 iterations (epochs)
model.fit(train_images, train_labels, epochs=5, validation_data=(test_images, test_labels))