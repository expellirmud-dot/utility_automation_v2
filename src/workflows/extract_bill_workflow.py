from src.services.extraction.field_extractor_service import FieldExtractorService
from src.models.bill_data import BillData

class ExtractBillWorkflow:
    @staticmethod
    def run(raw_text: str) -> BillData:
        # Orchestrate field extraction
        return FieldExtractorService.extract(raw_text)
