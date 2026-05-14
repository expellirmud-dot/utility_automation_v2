from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class CertificationFailure:
    check_key: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "check_key": self.check_key,
            "detail": self.detail,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CertificationCheck:
    key: str
    category: str
    description: str
    stable_order: int
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "description": self.description,
            "key": self.key,
            "required": self.required,
            "stable_order": self.stable_order,
        }


@dataclass(frozen=True)
class CertificationResult:
    check: CertificationCheck
    passed: bool
    failure: CertificationFailure | None = None

    def __post_init__(self) -> None:
        if not self.passed and self.failure is None:
            raise ValueError("failed certification result requires a failure")

    def to_dict(self) -> dict[str, object]:
        return {
            "check": self.check.to_dict(),
            "failure": self.failure.to_dict() if self.failure else None,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class CertificationArtifact:
    results: tuple[CertificationResult, ...]
    metadata: dict[str, str] = field(default_factory=dict)
    artifact_version: str = "task-049-certification-v1"

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.results, key=lambda item: item.check.stable_order))
        if ordered != self.results:
            raise ValueError("certification results must be in canonical order")

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def overall_score(self) -> float:
        if not self.results:
            return 0.0
        passed_count = sum(1 for result in self.results if result.passed)
        return (passed_count / len(self.results)) * 100

    @property
    def failures(self) -> tuple[CertificationFailure, ...]:
        return tuple(result.failure for result in self.results if result.failure is not None)

    def identity_payload(self) -> dict[str, object]:
        return {
            "artifact_version": self.artifact_version,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
        }

    @property
    def artifact_hash(self) -> str:
        return hashlib.sha256(canonical_json(self.identity_payload()).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "artifact_hash": self.artifact_hash,
            "metadata": dict(sorted(self.metadata.items())),
        }
