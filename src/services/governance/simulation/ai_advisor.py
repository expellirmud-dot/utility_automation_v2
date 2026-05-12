from .simulation_report import AIAdvice


class EvidenceOnlyAIAdvisor:
    def advise(self, deterministic_evidence: dict) -> AIAdvice:
        warnings = []
        if deterministic_evidence.get("risk_findings"):
            warnings.append("Deterministic risk findings require human review.")
        if deterministic_evidence.get("conflict_findings"):
            warnings.append("Deterministic conflict findings require remediation.")
        return AIAdvice(warnings=tuple(warnings), notes=("Advisory only; deterministic evidence remains authoritative.",))
