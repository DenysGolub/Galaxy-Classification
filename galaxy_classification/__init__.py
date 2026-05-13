# Galaxy Classification Package
"""
Galaxy Classification Package - Multi-modal galaxy classification system.

Module structure:
- core: Foundational components (database)
- data: Data loading and dataset preparation
- models: Neural network architectures
- training: Training and evaluation utilities
"""

from .models.neural_network import GalaxyCNN
from .core.database import GalaxyDatabase

__version__ = "0.1.0"
__all__ = ["GalaxyCNN", "GalaxyDatabase"]