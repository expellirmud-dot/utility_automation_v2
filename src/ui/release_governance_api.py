from pathlib import Path
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, List

from src.services.governance.promotion_governance.release_governance_provider import (
    get_release_governance_data,
)
from src.services.governance.promotion_governance.human_review_intent_provider import (
    HumanReviewIntentProvider,
)
from src.services.governance.promotion_governance.evidence_package_provider import (
    EvidencePackageProvider,
)
from src.services.governance.promotion_governance.evidence_package_integrity_provider import (
    EvidencePackageIntegrityProvider,
)
from src.services.governance.promotion_governance.evidence_package_readiness_provider import (
    EvidencePackageReadinessProvider,
)
from src.services.governance.promotion_governance.evidence_review_summary_provider import (
    EvidenceReviewSummaryProvider,
)

release_router = APIRouter(prefix="/ops/api", tags=["Release Governance"])

class ReleaseGovernanceResponse(BaseModel):
    certification: dict[str, Any]
    gatekeeper: dict[str, Any]
    authorization: dict[str, Any]

class EvidencePackageResponse(BaseModel):
    package: dict[str, Any]

class EvidencePackageIntegrityResponse(BaseModel):
    report: dict[str, Any]

class EvidencePackageReadinessResponse(BaseModel):
    report: dict[str, Any]

class EvidenceReviewSummaryResponse(BaseModel):
    summary: dict[str, Any]

@release_router.get("/release-governance", response_model=ReleaseGovernanceResponse)
def get_release_governance() -> ReleaseGovernanceResponse:
    return get_release_governance_data()

@release_router.get("/evidence-package", response_model=EvidencePackageResponse)
def get_evidence_package() -> EvidencePackageResponse:
    """
    Read-only surface for the Governance Evidence Package.
    Deterministic projection data only.
    """
    return EvidencePackageProvider.get_evidence_package_projection()

@release_router.get("/evidence-package-integrity", response_model=EvidencePackageIntegrityResponse)
def get_evidence_package_integrity() -> EvidencePackageIntegrityResponse:
    """
    Read-only surface for the Evidence Package Integrity Report.
    Deterministic projection data only.
    """
    return EvidencePackageIntegrityProvider.get_integrity_projection()

@release_router.get("/evidence-package-readiness", response_model=EvidencePackageReadinessResponse)
def get_evidence_package_readiness() -> EvidencePackageReadinessResponse:
    """
    Read-only surface for the Evidence Package Readiness Report.
    Deterministic projection data only.
    """
    return EvidencePackageReadinessProvider.get_readiness_projection()

@release_router.get("/evidence-review-summary", response_model=EvidenceReviewSummaryResponse)
def get_evidence_review_summary() -> EvidenceReviewSummaryResponse:
    """
    Read-only surface for the Evidence Review Summary.
    Deterministic projection data only.
    """
    return EvidenceReviewSummaryProvider.get_summary_projection()

@release_router.get("/human-review-intent", response_model=List[dict[str, Any]])



def get_human_review_intents() -> List[dict[str, Any]]:
    """
    Read-only surface for human review intent records.
    Deterministic projection data only.
    """
    return HumanReviewIntentProvider.get_latest_review_records()
