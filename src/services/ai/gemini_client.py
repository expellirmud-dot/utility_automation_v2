import time
import logging
from src.config.ai_config import AIConfig
from src.models.bill_data import BillData

# Setup basic logging for AI actions
logging.basicConfig(filename='output/pipeline_logs/ai_review.log', level=logging.INFO)

class GeminiClient:
    def __init__(self):
        self.config = AIConfig()

    def execute_prompt(self, prompt: str) -> str:
        # Placeholder for actual API integration
        # Real-world usage: model.generate_content(prompt)
        return '{"suspicious_fields": ["total"], "manual_review_required": true}'

    def _log_review(self, duration, status):
        logging.info(f"Model: {self.config.MODEL_NAME} | Timestamp: {time.time()} | Duration: {duration}ms | Status: {status}")
