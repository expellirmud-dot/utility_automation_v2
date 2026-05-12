from src.models.bill_data import BillData

class ConsistencyChecker:
    @staticmethod
    def check(bill: BillData):
        # Example check
        if bill.vendor_name == 'NT' and bill.account_number and len(bill.account_number) < 5:
            bill.extraction_notes.append("Warning: Short account number for NT")
        return bill
