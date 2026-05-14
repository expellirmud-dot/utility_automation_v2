"""
Promotion governance artifact generator.

Generates deterministic promotion manifests for governance review.
Output format: JSON with no timestamps in identity hash.
Output location: output/promotion/promotion_manifest.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.services.governance.promotion_governance.promotion_models import (
    PromotionRequest,
    PromotionEligibility,
    PromotionDecision,
    PromotionBundle,
    canonical_json,
)


class PromotionManifestGenerator:
    """
    Generates deterministic promotion governance manifests.
    
    Output:
    - JSON file with no timestamps in identity
    - Deterministic and hashable
    - Canonical ordering preserved
    """

    DEFAULT_OUTPUT_DIR = Path("output/promotion")

    @staticmethod
    def generate_manifest(
        bundle: PromotionBundle,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Generate and save promotion manifest.

        Args:
            bundle: PromotionBundle with complete governance info
            output_dir: Optional output directory (default: output/promotion)

        Returns:
            Path to generated manifest file
        """
        if output_dir is None:
            output_dir = PromotionManifestGenerator.DEFAULT_OUTPUT_DIR

        # Ensure directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate manifest
        manifest = {
            "type": "promotion_governance_manifest",
            "version": "task-050-b-promotion-governance-v1",
            "bundle": bundle.to_dict(),
        }

        # Write deterministically
        manifest_path = output_dir / "promotion_manifest.json"
        manifest_json = canonical_json(manifest)

        with open(manifest_path, "w", encoding="utf-8") as f:
            # Pretty-print for readability, but preserving deterministic structure
            f.write(json.dumps(json.loads(manifest_json), indent=2, ensure_ascii=True))

        return manifest_path

    @staticmethod
    def load_manifest(manifest_path: Path) -> dict:
        """Load and parse promotion manifest."""
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def verify_manifest_determinism(manifest_path: Path) -> bool:
        """
        Verify manifest is deterministically serializable.

        Args:
            manifest_path: Path to manifest file

        Returns:
            True if manifest can be deterministically serialized
        """
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)

            # Re-serialize canonically and verify
            canonical = canonical_json(manifest)
            # Verify it's valid JSON
            json.loads(canonical)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_simple_decision_bundle(
        source_version_id: str,
        target_stage: str,
        requested_by: str,
        eligibility: PromotionEligibility,
        request_epoch: int = 1,
        request_seq: int = 1,
        decision_epoch: int = 1,
        decision_seq: int = 1,
    ) -> PromotionBundle:
        """
        Convenience method to generate a complete bundle for testing.

        Args:
            source_version_id: Version to promote
            target_stage: Target promotion stage
            requested_by: Requesting actor
            eligibility: PromotionEligibility result
            request_epoch: Request epoch (deterministic)
            request_seq: Request sequence (deterministic)
            decision_epoch: Decision epoch (deterministic)
            decision_seq: Decision sequence (deterministic)

        Returns:
            PromotionBundle ready for manifest generation
        """
        # Create request
        request = PromotionRequest(
            source_version_id=source_version_id,
            target_stage=target_stage,
            requested_by=requested_by,
            request_epoch=request_epoch,
            request_seq=request_seq,
        )

        # Determine decision based on eligibility
        if eligibility.eligible:
            decision_str = "approved"
            rationale = "All promotion eligibility criteria satisfied"
        else:
            decision_str = "deferred"
            rationale = (
                f"Promotion deferred: {len(eligibility.failures)} "
                f"criterion/criteria not satisfied"
            )

        # Create decision
        decision = PromotionDecision(
            promotion_request=request,
            eligibility=eligibility,
            decision=decision_str,
            decision_rationale=rationale,
            decision_epoch=decision_epoch,
            decision_seq=decision_seq,
        )

        # Create bundle
        bundle = PromotionBundle(
            request=request,
            eligibility=eligibility,
            decision=decision,
        )

        return bundle
