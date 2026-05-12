import os
from src.services.testing.dataset_loader import DatasetLoader # Need to create this
from src.services.testing.truth_loader import TruthLoader
from src.services.testing.extraction_comparator import ExtractionComparator
from src.workflows.production_pipeline import ProductionPipeline

class RegressionValidator:
    @staticmethod
    def run_regression(dataset_root="datasets/golden"):
        results = []
        for root, _, files in os.walk(dataset_root):
            for file in files:
                if file.endswith(".pdf"):
                    path = os.path.join(root, file)
                    truth = TruthLoader.load(path)
                    if not truth: continue
                    
                    bill = ProductionPipeline.run(path)
                    comparison = ExtractionComparator.compare(bill.bill_data.__dict__, truth)
                    results.append({"file": file, "comparison": comparison})
        return results
