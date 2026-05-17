import os
import sys
import json
import shutil
import pytest
import tempfile
import subprocess
from datetime import datetime

from src.services.governance.execution_contract.completion_evidence_builder import CompletionEvidenceBuilder
from src.services.governance.execution_contract.execution_contract_exceptions import EvidenceValidationError
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


PYTHON_EXE = sys.executable


@pytest.fixture
def temp_env():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def run_cli_cmd(script_path: str, args: list, env: dict = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    full_env["PYTHONPATH"] = "."
    if env:
        full_env.update(env)
    cmd = [PYTHON_EXE, script_path] + args
    return subprocess.run(cmd, env=full_env, capture_output=True, text=True)


# --- Builder Tests ---

def test_builder_successful_creation(temp_env):
    out_file = os.path.join(temp_env, "out.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("content")

    builder = CompletionEvidenceBuilder(contract_id="CONT-01", worker_id="WORKER-01", root_dir=temp_env)
    builder.add_actual_outputs(["out.txt"])
    builder.set_status("SUCCESS")
    evidence = builder.build()

    assert evidence.contract_id == "CONT-01"
    assert evidence.worker_id == "WORKER-01"
    assert evidence.actual_outputs == ["out.txt"]
    assert evidence.status == "SUCCESS"
    assert evidence.evidence_hash is not None


def test_builder_missing_output_fails(temp_env):
    builder = CompletionEvidenceBuilder(contract_id="CONT-01", worker_id="WORKER-01", root_dir=temp_env)
    builder.add_actual_outputs(["non_existent.txt"])
    with pytest.raises(EvidenceValidationError, match="Missing required actual output file on disk"):
        builder.build()


def test_builder_deterministic_hash_replay(temp_env):
    out_file = os.path.join(temp_env, "out.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("content")

    dt = datetime(2026, 5, 18, 12, 0, 0)

    builder1 = CompletionEvidenceBuilder(contract_id="CONT-DET", worker_id="WORKER-DET", root_dir=temp_env)
    builder1.add_actual_outputs(["out.txt"]).set_timestamp(dt).set_status("SUCCESS")
    ev1 = builder1.build()

    builder2 = CompletionEvidenceBuilder(contract_id="CONT-DET", worker_id="WORKER-DET", root_dir=temp_env)
    builder2.add_actual_outputs(["out.txt"]).set_timestamp(dt).set_status("SUCCESS")
    ev2 = builder2.build()

    assert ev1.evidence_hash == ev2.evidence_hash


# --- Tool Trace Tests ---

def test_tool_trace_valid_array_parse(temp_env):
    trace_file = os.path.join(temp_env, "trace_array.json")
    trace_data = [
        {"tool": "serena_create_text_file", "argument": {"relative_path": "new.txt"}, "purpose": "write file"},
        {"tool": "serena_read_file", "argument": {"relative_path": "read.txt"}, "purpose": "read file"}
    ]
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f)

    builder = CompletionEvidenceBuilder(contract_id="CONT-01", worker_id="WORKER-01", root_dir=temp_env)
    builder.parse_and_add_tool_trace("trace_array.json")

    trace = builder._execution_trace
    assert len(trace) == 2
    assert trace[0]["action"] == "write"
    assert trace[0]["path"] == "new.txt"
    assert trace[1]["action"] == "read"
    assert trace[1]["path"] == "read.txt"


def test_tool_trace_valid_object_parse(temp_env):
    trace_file = os.path.join(temp_env, "trace_obj.json")
    trace_data = {
        "trace": [
            {"tool": "write_memory", "argument": {"path": "mem.json"}}
        ]
    }
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f)

    builder = CompletionEvidenceBuilder(contract_id="CONT-01", worker_id="WORKER-01", root_dir=temp_env)
    builder.parse_and_add_tool_trace("trace_obj.json")

    trace = builder._execution_trace
    assert len(trace) == 1
    assert trace[0]["action"] == "write"
    assert trace[0]["path"] == "mem.json"


def test_tool_trace_malformed_fail_closed(temp_env):
    bad_file = os.path.join(temp_env, "bad.json")
    with open(bad_file, "w", encoding="utf-8") as f:
        f.write("{invalid_json: 123")

    builder = CompletionEvidenceBuilder(contract_id="CONT-01", worker_id="WORKER-01", root_dir=temp_env)
    with pytest.raises(EvidenceValidationError, match="Malformed tool trace JSON"):
        builder.parse_and_add_tool_trace("bad.json")


# --- CLI Tests ---

def test_cli_stdout_and_file_generation(temp_env):
    out_file = os.path.join(temp_env, "actual.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("content")

    evidence_out = os.path.join(temp_env, "ev.json")
    script = "src/tools/runtime/generate_completion_evidence.py"
    args = [
        "--contract-id", "CONT-CLI",
        "--worker-id", "WORKER-CLI",
        "--actual-output", "actual.txt",
        "--output-file", evidence_out,
        "--root-dir", temp_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 0, f"CLI output: {res.stderr} {res.stdout}"
    data = json.loads(res.stdout)
    assert data["contract_id"] == "CONT-CLI"
    assert data["worker_id"] == "WORKER-CLI"
    assert data["evidence_hash"] is not None

    assert os.path.exists(evidence_out)
    with open(evidence_out, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    assert file_data["evidence_hash"] == data["evidence_hash"]


def test_cli_missing_required_args(temp_env):
    script = "src/tools/runtime/generate_completion_evidence.py"
    args = [
        "--worker-id", "WORKER-CLI",
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 2  # argparse required arg missing


def test_cli_malformed_trace_fail(temp_env):
    bad_file = os.path.join(temp_env, "bad.json")
    with open(bad_file, "w", encoding="utf-8") as f:
        f.write("{broken")

    out_file = os.path.join(temp_env, "actual.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("content")

    script = "src/tools/runtime/generate_completion_evidence.py"
    args = [
        "--contract-id", "CONT-CLI",
        "--worker-id", "WORKER-CLI",
        "--actual-output", "actual.txt",
        "--tool-trace-file", bad_file,
        "--root-dir", temp_env
    ]
    res = run_cli_cmd(script, args)
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["success"] is False
    assert "Malformed tool trace JSON" in data["error"]


# --- Integration Tests ---

def test_integration_evidence_validation_success_and_fail(temp_env):
    issuance_script = "src/tools/runtime/issue_execution_contract.py"
    generate_script = "src/tools/runtime/generate_completion_evidence.py"
    validate_script = "src/tools/runtime/validate_completion_evidence.py"

    task_id = "TASK-INT-01"
    contract_id = "CONT-INT-123"
    worker_id = "WORKER-INT"

    contracts_dir = os.path.join(temp_env, "contracts")
    os.makedirs(contracts_dir, exist_ok=True)

    allowed_file = "valid.txt"
    unauth_file = "unauth.txt"

    with open(os.path.join(temp_env, allowed_file), "w", encoding="utf-8") as f:
        f.write("ok")
    with open(os.path.join(temp_env, unauth_file), "w", encoding="utf-8") as f:
        f.write("bad")

    # Issue contract allowing only valid.txt
    issue_args = [
        "--task-id", task_id,
        "--actor-id", worker_id,
        "--allow-write", allowed_file,
        "--expected-output", allowed_file,
        "--contract-id", contract_id,
        "--contracts-dir", contracts_dir
    ]
    res_iss = run_cli_cmd(issuance_script, issue_args)
    assert res_iss.returncode == 0

    # 1. Generate valid trace and valid evidence
    valid_trace = os.path.join(temp_env, "valid_trace.json")
    with open(valid_trace, "w", encoding="utf-8") as f:
        json.dump([{"tool": "serena_create_text_file", "argument": {"relative_path": allowed_file}}], f)

    valid_evidence = os.path.join(temp_env, "valid_ev.json")
    gen_args = [
        "--contract-id", contract_id,
        "--worker-id", worker_id,
        "--actual-output", allowed_file,
        "--tool-trace-file", "valid_trace.json",
        "--output-file", valid_evidence,
        "--root-dir", temp_env
    ]
    res_gen = run_cli_cmd(generate_script, gen_args)
    assert res_gen.returncode == 0

    # Validate valid evidence
    val_args = [
        "--task-id", task_id,
        "--evidence-file", valid_evidence,
        "--contracts-dir", contracts_dir
    ]
    res_val = run_cli_cmd(validate_script, val_args)
    assert res_val.returncode == 0, f"Validation output: {res_val.stderr} {res_val.stdout}"
    val_data = json.loads(res_val.stdout)
    assert val_data["is_valid"] is True

    # 2. Generate unauthorized trace and evidence
    unauth_trace = os.path.join(temp_env, "unauth_trace.json")
    with open(unauth_trace, "w", encoding="utf-8") as f:
        json.dump([
            {"tool": "serena_create_text_file", "argument": {"relative_path": allowed_file}},
            {"tool": "serena_create_text_file", "argument": {"relative_path": unauth_file}}
        ], f)

    unauth_evidence = os.path.join(temp_env, "unauth_ev.json")
    gen_unauth_args = [
        "--contract-id", contract_id,
        "--worker-id", worker_id,
        "--actual-output", allowed_file,
        "--tool-trace-file", "unauth_trace.json",
        "--output-file", unauth_evidence,
        "--root-dir", temp_env
    ]
    res_gen_unauth = run_cli_cmd(generate_script, gen_unauth_args)
    assert res_gen_unauth.returncode == 0

    # Validate unauthorized evidence (should fail)
    val_unauth_args = [
        "--task-id", task_id,
        "--evidence-file", unauth_evidence,
        "--contracts-dir", contracts_dir
    ]
    res_val_unauth = run_cli_cmd(validate_script, val_unauth_args)
    assert res_val_unauth.returncode == 1
    val_unauth_data = json.loads(res_val_unauth.stdout)
    assert val_unauth_data["is_valid"] is False
    assert "Unauthorized write detected in trace" in val_unauth_data["reason"]
