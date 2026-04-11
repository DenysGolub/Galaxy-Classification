from PIL import Image
import requests
import torch
from io import BytesIO
import numpy as np
class GalaxyDataLoader:
    
    def __init__(self, class_names):
        self.class_names = class_names
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def load_image_from_disk(self, path, size=256):
        img = Image.open(path).convert("RGB")

        # resize
        img = img.resize((size, size))

        # PIL -> numpy
        img = np.array(img).astype(np.float32) / 255.0

        # HWC -> CHW
        img = torch.from_numpy(img).permute(2, 0, 1)

        return img
    
    def classify_sdss(self, model, ra, dec):
        img = self.get_sdss_image(ra, dec, size=256)

        # PIL -> Tensor
        x = self.preprocess_pil(img)

        # add batch dim
        x = x.unsqueeze(0).to(self.device)

        model.eval()
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)

            pred = probs.argmax(1).item()
            conf = probs.max().item()

        print("Predicted:", self.class_names[pred])
        print("Confidence:", round(conf, 4))

        return img, pred, conf

    def preprocess_pil(self, img, size=256):
        # resize
        img = img.resize((size, size))

        # PIL -> numpy
        img = np.array(img).astype(np.float32) / 255.0  # normalize 0–1

        # HWC -> CHW
        img = torch.from_numpy(img).permute(2, 0, 1)

        return img


    def get_sdss_image(self, ra, dec, size=256):
        """
        ra, dec — координати
        size — пікселі (256x256)
        """

        url = f"https://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg?ra={ra}&dec={dec}&width={size}&height={size}&scale=0.1"

        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGB")

        return img
            
        