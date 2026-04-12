from PIL import Image
import requests
import torch
import numpy as np
from io import BytesIO


class GalaxyDataLoader:

    def __init__(self, class_names):
        self.class_names = class_names
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # -------------------------
    # LEGACY SURVEY IMAGE LOADER
    # -------------------------
    def get_legacy_image(self, ra, dec, size=256, layer="ls-dr10", pixscale=0.262):
        """
        Downloads RGB cutout from Legacy Survey
        """
        url = (
        f"https://www.legacysurvey.org/viewer/cutout.jpg"
        f"?ra={ra}&dec={dec}&size={size}&layer={layer}"
        f"&pixscale={pixscale}"
    )

        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img

    # -------------------------
    # PREPROCESS (UNIFIED)
    # -------------------------
    def preprocess(self, img, size=256):
        """
        PIL -> Tensor [C, H, W]
        """

        img = img.resize((size, size))
        img = np.array(img).astype(np.float32) / 255.0

        # (optional but good for astro images)
        img = np.clip(img, 0, 1)

        # HWC -> CHW
        img = torch.from_numpy(img).permute(2, 0, 1)

        return img

    # -------------------------
    # CLASSIFY LEGACY SURVEY
    # -------------------------
    def classify_legacy(self, model, ra, dec, size=256, pixscale=0.262):

        img = self.get_legacy_image(ra, dec, size=size, pixscale=pixscale)

        x = self.preprocess(img, size=size)
        x = x.unsqueeze(0).to(self.device)

        model.eval()
        model = model.to(self.device)

        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)

            pred = probs.argmax(1).item()
            conf = probs.max().item()

        print("Predicted:", self.class_names[pred])
        print("Confidence:", round(conf, 4))

        return img, pred, conf

    # -------------------------
    # LOCAL IMAGE CLASSIFICATION
    # -------------------------
    def classify_local(self, model, path, size=256):

        img = Image.open(path).convert("RGB")
        x = self.preprocess(img, size=size)

        x = x.unsqueeze(0).to(self.device)

        model.eval()
        model = model.to(self.device)

        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)

            pred = probs.argmax(1).item()
            conf = probs.max().item()

        print("Predicted:", self.class_names[pred])
        print("Confidence:", round(conf, 4))

        return img, pred, conf

