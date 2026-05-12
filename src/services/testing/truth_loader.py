import os
import json

class TruthLoader:
    @staticmethod
    def load(pdf_path: str) -> dict:
        truth_path = pdf_path.replace(".pdf", ".truth.json")
        if os.path.exists(truth_path):
            with open(truth_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
