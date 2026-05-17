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


def start_runtime_task(args: argparse.Namespace) -> Dict[str, Any]:
    serializer = ExecutionContractSerializer()

    request_file = args.request_file
    if not request_file or not os.path.exists(request_file):
        # Need to generate request file
        if not args.title or not args.objective or not args.rationale or not args.scope or not args.candidate_modules or not args.tests or not args.validation or not args.acceptance:
            return {
                "status": "FAILED",
                "task_id": args.task_id,
                "step": "request_generation",
                "error": "Request file not found and missing required arguments (--title, --objective, etc.) to generate one."
            }
        
        request_file = args.request_file or os.path.join(args.inbox_dir, f"{args.task_id}-controller-request.md")
        gen_cmd = [
            PYTHON_EXE, "src/tools/runtime/create_controller_request.py",
            "--task-id", args.task_id,
            "--title", args.title,
            "--objective", args.objective,
            "--rationale", args.rationale,
            "--scope", *args.scope,
            "--candidate-modules", *args.candidate_modules,
            "--tests", *args.tests,
            "--validation", *args.validation,
            "--acceptance", *args.acceptance,
            "--output-file", request_file
        ]
        if args.next_task:
            gen_cmd.extend(["--next-task", args.next_task])

        res = run_command(gen_cmd)
        if res.returncode != 0:
            return {
                "status": "FAILED",
                "task_id": args.task_id,
                "step": "create_controller_request",
                "error": res.stderr.strip() or res.stdout.strip(),
                "exit_code": res.returncode
            }

    # Step 0.5: Validate Controller Request
    val_cmd = [
        PYTHON_EXE, "src/tools/runtime/validate_controller_request.py",
        "--request-file", request_file
    ]
    res = run_command(val_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "validate_controller_request",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    # Step 1: Issue Execution Contract
    if not args.allow_read and not args.allow_write:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "issue_execution_contract",
            "error": "Contract scope must allow at least one read or write path."
        }

    if not args.expected_output:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "issue_execution_contract",
            "error": "At least one expected output path must be specified."
        }

    issue_cmd = [
        PYTHON_EXE, "src/tools/runtime/issue_execution_contract.py",
        "--task-id", args.task_id,
        "--actor-id", args.actor_id,
        "--allow-read", *args.allow_read,
        "--allow-write", *args.allow_write,
        "--expected-output", *args.expected_output,
        "--contracts-dir", args.contracts_dir,
        "--duration-mins", str(args.duration_mins)
    ]
    if args.allow_command:
        issue_cmd.extend(["--allow-command", *args.allow_command])
    if args.forbid_pattern:
        issue_cmd.extend(["--forbid-pattern", *args.forbid_pattern])

    res = run_command(issue_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "issue_execution_contract",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    try:
        contract_data = json.loads(res.stdout)
        contract_id = contract_data["contract_id"]
    except Exception as e:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "issue_execution_contract_output",
            "error": f"Failed to parse contract output JSON: {str(e)}",
            "raw_stdout": res.stdout
        }

    # Step 2: Check Execution Readiness
    readiness_cmd = [
        PYTHON_EXE, "src/tools/runtime/check_execution_readiness.py",
        "--task-id", args.task_id,
        "--actor-id", args.actor_id,
        "--contracts-dir", args.contracts_dir
    ]
    res = run_command(readiness_cmd)
    if res.returncode != 0:
        return {
            "status": "FAILED",
            "task_id": args.task_id,
            "step": "check_execution_readiness",
            "error": res.stderr.strip() or res.stdout.strip(),
            "exit_code": res.returncode
        }

    return {
        "status": "SUCCESS",
        "task_id": args.task_id,
        "contract_id": contract_id,
        "actor_id": args.actor_id,
        "request_file": request_file,
        "readiness_verified": True,
        "timestamp": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Controller Runtime Automation Harness CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. TASK-081).")
    parser.add_argument("--actor-id", required=True, help="Assigned worker actor ID.")
    parser.add_argument("--request-file", default=None, help="Path to existing controller request md file.")
    
    # Request generation optional args
    parser.add_argument("--title", default=None, help="Task title.")
    parser.add_argument("--objective", default=None, help="Primary objective.")
    parser.add_argument("--rationale", default=None, help="Architectural rationale.")
    parser.add_argument("--scope", nargs="+", default=[], help="In-scope items.")
    parser.add_argument("--candidate-modules", nargs="+", default=[], help="Candidate module paths.")
    parser.add_argument("--tests", nargs="+", default=[], help="Test file paths.")
    parser.add_argument("--validation", nargs="+", default=[], help="Required validation items.")
    parser.add_argument("--acceptance", nargs="+", default=[], help="Acceptance criteria items.")
    parser.add_argument("--next-task", default=None, help="Next task reference.")

    # Contract issuance args
    parser.add_argument("--allow-read", nargs="*", default=[], help="Allowed read paths.")
    parser.add_argument("--allow-write", nargs="*", default=[], help="Allowed write paths.")
    parser.add_argument("--expected-output", nargs="*", default=[], help="Expected output file paths.")
    parser.add_argument("--allow-command", nargs="*", default=None, help="Allowed shell commands.")
    parser.add_argument("--forbid-pattern", nargs="*", default=None, help="Forbidden action patterns.")
    parser.add_argument("--duration-mins", type=int, default=60, help="Contract duration in minutes.")

    # Directory overrides
    parser.add_argument("--inbox-dir", default="ai_runtime/inbox", help="Inbox directory.")
    parser.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    result = start_runtime_task(args)
    if result["status"] == "FAILED":
        print(serializer.serialize(result))
        sys.exit(1)

    print(serializer.serialize(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
