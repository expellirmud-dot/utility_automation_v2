import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


PYTHON_EXE = sys.executable


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def finish_runtime_task(args: argparse.Namespace) -> Dict[str, Any]:
    serializer = ExecutionContractSerializer()

    contract_path = os.path.join(args.contracts_dir, f"{args.task_id}.json")
    if not os.path.exists(contract_path):
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "locate_contract",
            "error": f"Execution contract not found at {contract_path}"
        }

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract_data = json.load(f)
        contract = serializer.deserialize_contract(contract_data)
        contract_id = contract.contract_id
    except Exception as e:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "parse_contract",
            "error": f"Failed to parse contract JSON: {str(e)}"
        }

    # Step 3.2: Validate Runtime Artifact Bundle
    bundle_cmd = [
        PYTHON_EXE, "src/tools/runtime/validate_runtime_artifact_bundle.py",
        "--task-id", args.task_id,
        "--worker-id", args.worker_id,
        "--reports-dir", args.reports_dir,
        "--generate-manifest",
        "--root-dir", args.root_dir
    ]
    res = run_command(bundle_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "validate_runtime_artifact_bundle",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    # Step 3.5: Generate Completion Evidence Manifest
    evidence_file = os.path.join(args.reports_dir, f"{args.task_id}-evidence.json")
    gen_cmd = [
        PYTHON_EXE, "src/tools/runtime/generate_completion_evidence.py",
        "--contract-id", contract_id,
        "--worker-id", args.worker_id,
        "--tool-trace-file", os.path.join(args.reports_dir, f"{args.task_id}-tool-trace.json"),
        "--execution-transcript", os.path.join(args.reports_dir, f"{args.task_id}-execution-transcript.md"),
        "--worker-report", os.path.join(args.reports_dir, f"{args.task_id}-worker-report.md"),
        "--actual-output", *args.actual_output,
        "--output-file", evidence_file,
        "--root-dir", args.root_dir,
        "--status", "SUCCESS"
    ]
    res = run_command(gen_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "generate_completion_evidence",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    try:
        evidence_data = json.loads(res.stdout)
        evidence_hash = evidence_data.get("evidence_hash")
    except Exception as e:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "parse_evidence_output",
            "error": f"Failed to parse evidence output JSON: {str(e)}",
            "raw_stdout": res.stdout
        }

    # Step 4.0: Validate Completion Evidence
    val_cmd = [
        PYTHON_EXE, "src/tools/runtime/validate_completion_evidence.py",
        "--task-id", args.task_id,
        "--evidence-file", evidence_file,
        "--contracts-dir", args.contracts_dir
    ]
    res = run_command(val_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "validate_completion_evidence",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    # Step 2.5 Lifecycle Inspection
    inspect_cmd = [
        PYTHON_EXE, "src/tools/runtime/inspect_runtime_contract.py",
        "--task-id", args.task_id,
        "--contracts-dir", args.contracts_dir,
        "--reports-dir", args.reports_dir
    ]
    res = run_command(inspect_cmd)
    lifecycle_state = "UNKNOWN"
    if res.returncode == 0:
        try:
            inspect_data = json.loads(res.stdout)
            lifecycle_state = inspect_data.get("state", "UNKNOWN")
        except Exception:
            pass

    commit_package = {
        "summary": f"Task {args.task_id} completed and verified against contract {contract_id}.",
        "actual_outputs": args.actual_output,
        "evidence_file": evidence_file,
        "manifest_file": os.path.join(args.reports_dir, f"{args.task_id}-runtime-manifest.json"),
        "verification_status": "VALIDATED_COMPLETION" if lifecycle_state == "VALIDATED_COMPLETION" else "PENDING",
        "instructions": (
            f"Review package ready for controller approval. "
            f"Run 'git status' and 'git diff' to inspect changes. "
            f"Do not commit or push without explicit controller authorization."
        )
    }

    return {
        "status": "SUCCESS",
        "task_id": args.task_id,
        "contract_id": contract_id,
        "worker_id": args.worker_id,
        "evidence_hash": evidence_hash,
        "lifecycle_state": lifecycle_state,
        "timestamp": datetime.now().isoformat(),
        "controller_commit_package": commit_package
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Runtime Post-Task Automation Harness CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. TASK-084).")
    parser.add_argument("--worker-id", required=True, help="Assigned worker actor ID.")
    parser.add_argument("--actual-output", nargs="+", required=True, help="List of actual output file paths.")
    parser.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")
    parser.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser.add_argument("--root-dir", default=".", help="Root directory for absolute path resolution.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    result = finish_runtime_task(args)
    if result["status"] == "FAILED":
        print(serializer.serialize(result))
        sys.exit(1)

    print(serializer.serialize(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
