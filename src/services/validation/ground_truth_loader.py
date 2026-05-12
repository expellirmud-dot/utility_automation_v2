import json
import os

class GroundTruthLoader:
    def load_truth(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
