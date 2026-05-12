import json
import os
from src.models.processing_result import ProcessingResult

class JSONSerializer:
    @staticmethod
    def serialize(result: ProcessingResult, output_dir: str):
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Serialize result object
        file_path = os.path.join(output_dir, "processing_result.json")
        with open(file_path, "w", encoding="utf-8") as f:
            # Simple conversion to dict
            data = {
                "bill_data": result.bill_data.__dict__,
                "ai_review": result.ai_review_result.__dict__ if result.ai_review_result else None,
                "status": result.processing_status,
                "timestamp": result.timestamp
            }
            json.dump(data, f, indent=4, ensure_ascii=False)
