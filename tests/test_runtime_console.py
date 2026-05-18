import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_console_dirs():
    tmpdir = tempfile.mkdtemp()
    inbox_dir = os.path.join(tmpdir, "inbox")
    contracts_dir = os.path.join(tmpdir, "contracts")
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(contracts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    yield tmpdir, inbox_dir, contracts_dir, reports_dir
    shutil.rmtree(tmpdir)


def test_console_create_and_status(temp_console_dirs):
    tmpdir, inbox_dir, contracts_dir, reports_dir = temp_console_dirs
    script = "src/tools/runtime/runtime_console.py"

    req_file = os.path.join(inbox_dir, "TASK-777-controller-request.md")
    cmd_create = [
        PYTHON_EXE, script, "create",
        "--task-id", "TASK-777",
        "--title", "Console Test",
        "--objective", "Obj",
        "--rationale", "Rat",
        "--scope", "Scp",
        "--candidate-modules", "mod.py",
        "--tests", "test_mod.py",
        "--validation", "Val",
        "--acceptance", "Acc",
        "--output-file", req_file,
        "--inbox-dir", inbox_dir
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd_create, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert os.path.exists(req_file)

    cmd_status = [
        PYTHON_EXE, script, "status",
        "--contracts-dir", contracts_dir,
        "--reports-dir", reports_dir,
        "--format", "table"
    ]
    res = subprocess.run(cmd_status, env=env, capture_output=True, text=True)
    assert res.returncode == 0
