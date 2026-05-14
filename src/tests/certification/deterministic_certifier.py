from __future__ import annotations

import json
import sys

from src.tests.certification.certification_runner import CertificationRunner


class DeterministicCertifier:
    def __init__(self) -> None:
        self.runner = CertificationRunner()

    def run_all_certifications(self) -> dict[str, object]:
        artifact = self.runner.run()
        return artifact.to_dict()


def main() -> int:
    artifact_payload = DeterministicCertifier().run_all_certifications()
    print(json.dumps(artifact_payload, sort_keys=True, indent=2, ensure_ascii=True))
    return 0 if artifact_payload["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
