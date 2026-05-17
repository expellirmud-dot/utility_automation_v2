import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable

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


@pytest.fixture
def temp_request_files():
    tmpdir = tempfile.mkdtemp()
    valid_path = os.path.join(tmpdir, "valid_request.md")
    with open(valid_path, "w", encoding="utf-8") as f:
        f.write(VALID_CONTENT)

    invalid_ph_path = os.path.join(tmpdir, "invalid_ph.md")
    with open(invalid_ph_path, "w", encoding="utf-8") as f:
        f.write(INVALID_CONTENT_PLACEHOLDER)

    invalid_sec_path = os.path.join(tmpdir, "invalid_sec.md")
    with open(invalid_sec_path, "w", encoding="utf-8") as f:
        f.write(INVALID_CONTENT_MISSING_SECTION)

    yield valid_path, invalid_ph_path, invalid_sec_path
    shutil.rmtree(tmpdir)


def test_cli_valid_request(temp_request_files):
    valid_path, _, _ = temp_request_files
    script = "src/tools/runtime/validate_controller_request.py"
    cmd = [PYTHON_EXE, script, "--request-file", valid_path]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["is_valid"] is True
    assert data["task_id"] == "TASK-078"


def test_cli_invalid_placeholder_fails(temp_request_files):
    _, invalid_ph_path, _ = temp_request_files
    script = "src/tools/runtime/validate_controller_request.py"
    cmd = [PYTHON_EXE, script, "--request-file", invalid_ph_path]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["is_valid"] is False
    assert len(data["placeholders_found"]) > 0


def test_cli_invalid_missing_section_fails(temp_request_files):
    _, _, invalid_sec_path = temp_request_files
    script = "src/tools/runtime/validate_controller_request.py"
    cmd = [PYTHON_EXE, script, "--request-file", invalid_sec_path]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["is_valid"] is False
    assert "Scope" in data["missing_sections"]
