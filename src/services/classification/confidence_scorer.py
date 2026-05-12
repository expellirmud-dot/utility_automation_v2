import json

class ConfidenceScorer:
    # V2 weights: Layout is primary
    WEIGHTS = {"ocr": 0.3, "keyword": 0.25, "layout": 0.35, "filename": 0.1}

    @staticmethod
    def calculate(signals):
        score = sum(signals.get(k, 0) * ConfidenceScorer.WEIGHTS[k] for k in ConfidenceScorer.WEIGHTS)
        return round(score, 2)
