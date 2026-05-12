import json
import os
from src.models.pipeline_metrics import FailureSnapshot

class FailureSnapshotService:
    @staticmethod
    def export(snapshot: FailureSnapshot, output_dir="output/failures"):
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{os.path.basename(snapshot.source_file)}_{snapshot.pipeline_stage}_fail.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.__dict__, f, indent=4, ensure_ascii=False)
