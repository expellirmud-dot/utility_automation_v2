import pytest
from src.services.governance.execution_contract.controller_request_validator import ControllerRequestValidator


VALID_CONTENT = """# Controller Execution Request

## Task ID
TASK-078

## Title
Runtime Workflow Genericization

## Authority
Human-approved controller request

## Objective
Harden the governed runtime workflow by eliminating placeholders.

## Scope
- generic runtime workflow normalization
- controller request completeness validator

## Required validation
- deterministic behavior

## Acceptance criteria
- implementation complete

## Next
TASK 079 [TBD]
"""

INVALID_CONTENT_PLACEHOLDER = """# Controller Execution Request

## Task ID
TASK-078

## Title
REPLACE_WITH_TITLE

## Objective
[REPLACE OBJECTIVE]

## Scope
- [REPLACE]

## Required validation
- deterministic behavior

## Acceptance criteria
- implementation complete
"""

INVALID_CONTENT_MISSING_SECTION = """# Controller Execution Request

## Task ID
TASK-078

## Title
Valid Title

## Objective
Valid Objective

## Required validation
- deterministic behavior
"""


def test_validator_valid_content():
    validator = ControllerRequestValidator()
    result = validator.validate_request_content(VALID_CONTENT)
    assert result["is_valid"] is True
    assert result["task_id"] == "TASK-078"
    assert result["title"] == "Runtime Workflow Genericization"
    assert len(result["missing_sections"]) == 0
    assert len(result["placeholders_found"]) == 0


def test_validator_placeholders_detected():
    validator = ControllerRequestValidator()
    result = validator.validate_request_content(INVALID_CONTENT_PLACEHOLDER)
    assert result["is_valid"] is False
    assert len(result["placeholders_found"]) > 0
    assert any("REPLACE_WITH_TITLE" in p for p in result["placeholders_found"])
    assert any("[REPLACE OBJECTIVE]" in p for p in result["placeholders_found"])


def test_validator_missing_sections():
    validator = ControllerRequestValidator()
    result = validator.validate_request_content(INVALID_CONTENT_MISSING_SECTION)
    assert result["is_valid"] is False
    assert "Scope" in result["missing_sections"]
    assert "Acceptance criteria" in result["missing_sections"]
