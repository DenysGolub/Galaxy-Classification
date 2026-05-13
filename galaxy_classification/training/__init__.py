"""
Training module - Training and evaluation utilities.

Dependencies: models, data modules
"""

from .trainer import GalaxyTrainer
from . import train
from . import evaluation

__all__ = ["GalaxyTrainer", "train", "evaluation"]