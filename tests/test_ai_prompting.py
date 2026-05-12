from src.services.ai.ai_prompt_builder import AIPromptBuilder
from src.models.bill_data import BillData

def test_prompting():
    bill = BillData(vendor_name='NT', confidence_flags=['missing_total'])
    prompt = AIPromptBuilder.build_prompt(bill)
    print(prompt)

if __name__ == "__main__":
    test_prompting()
