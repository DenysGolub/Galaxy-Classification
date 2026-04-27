import h5py
import torch
import numpy as np
class GalaxyDatasetCNN(torch.utils.data.Dataset):
    def __init__(self, path, limit=None):
        with h5py.File(path, "r") as f:
            images = f["images"][:limit] if limit else f["images"][:]
            labels = f["ans"][:limit] if limit else f["ans"][:]

        self.images = torch.tensor(images, dtype=torch.float32) / 255.0
        self.labels = torch.tensor(labels, dtype=torch.long)

        self.class_map = {
            0: 0, 
            1: 0,
            2: 1, 
            3: 1, 
            4: 1,
            5: 2, 
            6: 2, 
            7: 2,
            8: 3, 
            9: 3,
        }
        
        # Original labels are 0-9, we map them to 0-3 based on the provided mapping.
        # 0,1 -> 0 (Disturbed / Merging)
        # 2,3,4 -> 1 (Smooth)
        # 5,6,7 -> 2 (Spiral)
        # 8,9 -> 3 (Edge-on)
        

        # Apply mapping
        self.labels = torch.tensor([self.class_map[int(y)] for y in self.labels])

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        x = self.images[idx].permute(2, 0, 1)  # HWC -> CHW
        y = self.labels[idx]
        return x, y


class GalaxyDatasetMultimodal(torch.utils.data.Dataset):
    def __init__(self, path, tabular_cols, limit=None):
        """
        path: path to HDF5 file
        tabular_cols: list of feature names
        limit: optional dataset limit
        """
        self.path = path
        self.tabular_cols = tabular_cols

        # Only read metadata here (no persistent file handle)
        with h5py.File(self.path, "r") as f:
            self.length = min(limit, f["images"].shape[0]) if limit else f["images"].shape[0]

            # detect label key
            if "galaxy_type" in f:
                self.label_key = "galaxy_type"
            elif "ans" in f:
                self.label_key = "ans"
            else:
                raise ValueError("No label column found in HDF5")

            # Validate tabular columns exist
            for col in tabular_cols:
                if col not in f:
                    raise ValueError(f"Column {col} not found in HDF5")

        self.file = None  # lazy init per worker

    def __len__(self):
        return self.length

    def _init_file(self):
        if self.file is None:
            self.file = h5py.File(self.path, "r")

    def __getitem__(self, idx):
        self._init_file()

        # -------------------------
        # IMAGE
        # -------------------------
        img = self.file["images"][idx]  # HWC
        img = torch.from_numpy(img).float() / 255.0
        img = img.permute(2, 0, 1)  # → CHW

        # -------------------------
        # TABULAR
        # -------------------------
        tabular_data = []

        for col in self.tabular_cols:
            val = self.file[col][idx]

            # Convert bytes → skip or encode
            if isinstance(val, (bytes, str)):
                # safest: skip non-numeric
                val = 0.0

            # Convert numpy scalar → float
            if isinstance(val, np.generic):
                val = np.nan_to_num(val, nan=0.0)

            tabular_data.append(float(val))

        tabular_tensor = torch.tensor(tabular_data, dtype=torch.float32)

        # -------------------------
        # LABEL
        # -------------------------
        label = int(self.file[self.label_key][idx])
        label = torch.tensor(label, dtype=torch.long)

        # -------------------------
        # RETURN (IMPORTANT)
        # -------------------------
        return img, tabular_tensor, label
