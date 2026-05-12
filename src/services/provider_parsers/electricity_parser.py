from src.services.provider_parsers.base_provider_parser import BaseProviderParser
from src.models.bill_data import BillData
import re

class ElectricityParser(BaseProviderParser):
    def can_handle(self, bill_data: BillData) -> bool:
        return bill_data.vendor_name == 'Electricity'

    def refine(self, bill_data: BillData) -> BillData:
        # Example: Extract Account Number (CA)
        match = re.search(r'CA\s*(\d{9,12})', bill_data.raw_text)
        if match:
            bill_data.account_number = match.group(1)
            bill_data.extraction_notes.append("Refined: CA Account Number extracted.")
        return bill_data
