from src.models.bill_data import BillData

class FieldValidator:
    @staticmethod
    def validate(bill: BillData):
        if not bill.bill_number:
            bill.confidence_flags.append('missing_bill_number')
        if not bill.total:
            bill.confidence_flags.append('missing_total')
        if not bill.account_number:
            bill.confidence_flags.append('missing_account_number')
        return bill
