from src.models.bill_data import BillData
from src.services.provider_parsers.nt_parser import NTParser

def test_nt_parser():
    bill = BillData(vendor_name='NT', raw_text="Here is your bill 1234567890 for NT")
    parser = NTParser()
    if parser.can_handle(bill):
        bill = parser.refine(bill)
        print(f"Refined Bill: {bill}")

if __name__ == "__main__":
    test_nt_parser()
