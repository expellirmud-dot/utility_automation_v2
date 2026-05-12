import os
import json
from src.workflows.process_bill_workflow import ProcessBillWorkflow

class RegressionRunner:
    @staticmethod
    def run_all(samples):
        results = []
        for path in samples:
            try:
                bill = ProcessBillWorkflow.run(path)
                results.append({"path": path, "success": True, "bill": bill})
            except Exception as e:
                results.append({"path": path, "success": False, "error": str(e)})
        return results

    @staticmethod
    def generate_report(results, output_path="output/reports/regression.txt"):
        total = len(results)
        successes = [r for r in results if r["success"]]
        failures = [r for r in results if not r["success"]]
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Total Files: {total}\n")
            f.write(f"Successful Extraction: {len(successes)}\n")
            f.write(f"Failed Extraction: {len(failures)}\n\n")
            
            # Additional logic can be added here
