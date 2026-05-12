from src.models.bill_data import BillData

class AmountValidator:
    @staticmethod
    def validate(bill: BillData):
        if bill.total and bill.total < 0:
            bill.confidence_flags.append('negative_total')
        if bill.subtotal and bill.vat and bill.total:
            if abs((bill.subtotal + bill.vat) - bill.total) > 0.01:
                bill.confidence_flags.append('subtotal_mismatch')
        return bill
