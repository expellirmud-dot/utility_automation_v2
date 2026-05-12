from src.services.performance.telemetry_collector import TelemetryCollector
from src.services.performance.bottleneck_detector import BottleneckDetector
from src.services.performance.root_cause_analyzer import RootCauseAnalyzer
from src.services.performance.performance_report import PerformanceReport

class BottleneckAnalyzer:
    def __init__(self):
        self.telemetry = TelemetryCollector()
        self.detector = BottleneckDetector()
        self.rca = RootCauseAnalyzer()
        self.reporter = PerformanceReport()

    def analyze(self, pipeline_runner=None):
        # Allow passing pipeline_runner to integrate smoothly with the system execution
        stats = self.telemetry.get_stats()
        bottlenecks = self.detector.detect(stats)
        causes = self.rca.analyze(bottlenecks)

        return self.reporter.generate(stats, bottlenecks, causes)

    def instrument(self):
        return self.telemetry
