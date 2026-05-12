from src.storage.database.database_manager import DatabaseManager
from src.storage.repositories.bill_repository import BillRepository

class MockBill:
    def __init__(self):
        self.vendor_name = 'NT'
        self.total = 100.0
        self.raw_text = 'test'
        self.source_file = 'test.pdf'

def test():
    DatabaseManager.initialize()
    b = MockBill()
    BillRepository.save(b)
    print("Persistence successful")

if __name__ == "__main__":
    test()
