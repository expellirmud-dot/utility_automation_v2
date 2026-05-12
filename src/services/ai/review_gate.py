from src.models.bill_data import BillData

class ReviewGate:
    @staticmethod
    def should_trigger(bill: BillData) -> bool:
        # Trigger if confidence flags exist or required field missing
        if bill.confidence_flags:
            return True
        if not bill.vendor_name or not bill.total:
            return True
        return False
