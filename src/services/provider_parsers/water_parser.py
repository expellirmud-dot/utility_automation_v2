from src.services.provider_parsers.base_provider_parser import BaseProviderParser
from src.models.bill_data import BillData
import re

class WaterParser(BaseProviderParser):
    def can_handle(self, bill_data: BillData) -> bool:
        return bill_data.vendor_name == 'Water'

    def refine(self, bill_data: BillData) -> BillData:
        # Example: Usage Period
        match = re.search(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', bill_data.raw_text)
        if match:
            bill_data.service_period = f"{match.group(1)} to {match.group(2)}"
            bill_data.extraction_notes.append("Refined: Water service period extracted.")
        return bill_data
