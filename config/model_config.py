from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT_DIR / "models" / "efficient_net_0.8324.pth"
MODEL_VERSION = MODEL_PATH.name
