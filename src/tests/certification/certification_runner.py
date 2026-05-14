from __future__ import annotations

import json
from pathlib import Path

from src.tests.certification.certification_checks import run_registered_checks
from src.services.governance.certification.models import (
    CertificationArtifact,
)



DEFAULT_ARTIFACT_PATH = Path("output/certification/certification_artifact.json")
LEGACY_REPORT_PATH = Path("output/certification/cert_report.json")


class CertificationRunner:
    def __init__(self, artifact_path: Path | str = DEFAULT_ARTIFACT_PATH) -> None:
        self.artifact_path = Path(artifact_path)

    def run(self) -> CertificationArtifact:
        artifact = CertificationArtifact(results=run_registered_checks())
        self.write_artifact(artifact)
        return artifact

    def write_artifact(self, artifact: CertificationArtifact) -> None:
        payload = artifact.to_dict()
        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        LEGACY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_REPORT_PATH.write_text(
            json.dumps(self._legacy_report(artifact), sort_keys=True, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    def _legacy_report(self, artifact: CertificationArtifact) -> dict[str, object]:
        report: dict[str, object] = {
            result.check.key: "PASS" if result.passed else "FAIL"
            for result in artifact.results
        }
        report["artifact_hash"] = artifact.artifact_hash
        report["overall_score"] = artifact.overall_score
        return report
