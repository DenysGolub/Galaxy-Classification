import h5py
import torch
class GalaxyDataset(torch.utils.data.Dataset):
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
