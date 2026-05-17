import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_harness_dirs():
    tmpdir = tempfile.mkdtemp()
    inbox_dir = os.path.join(tmpdir, "inbox")
    contracts_dir = os.path.join(tmpdir, "contracts")
    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(contracts_dir, exist_ok=True)

    valid_req = os.path.join(inbox_dir, "TASK-201-controller-request.md")
    with open(valid_req, "w", encoding="utf-8") as f:
        f.write("""# Controller Execution Request

## Task ID
TASK-201

## Title
Test Automation

## Authority
Human-approved controller request

## Objective
Test objective

## Architectural rationale
Test rationale

## Scope

### In scope
- Item A

### Candidate modules
src/foo.py

### Runtime artifacts
ai_runtime/contracts/
ai_runtime/completions/
ai_runtime/reports/
ai_runtime/inbox/

### Tests
tests/test_foo.py

## Constraints
- ledger remains sole source of truth
- SQLite is projection/cache only
- AI advisory only
- no autonomous authority mutation
- no self-approval
- no hidden execution channels
- no frontend authority expansion
- preserve existing workflow

## Non-goals
- autonomous task planning
- automatic scope invention
- scheduler design
- governance redesign
- promotion authority mutation
- freeform worker autonomy

## Required validation
- deterministic behavior

## Acceptance criteria
- tests pass

## Required execution discipline
READ-FIRST mandatory
Inspect actual files first
Use Serena when relevant
Treat ai_runtime/inbox controller requests as READ-ONLY
No implementation from memory
Return exact validation output
Separate evidence from assumptions

## State
APPROVED FOR IMPLEMENTATION

## Next
TASK 202 [TBD]
""")

    invalid_req = os.path.join(inbox_dir, "TASK-202-controller-request.md")
    with open(invalid_req, "w", encoding="utf-8") as f:
        f.write("""# Controller Execution Request
## Task ID
TASK-202
## Title
REPLACE_WITH_TITLE
""")

    yield inbox_dir, contracts_dir, valid_req, invalid_req
    shutil.rmtree(tmpdir)


def test_start_runtime_task_with_valid_request(temp_harness_dirs):
    inbox_dir, contracts_dir, valid_req, _ = temp_harness_dirs
    script = "src/tools/runtime/start_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-201",
        "--actor-id", "WORKER-01",
        "--request-file", valid_req,
        "--allow-read", "src/",
        "--allow-write", "src/",
        "--expected-output", "src/foo.py",
        "--inbox-dir", inbox_dir,
        "--contracts-dir", contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "SUCCESS"
    assert data["readiness_verified"] is True
    assert data["task_id"] == "TASK-201"
    assert os.path.exists(os.path.join(contracts_dir, "TASK-201.json"))


def test_start_runtime_task_with_invalid_request(temp_harness_dirs):
    inbox_dir, contracts_dir, _, invalid_req = temp_harness_dirs
    script = "src/tools/runtime/start_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-202",
        "--actor-id", "WORKER-01",
        "--request-file", invalid_req,
        "--allow-read", "src/",
        "--allow-write", "src/",
        "--expected-output", "src/foo.py",
        "--inbox-dir", inbox_dir,
        "--contracts-dir", contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["status"] == "FAILED"
    assert data["step"] == "validate_controller_request"


def test_start_runtime_task_with_generation(temp_harness_dirs):
    inbox_dir, contracts_dir, _, _ = temp_harness_dirs
    script = "src/tools/runtime/start_runtime_task.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-203",
        "--actor-id", "WORKER-01",
        "--title", "Generated Request",
        "--objective", "Verify on-the-fly generation",
        "--rationale", "Automation testing",
        "--scope", "Scope item",
        "--candidate-modules", "src/bar.py",
        "--tests", "tests/test_bar.py",
        "--validation", "Val item",
        "--acceptance", "Acc item",
        "--allow-read", "src/",
        "--allow-write", "src/",
        "--expected-output", "src/bar.py",
        "--inbox-dir", inbox_dir,
        "--contracts-dir", contracts_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "SUCCESS"
    assert data["readiness_verified"] is True
    assert data["task_id"] == "TASK-203"
    assert os.path.exists(os.path.join(inbox_dir, "TASK-203-controller-request.md"))
    assert os.path.exists(os.path.join(contracts_dir, "TASK-203.json"))
