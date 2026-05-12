import os
import shutil
import json
from src.services.classification.provider_detector_v1 import ProviderDetectorV1

class ClassificationRouter:
    @staticmethod
    def process_unknowns(unknown_dir="datasets/raw_original/unknown"):
        processed = []
        for file in os.listdir(unknown_dir):
            if not file.endswith(".pdf"): continue
            
            path = os.path.join(unknown_dir, file)
            detection = ProviderDetectorV1.detect(path)
            
            # Logic: confidence >= 0.80 -> assign, 0.5-0.79 -> flag, <0.5 -> unknown
            conf = detection["score"]
            if conf >= 0.80:
                target = os.path.join("datasets/raw_original", detection["provider"].lower(), file)
                shutil.move(path, target)
                processed.append({"file": file, "action": "moved", "to": target, "conf": conf})
            else:
                processed.append({"file": file, "action": "kept_unknown", "conf": conf})
        return processed
