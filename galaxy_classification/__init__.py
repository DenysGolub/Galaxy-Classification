# Galaxy Classification Package

from .models.cnn import GalaxyCNN
from .database import GalaxyDatabase

__version__ = "0.1.0"
__all__ = ["GalaxyCNN", "GalaxyDatabase"]