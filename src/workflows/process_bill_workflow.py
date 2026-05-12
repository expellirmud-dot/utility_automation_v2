from src.workflows.process_pdf_workflow import ProcessPDFWorkflow
from src.workflows.extract_bill_workflow import ExtractBillWorkflow
from src.models.bill_data import BillData

class ProcessBillWorkflow:
    @staticmethod
    def run(pdf_path: str) -> BillData:
        # Step 1: OCR Pipeline
        ocr_result = ProcessPDFWorkflow.run(pdf_path)
        
        # Step 2: Extraction Workflow
        bill_data = ExtractBillWorkflow.run(ocr_result.extracted_text)
        
        return bill_data
