class RootCauseAnalyzer:
    def analyze(self, bottlenecks):
        causes = []

        for b in bottlenecks:
            if b["stage"] == "SEMANTIC":
                causes.append("Complex rule evaluation or large ontology load")
            elif b["stage"] == "FINANCIAL":
                causes.append("Redundant validation or nested calculations")
            elif b["stage"] == "GOVERNANCE":
                causes.append("Rule versioning conflict or audit overhead")
            elif b["stage"] == "OCR":
                causes.append("Input size or parsing inefficiency")
            else:
                causes.append(f"Unknown bottleneck in {b['stage']}")

        return list(set(causes)) # Return unique causes
