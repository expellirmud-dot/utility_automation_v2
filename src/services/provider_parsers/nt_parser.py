from src.services.provider_parsers.base_provider_parser import BaseProviderParser
from src.models.bill_data import BillData
import re

class NTParser(BaseProviderParser):
    def can_handle(self, bill_data: BillData) -> bool:
        return bill_data.vendor_name == 'NT'

    def refine(self, bill_data: BillData) -> BillData:
        # Example refinement: Extracting Bill Number (pattern: 10 digits)
        match = re.search(r'\b\d{10}\b', bill_data.raw_text)
        if match:
            bill_data.bill_number = match.group(0)
            bill_data.extraction_notes.append("Refined: NT Bill Number extracted.")
        return bill_data
