from src.workflows.process_pdf_workflow import ProcessPDFWorkflow
from src.workflows.extract_bill_workflow import ExtractBillWorkflow
from src.workflows.provider_refinement_workflow import ProviderRefinementWorkflow
from src.workflows.validation_workflow import ValidationWorkflow
from src.models.bill_data import BillData

class UnifiedBillPipeline:
    @staticmethod
    def run(pdf_path: str) -> BillData:
        # 1. OCR
        ocr_result = ProcessPDFWorkflow.run(pdf_path)
        # 2. Extract
        bill = ExtractBillWorkflow.run(ocr_result.extracted_text)
        # 3. Refine
        bill = ProviderRefinementWorkflow.run(bill)
        # 4. Validate
        bill = ValidationWorkflow.run(bill)
        
        return bill
