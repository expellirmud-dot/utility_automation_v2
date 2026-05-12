from src.services.ai.gemini_client import GeminiClient
from src.services.ai.ai_prompt_builder import AIPromptBuilder
from src.services.ai.ai_response_parser import AIResponseParser
from src.models.bill_data import BillData
from src.models.ai_review_result import AIReviewResult

class AIReviewService:
    def __init__(self):
        self.client = GeminiClient()

    def run_review(self, bill: BillData) -> AIReviewResult:
        prompt = AIPromptBuilder.build_prompt(bill)
        # Note: calling internal client logic
        raw_response = self.client.execute_prompt(prompt)
        return AIResponseParser.parse(raw_response)
