from src.services.testing.sample_loader import SampleLoader
from src.services.testing.regression_runner import RegressionRunner

def run_regression():
    samples = SampleLoader.get_all_samples()
    results = RegressionRunner.run_all(samples)
    RegressionRunner.generate_report(results)
    print("Regression report generated at output/reports/regression.txt")

if __name__ == "__main__":
    run_regression()
