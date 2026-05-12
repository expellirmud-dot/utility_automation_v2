class ExtractionComparator:
    @staticmethod
    def compare(extracted: dict, truth: dict) -> dict:
        results = {"exact_match": True, "differences": {}}
        for key, expected in truth.items():
            actual = extracted.get(key)
            if actual != expected:
                results["exact_match"] = False
                results["differences"][key] = {"expected": expected, "actual": actual}
        return results
