from src.services.review.correction_service import CorrectionService
from src.services.audit.correction_logger import CorrectionLogger

class CorrectionWorkflow:
    @staticmethod
    def apply(item, field, original, corrected, reason, user):
        record = CorrectionService.apply_correction(field, original, corrected, reason, user)
        CorrectionLogger.log(record)
        return record
