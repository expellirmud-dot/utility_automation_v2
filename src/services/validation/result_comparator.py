class ResultComparator:
    def compare(self, predictions, ground_truth):
        matches = 0
        total = len(predictions)
        mismatches = []

        for pred in predictions:
            truth = ground_truth.get(pred["doc"])
            if not truth:
                continue

            if pred["result"].get("decision") == truth.get("decision"):
                matches += 1
            else:
                mismatches.append({
                    "doc": pred["doc"],
                    "pred": pred["result"],
                    "truth": truth
                })

        accuracy = matches / total if total > 0 else 0

        return {
            "accuracy": accuracy,
            "mismatches": mismatches
        }
