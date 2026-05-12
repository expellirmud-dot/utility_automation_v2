from src.models.bill_data import BillData
from src.services.extraction.date_parser import DateParser
from src.services.extraction.amount_parser import AmountParser
from src.services.extraction.vendor_detector import VendorDetector
import re

class FieldExtractorService:
    @staticmethod
    def extract(raw_text: str) -> BillData:
        bill = BillData(raw_text=raw_text)
        
        # Vendor
        bill.vendor_name = VendorDetector.detect(raw_text)
        if not bill.vendor_name:
            bill.confidence_flags.append('low_vendor_confidence')
            
        # Amount (Heuristic: search for lines ending with amount)
        amounts = [AmountParser.parse(line) for line in raw_text.splitlines() if AmountParser.parse(line)]
        if amounts:
            bill.total = amounts[0] # Simplistic strategy
        else:
            bill.confidence_flags.append('missing_total')
            
        # Date
        bill.bill_date = DateParser.parse(raw_text)
        if not bill.bill_date:
            bill.confidence_flags.append('invalid_date')
            
        return bill
