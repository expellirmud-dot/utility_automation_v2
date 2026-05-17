import os
import pytest
import tempfile
import shutil
from src.services.governance.execution_contract.artifact_bundle_validator import ArtifactBundleValidator
from src.services.governance.execution_contract.execution_contract_exceptions import EvidenceValidationError


@pytest.fixture
def temp_env():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_validate_execution_transcript_valid(temp_env):
    file_path = os.path.join(temp_env, "transcript.md")
    content = """# Execution Transcript
## Task identification
TASK-123
## Read-first inspection
Checked files.
## Files inspected
- a.py
## Files changed
- b.py
## Commands executed
- pytest
## Validation summary
All passed.
## Notes
None.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    validator = ArtifactBundleValidator(task_id="TASK-123", root_dir=temp_env)
    validator.validate_execution_transcript("transcript.md")


def test_validate_execution_transcript_missing_heading_fails(temp_env):
    file_path = os.path.join(temp_env, "transcript_bad.md")
    content = """# Execution Transcript
## Task identification
TASK-123
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    validator = ArtifactBundleValidator(task_id="TASK-123", root_dir=temp_env)
    with pytest.raises(EvidenceValidationError, match="Execution transcript missing required template sections: Read-first inspection"):
        validator.validate_execution_transcript("transcript_bad.md")


def test_validate_worker_report_valid(temp_env):
    file_path = os.path.join(temp_env, "report.md")
    content = """# Worker Report
## Objective
Goal.
## Scope completed
Done.
## Artifacts produced
- x.py
## Validation results
Passed.
## Risks
None.
## Controller handoff
Ready.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    validator = ArtifactBundleValidator(task_id="TASK-123", root_dir=temp_env)
    validator.validate_worker_report("report.md")


def test_validate_validation_output_empty_fails(temp_env):
    file_path = os.path.join(temp_env, "val.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        pass  # empty

    validator = ArtifactBundleValidator(task_id="TASK-123", root_dir=temp_env)
    with pytest.raises(EvidenceValidationError, match="Validation output artifact is empty"):
        validator.validate_validation_output("val.txt")
