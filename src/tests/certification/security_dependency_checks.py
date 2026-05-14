from __future__ import annotations

import json
from pathlib import Path
from src.tests.certification.certification_models import (
    CertificationCheck,
    CertificationFailure,
    CertificationResult,
)


def check_security_dependencies(
    repo_root: Path, 
    check: CertificationCheck
) -> CertificationResult:
    """
    Deterministic security dependency check.
    Ensures that known risks are registered and no unauthorized breaking upgrades occur.
    """
    risk_register_path = repo_root / "docs" / "security" / "dependency_risk_register.md"
    package_json_path = repo_root / "frontend" / "operator-observatory" / "package.json"

    # 1. Verify Risk Register presence
    if not risk_register_path.exists():
        return CertificationResult(
            check=check,
            passed=False,
            failure=CertificationFailure(
                check_key=check.key,
                reason="missing_risk_register",
                detail=f"Risk register not found at {risk_register_path}",
            ),
        )

    # 2. Verify Risk Register content
    content = risk_register_path.read_text(encoding="utf-8")
    if "Next.js / PostCSS Vulnerabilities" not in content:
        return CertificationResult(
            check=check,
            passed=False,
            failure=CertificationFailure(
                check_key=check.key,
                reason="risk_not_documented",
                detail="Next.js/PostCSS vulnerabilities must be documented in the risk register.",
            ),
        )

    # 3. Prevent unauthorized breaking upgrade to Next 16
    if package_json_path.exists():
        try:
            pkg = json.loads(package_json_path.read_text(encoding="utf-8"))
            next_version = pkg.get("dependencies", {}).get("next", "")
            
            # Simple version check: if it starts with 16, it's a major upgrade
            if next_version.strip("^").strip("~").startswith("16"):
                # Check if the register has been updated to reflect the upgrade
                if "remediated" not in content.lower() and "updated to 16" not in content.lower():
                    return CertificationResult(
                        check=check,
                        passed=False,
                        failure=CertificationFailure(
                            check_key=check.key,
                            reason="unauthorized_breaking_upgrade",
                            detail=f"Next.js version {next_version} detected, but risk register not updated to reflect remediation.",
                        ),
                    )
        except Exception as e:
            return CertificationResult(
                check=check,
                passed=False,
                failure=CertificationFailure(
                    check_key=check.key,
                    reason="package_json_parse_error",
                    detail=str(e),
                ),
            )

    return CertificationResult(check=check, passed=True)

