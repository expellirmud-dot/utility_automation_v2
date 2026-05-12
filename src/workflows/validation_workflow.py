from src.services.validation.field_validator import FieldValidator
from src.services.validation.amount_validator import AmountValidator
from src.services.validation.date_validator import DateValidator
from src.services.validation.consistency_checker import ConsistencyChecker
from src.models.bill_data import BillData

class ValidationWorkflow:
    @staticmethod
    def run(bill: BillData) -> BillData:
        bill = FieldValidator.validate(bill)
        bill = AmountValidator.validate(bill)
        bill = DateValidator.validate(bill)
        bill = ConsistencyChecker.check(bill)
        return bill
