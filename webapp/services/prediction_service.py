import io
import base64
import torch
import uuid
from PIL import Image
import torchvision.transforms as transforms

from galaxy_classification.models.neural_network import GalaxyCNN
from config.model_config import MODEL_PATH, MODEL_VERSION

class PredictionService:
    def __init__(self):
        self.model_path = MODEL_PATH
        self.model_version = MODEL_VERSION
        self.model = GalaxyCNN()
        try:
            self.model.load_state_dict(torch.load(self.model_path, map_location='cpu'))
            self.model.eval()
            print(f"AI CORE: Neural weights loaded successfully ({self.model_version}).")
        except Exception as e:
            print(f"FATAL: Could not load model: {e}")
            self.model = None

        self.CLASSES = ["Disturbed / Merging", "Smooth", "Spiral", "Edge-on"]

        # Matches the size your model expects
        self.preprocess = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
        ])

    def predict_galaxy(self, image_data):
        """Predict galaxy morphology from base64 image data"""
        if self.model is None:
            raise Exception("Model not loaded")

        try:
            # Decode base64 image
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # Preprocess image
            input_tensor = self.preprocess(img).unsqueeze(0)

            print(f"Input tensor shape: {input_tensor.shape}")

            # Make prediction
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                print(f"Model probabilities: {probabilities}")
                confidence, index = torch.max(probabilities, 0)

            predicted_class = self.CLASSES[index.item()]
            
            # Create probabilities dictionary for all classes
            class_probabilities = {}
            for i, class_name in enumerate(self.CLASSES):
                class_probabilities[class_name] = round(probabilities[i].item() * 100, 2)

            return {
                "prediction": predicted_class,
                "confidence": round(confidence.item() * 100, 2),
                "class_probabilities": class_probabilities,
                "status": "success"
            }

        except Exception as e:
            print(f"PREDICTION ERROR: {str(e)}")
            raise Exception(f"Prediction failed: {str(e)}")

    def generate_observation_id(self):
        """Generate a unique observation ID"""
        return f"GCSO-{uuid.uuid4().hex[:8].upper()}"
