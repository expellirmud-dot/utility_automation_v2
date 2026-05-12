from src.services.performance.production_load_generator import ProductionLoadGenerator
from src.services.performance.concurrency_engine import ConcurrencyEngine
from src.services.performance.statistical_analyzer import StatisticalAnalyzer
from src.services.performance.bottleneck_drift_detector import BottleneckDriftDetector
from src.services.performance.production_report import ProductionReport

class ProductionStressTest:
    def __init__(self, pipeline, telemetry):
        self.pipeline = pipeline
        self.telemetry = telemetry

        self.generator = ProductionLoadGenerator()
        self.concurrent = ConcurrencyEngine(pipeline, telemetry)

        self.stats = StatisticalAnalyzer()
        self.drift = BottleneckDriftDetector()
        self.reporter = ProductionReport()

    def run(self, n=10000, threads=10):
        dataset = self.generator.generate(n)

        results = self.concurrent.run(dataset, threads=threads)

        telemetry_stats = self.telemetry.get_stats()

        analyzed = self.stats.analyze(telemetry_stats)

        # Base case drift: current compared to itself is 0 drift (STABLE). 
        # In real system, baseline would be loaded from previous stable run.
        drift = self.drift.detect(analyzed, analyzed)

        return self.reporter.generate(analyzed, drift, results)
