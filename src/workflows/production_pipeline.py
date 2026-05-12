import time
from src.workflows.unified_bill_pipeline import UnifiedBillPipeline
from src.workflows.ai_validation_workflow import AIValidationWorkflow
from src.models.processing_result import ProcessingResult
from src.services.serialization.json_serializer import JSONSerializer
import os

class ProductionPipeline:
    @staticmethod
    def run(pdf_path: str):
        start = time.time()
        
        # Deterministic Pipeline
        bill = UnifiedBillPipeline.run(pdf_path)
        
        # AI Review
        ai_res = None
        if "missing_total" in bill.confidence_flags: # Trigger condition
            ai_res = AIValidationWorkflow.run(bill)
            
        result = ProcessingResult(
            bill_data=bill,
            ai_review_result=ai_res,
            source_file=pdf_path,
            processing_duration_ms=(time.time() - start) * 1000
        )
        
        # Export
        vendor = bill.vendor_name or "Unknown"
        output_dir = os.path.join("output", "processed", vendor)
        JSONSerializer.serialize(result, output_dir)
        
        return result
