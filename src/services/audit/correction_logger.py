import logging

class CorrectionLogger:
    @staticmethod
    def log(record):
        # Configure as needed
        logging.info(f"Correction: {record.field_name} | Orig: {record.original_value} -> New: {record.corrected_value} | Reason: {record.correction_reason}")
