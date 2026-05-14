import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.governance.certification.models import (
    CertificationArtifact,
    CertificationCheck,
    CertificationResult,
    CertificationFailure,
)
from src.services.governance.promotion_governance.promotion_gatekeeper import PromotionGatekeeperEvaluator
from src.services.governance.promotion_governance.release_authorizer import ReleaseAuthorizer

# Re-use the existing router and prefix from the file
# (I will add these to the existing file via edit)

class ReleaseGovernanceResponse(BaseModel):
    certification: dict[str, Any]
    gatekeeper: dict[str, Any]
    authorization: dict[str, Any]

def get_release_governance_data() -> ReleaseGovernanceResponse:
    # Path to the latest deterministic certification artifact
    artifact_path = Path("output/certification/certification_artifact.json")
    
    if not artifact_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="No certification artifact found. Please run the certification pipeline first."
        )
    
    # 1. Load Certification Artifact
    artifact_data = json.loads(artifact_path.read_text(encoding="utf-8"))
    # We need to reconstruct the CertificationArtifact object for the evaluators
    # Note: This assumes the artifact was written via to_dict()
    # In a real system, we'd have a proper from_dict() method.
    # For now, we reconstruct the results tuple.
    
    results = []
    for r in artifact_data["results"]:
        check = CertificationCheck(**r["check"])
        failure = CertificationFailure(**r["failure"]) if r["failure"] else None
        results.append(CertificationResult(check=check, passed=r["passed"], failure=failure))
    
    artifact = CertificationArtifact(
        results=tuple(results),
        metadata=artifact_data.get("metadata", {})
    )
    
    # 2. Evaluate Gatekeeper
    gatekeeper_report = PromotionGatekeeperEvaluator.evaluate(artifact)
    
    # 3. Evaluate Release Authorization
    auth_bundle = ReleaseAuthorizer.authorize(artifact, gatekeeper_report)
    
    return ReleaseGovernanceResponse(
        certification=artifact.to_dict(),
        gatekeeper=gatekeeper_report.to_dict(),
        authorization=auth_bundle.to_dict()
    )
