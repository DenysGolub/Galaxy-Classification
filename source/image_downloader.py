import os
import time
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
from astropy.stats import sigma_clipped_stats
from astropy.visualization import make_lupton_rgb
from skimage.io import imsave
import cv2

# =========================
# CONFIG
# =========================
CSV_PATH = "data/metadata/gz2sample.csv"
OUTPUT_DIR = "data/images_legacy_lupton"
MAX_IMAGES = 500
SLEEP_TIME = 0.2
IMAGE_SIZE = 512
PIXSCALE = 0.262
LAYER = "ls-dr10"
BANDS = ["g","r","i"]  # будемо робити RGB з g,r,i

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["RA","DEC"])
df = df.head(MAX_IMAGES)

# =========================
# FUNCTIONS
# =========================
def download_band(ra, dec, band, size=IMAGE_SIZE):
    """Завантажуємо JPEG канал з Legacy Survey"""
    url = (
        f"https://www.legacysurvey.org/viewer/jpeg-cutout"
        f"?ra={ra}&dec={dec}&layer={LAYER}"
        f"&pixscale={PIXSCALE}&bands={band}&size={size}"
    )
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            img_array = np.frombuffer(r.content, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            return img.astype(np.float32)
        else:
            return None
    except:
        return None

def preprocess_channel(img):
    """Sigma-clipping + нормалізація 0-1"""
    if img is None:
        return None
    mean, median, std = sigma_clipped_stats(img, sigma=3.0)
    img = np.clip(img, median - 3*std, median + 3*std)
    img = (img - img.min()) / max(img.max() - img.min(), 1e-8)
    return img

# =========================
# MAIN LOOP
# =========================
success = 0
failed = 0

for i, row in tqdm(df.iterrows(), total=len(df)):
    ra = row["RA"]
    dec = row["DEC"]

    # Завантажуємо канали
    g = preprocess_channel(download_band(ra, dec, "g"))
    r = preprocess_channel(download_band(ra, dec, "r"))
    i_band = preprocess_channel(download_band(ra, dec, "i"))

    if g is None or r is None or i_band is None:
        failed += 1
        continue

    # Lupton RGB: i->R, r->G, g->B
    rgb = make_lupton_rgb(i_band, r, g, stretch=0.5, Q=10)
    
    # Зберігаємо JPEG
    filename = os.path.join(OUTPUT_DIR, f"{i:05d}_{ra:.5f}_{dec:.5f}.jpg")
    imsave(filename, (rgb*255).astype(np.uint8))
    success += 1

    time.sleep(SLEEP_TIME)

print(f"\nDownloaded & processed (Lupton RGB): {success}")
print(f"Failed: {failed}")
