from src.models.bill_data import BillData
from datetime import datetime

class DateValidator:
    @staticmethod
    def validate(bill: BillData):
        if bill.bill_date and bill.due_date:
            try:
                b = datetime.strptime(bill.bill_date, '%Y-%m-%d')
                d = datetime.strptime(bill.due_date, '%Y-%m-%d')
                if d < b:
                    bill.confidence_flags.append('invalid_due_date')
            except ValueError:
                bill.confidence_flags.append('invalid_date_format')
        return bill
