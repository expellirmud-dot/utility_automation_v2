import json
from src.models.ai_review_result import AIReviewResult

class AIResponseParser:
    @staticmethod
    def parse(raw_response: str) -> AIReviewResult:
        result = AIReviewResult(raw_ai_response=raw_response)
        try:
            # Simple attempt to locate JSON block
            start = raw_response.find('{')
            end = raw_response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = raw_response[start:end]
                data = json.loads(json_str)
                result.suspicious_fields = data.get("suspicious_fields", [])
                result.warnings = data.get("warnings", [])
                result.manual_review_required = data.get("manual_review_required", False)
                result.review_summary = data.get("review_summary", "")
                result.confidence_assessment = data.get("confidence_assessment", "")
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            result.parsing_error = str(e)
        return result
