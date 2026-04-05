from astroquery.sdss import SDSS
from astropy import coordinates as coords
import astropy.units as u
import h5py
import numpy as np
from tensorflow.keras import utils

class DataManager:
    def __init__(self, hdf5_path):
        self.hdf5_path = hdf5_path

    def load_from_hdf5(self):
        """Завантажуємо з HDF5 файл зображення, метадані та мітки"""
        with h5py.File(self.hdf5_path, "r") as f:
            images = f["images"][:].astype(np.float32)
            labels = f["ans"][:]

            ra = f["ra"][:]
            dec = f["dec"][:]
            redshift = f["redshift"][:]
            pxscale = f["pxscale"][:]
            labels = utils.to_categorical(labels, 10).astype(np.float32)
            
            return [
                {
                    "image": images[i],
                    "label": labels[i],
                    "metadata": {
                        "ra": ra[i],
                        "dec": dec[i],
                        "redshift": redshift[i],
                        "pxscale": pxscale[i]
                    }
                }
                for i in range(images.shape[0])
            ]