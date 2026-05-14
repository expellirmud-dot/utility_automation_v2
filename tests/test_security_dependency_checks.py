from __future__ import annotations

import json
import pytest
from pathlib import Path
from src.tests.certification.certification_models import CertificationCheck
from src.tests.certification.security_dependency_checks import check_security_dependencies

@pytest.fixture
def mock_repo(tmp_path: Path) -> Path:
    return tmp_path

def test_security_dependency_check_pass(mock_repo: Path):
    # Setup: Create valid risk register and package.json
    security_dir = mock_repo / "docs" / "security"
    security_dir.mkdir(parents=True)
    
    risk_register = security_dir / "dependency_risk_register.md"
    risk_register.write_text("Next.js / PostCSS Vulnerabilities\nDeferred due to breaking changes.")

    frontend_dir = mock_repo / "frontend" / "operator-observatory"
    frontend_dir.mkdir(parents=True)
    
    package_json = frontend_dir / "package.json"
    package_json.write_text(json.dumps({"dependencies": {"next": "14.2.33"}}))

    check = CertificationCheck(key="security_dependency_governance", category="validation", description="test", stable_order=110)
    result = check_security_dependencies(mock_repo, check)
    
    assert result.passed is True

def test_security_dependency_check_missing_register(mock_repo: Path):
    # Setup: No risk register
    package_json_dir = mock_repo / "frontend" / "operator-observatory"
    package_json_dir.mkdir(parents=True)
    (package_json_dir / "package.json").write_text(json.dumps({"dependencies": {"next": "14.2.33"}}))

    check = CertificationCheck(key="security_dependency_governance", category="validation", description="test", stable_order=110)
    result = check_security_dependencies(mock_repo, check)
    
    assert result.passed is False
    assert result.failure.reason == "missing_risk_register"

def test_security_dependency_check_missing_documentation(mock_repo: Path):
    # Setup: Risk register exists but doesn't mention the vulnerability
    security_dir = mock_repo / "docs" / "security"
    security_dir.mkdir(parents=True)
    (security_dir / "dependency_risk_register.md").write_text("Some other risk.")

    check = CertificationCheck(key="security_dependency_governance", category="validation", description="test", stable_order=110)
    result = check_security_dependencies(mock_repo, check)
    
    assert result.passed is False
    assert result.failure.reason == "risk_not_documented"

def test_security_dependency_check_unauthorized_upgrade(mock_repo: Path):
    # Setup: Valid register, but package.json has Next 16 without remediation note
    security_dir = mock_repo / "docs" / "security"
    security_dir.mkdir(parents=True)
    (security_dir / "dependency_risk_register.md").write_text("Next.js / PostCSS Vulnerabilities\nDeferred.")

    frontend_dir = mock_repo / "frontend" / "operator-observatory"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "package.json").write_text(json.dumps({"dependencies": {"next": "16.2.6"}}))

    check = CertificationCheck(key="security_dependency_governance", category="validation", description="test", stable_order=110)
    result = check_security_dependencies(mock_repo, check)
    
    assert result.passed is False
    assert result.failure.reason == "unauthorized_breaking_upgrade"

def test_security_dependency_check_authorized_upgrade(mock_repo: Path):
    # Setup: Valid register with remediation note, and package.json has Next 16
    security_dir = mock_repo / "docs" / "security"
    security_dir.mkdir(parents=True)
    (security_dir / "dependency_risk_register.md").write_text("Next.js / PostCSS Vulnerabilities\nUpdated to 16 and remediated.")

    frontend_dir = mock_repo / "frontend" / "operator-observatory"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "package.json").write_text(json.dumps({"dependencies": {"next": "16.2.6"}}))

    check = CertificationCheck(key="security_dependency_governance", category="validation", description="test", stable_order=110)
    result = check_security_dependencies(mock_repo, check)
    
    assert result.passed is True
