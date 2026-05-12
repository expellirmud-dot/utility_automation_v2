from src.storage.repositories.bill_repository import BillRepository

class PersistenceWorkflow:
    @staticmethod
    def persist_bill(bill_data):
        try:
            return BillRepository.save(bill_data)
        except Exception as e:
            # Handle rollback/logging
            print(f"Persistence failed: {e}")
            raise
