from src.services.validation.result_comparator import ResultComparator
from src.services.validation.reality_drift_analyzer import RealityDriftAnalyzer
from src.services.validation.reality_score_engine import RealityScoreEngine
from src.services.validation.reality_report import RealityReport

class RealWorldValidator:
    def __init__(self):
        self.comparator = ResultComparator()
        self.drift = RealityDriftAnalyzer()
        self.scorer = RealityScoreEngine()
        self.reporter = RealityReport()

    def validate(self, predictions, ground_truth, sim_metrics, real_metrics):
        comparison = self.comparator.compare(predictions, ground_truth)
        drift = self.drift.analyze(sim_metrics, real_metrics)
        score = self.scorer.score(comparison["accuracy"], drift)

        return self.reporter.generate(
            comparison["accuracy"],
            drift,
            score
        )
