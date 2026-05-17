import os
import json
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


def test_standardize_raw_list_to_canonical():
    raw_list = [{"tool": "read_file", "argument": {"path": "test.txt"}}]
    std = ArtifactBundleValidator.standardize_tool_trace(raw_list, task_id="TASK-TEST")
    
    assert std["schema_version"] == "runtime-tool-trace-v1"
    assert std["task_id"] == "TASK-TEST"
    assert len(std["events"]) == 1
    assert std["events"][0]["tool"] == "read_file"


def test_standardize_already_canonical_returns_as_is():
    canon = {
        "schema_version": "runtime-tool-trace-v1",
        "task_id": "TASK-CANON",
        "worker_id": "WORKER-01",
        "generated_at": "2026-05-18T12:00:00",
        "events": [{"tool": "list_dir", "argument": {}}]
    }
    std = ArtifactBundleValidator.standardize_tool_trace(canon, task_id="TASK-CANON")
    assert std == canon


def test_validate_tool_trace_schema_valid(temp_env):
    trace_file = os.path.join(temp_env, "TASK-VALID-tool-trace.json")
    canon = {
        "schema_version": "runtime-tool-trace-v1",
        "task_id": "TASK-VALID",
        "worker_id": "WORKER-01",
        "generated_at": "2026-05-18T12:00:00",
        "events": [{"tool": "list_dir", "argument": {}}]
    }
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(canon, f)

    validator = ArtifactBundleValidator(task_id="TASK-VALID", root_dir=temp_env)
    events = validator.validate_tool_trace_schema("TASK-VALID-tool-trace.json")
    assert len(events) == 1


def test_validate_tool_trace_schema_mismatch_fails(temp_env):
    trace_file = os.path.join(temp_env, "TASK-BAD-tool-trace.json")
    canon = {
        "schema_version": "invalid-version",
        "task_id": "TASK-BAD",
        "events": []
    }
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(canon, f)

    validator = ArtifactBundleValidator(task_id="TASK-BAD", root_dir=temp_env)
    with pytest.raises(EvidenceValidationError, match="Invalid tool trace schema_version"):
        validator.validate_tool_trace_schema("TASK-BAD-tool-trace.json")
