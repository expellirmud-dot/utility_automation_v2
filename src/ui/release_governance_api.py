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

release_router = APIRouter(prefix="/ops", tags=["Release Governance"])

class ReleaseGovernanceResponse(BaseModel):
    certification: dict[str, Any]
    gatekeeper: dict[str, Any]
    authorization: dict[str, Any]

@release_router.get("/api/release-governance", response_model=ReleaseGovernanceResponse)
def get_release_governance() -> ReleaseGovernanceResponse:
    return get_release_governance_data()

@release_router.get("/api/human-review-intent", response_model=List[dict[str, Any]])
def get_human_review_intents() -> List[dict[str, Any]]:
    """
    Read-only surface for human review intent records.
    Deterministic projection data only.
    """
    return HumanReviewIntentProvider.get_latest_review_records()
