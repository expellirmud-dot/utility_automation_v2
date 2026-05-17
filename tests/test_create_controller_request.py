import os
import sys
import json
import pytest
import tempfile
import shutil
import subprocess


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_output_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_create_controller_request_success(temp_output_dir):
    out_file = os.path.join(temp_output_dir, "TASK-TEST-002-controller-request.md")
    script = "src/tools/runtime/create_controller_request.py"

    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-TEST-002",
        "--title", "Automated Test Title",
        "--objective", "Verify CLI generation",
        "--rationale", "Robustness testing",
        "--scope", "Item A", "Item B",
        "--candidate-modules", "src/foo.py", "src/bar.py",
        "--tests", "tests/test_foo.py",
        "--validation", "Val A",
        "--acceptance", "Acc A", "Acc B",
        "--output-file", out_file
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "SUCCESS"
    assert data["is_valid"] is True
    assert data["task_id"] == "TASK-TEST-002"

    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# Controller Execution Request" in content
    assert "TASK-TEST-002" in content
    assert "Automated Test Title" in content
    assert "Verify CLI generation" in content
    assert "- Item A" in content
    assert "src/foo.py" in content
    assert "tests/test_foo.py" in content
    assert "- Val A" in content
    assert "- Acc B" in content
    assert "APPROVED FOR IMPLEMENTATION" in content


def test_create_controller_request_missing_required_args():
    script = "src/tools/runtime/create_controller_request.py"
    # Missing required args like --objective, --scope
    cmd = [
        PYTHON_EXE, script,
        "--task-id", "TASK-TEST-003",
        "--title", "Title Alone"
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)

    assert res.returncode == 2 # argparse error exit code
