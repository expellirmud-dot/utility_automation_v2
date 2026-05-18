import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.tools.runtime.runtime_task_status import get_all_runtime_tasks, format_status_table


PYTHON_EXE = sys.executable


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        # Fallback to clip on Windows
        if sys.platform == "win32":
            try:
                proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return True
            except Exception:
                pass
    return False


def cmd_create(args: argparse.Namespace, serializer: ExecutionContractSerializer, interactive: bool = False) -> bool:
    req_file = args.output_file or os.path.join(args.inbox_dir, f"{args.task_id}-controller-request.md")
    cmd = [
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
        "--output-file", req_file
    ]
    if args.next_task:
        cmd.extend(["--next-task", args.next_task])

    res = run_command(cmd)
    if res.returncode != 0:
        print(res.stderr or res.stdout)
        if not interactive:
            sys.exit(1)
        return False

    print(res.stdout)
    if not interactive:
        sys.exit(0)
    return True


def cmd_start(args: argparse.Namespace, serializer: ExecutionContractSerializer, interactive: bool = False) -> bool:
    req_file = args.request_file or os.path.join(args.inbox_dir, f"{args.task_id}-controller-request.md")
    cmd = [
        PYTHON_EXE, "src/tools/runtime/start_runtime_task.py",
        "--task-id", args.task_id,
        "--actor-id", args.actor_id,
        "--request-file", req_file,
        "--inbox-dir", args.inbox_dir,
        "--contracts-dir", args.contracts_dir,
        "--duration-mins", str(args.duration_mins)
    ]
    if args.allow_read:
        cmd.extend(["--allow-read", *args.allow_read])
    if args.allow_write:
        cmd.extend(["--allow-write", *args.allow_write])
    if args.expected_output:
        cmd.extend(["--expected-output", *args.expected_output])
    if args.allow_command:
        cmd.extend(["--allow-command", *args.allow_command])
    if args.forbid_pattern:
        cmd.extend(["--forbid-pattern", *args.forbid_pattern])

    res = run_command(cmd)
    if res.returncode != 0:
        print(res.stderr or res.stdout)
        if not interactive:
            sys.exit(1)
        return False

    try:
        out_data = json.loads(res.stdout)
        contract_id = out_data.get("contract_id", "UNKNOWN")
    except Exception:
        print(f"Failed to parse startup output:\n{res.stdout}")
        if not interactive:
            sys.exit(1)
        return False

    # Generate Worker Handoff Prompt
    cwd = os.path.abspath(".")
    prompt = (
        f"Serena active.\n"
        f"New controller request is available.\n"
        f"{args.task_id}\n"
        f"Workspace:\n"
        f"{cwd}\n\n"
        f"READ-FIRST mandatory.\n"
        f"Inspect actual repository state first.\n"
        f"Treat controller request as READ-ONLY.\n"
        f"Return controller review package only.\n"
        f"No commit.\n"
        f"No push."
    )

    copied = copy_to_clipboard(prompt)

    out_data["worker_handoff_prompt"] = prompt
    out_data["prompt_copied_to_clipboard"] = copied

    banner = (
        f"======================================================================\n"
        f"RUNTIME TASK {args.task_id} SUCCESSFULLY INITIATED\n"
        f"Contract ID: {contract_id}\n"
        f"Worker ID: {args.actor_id}\n"
        f"Clipboard Status: {'COPIED TO CLIPBOARD' if copied else 'COPY FAILED'}\n"
        f"======================================================================"
    )

    if args.format == "text":
        print(banner)
        print("\nWorker Handoff Prompt:\n")
        print(prompt)
    else:
        print(serializer.serialize(out_data))

    if not interactive:
        sys.exit(0)
    return True


def cmd_finish(args: argparse.Namespace, serializer: ExecutionContractSerializer, interactive: bool = False) -> bool:
    cmd = [
        PYTHON_EXE, "src/tools/runtime/finish_runtime_task.py",
        "--task-id", args.task_id,
        "--worker-id", args.worker_id,
        "--actual-output", *args.actual_output,
        "--reports-dir", args.reports_dir,
        "--contracts-dir", args.contracts_dir,
        "--root-dir", args.root_dir
    ]
    res = run_command(cmd)
    if res.returncode != 0:
        print(res.stderr or res.stdout)
        if not interactive:
            sys.exit(1)
        return False

    try:
        out_data = json.loads(res.stdout)
    except Exception:
        print(f"Failed to parse finish output:\n{res.stdout}")
        if not interactive:
            sys.exit(1)
        return False

    if args.format == "text":
        pkg = out_data.get("controller_commit_package", {})
        print(f"======================================================================")
        print(f"RUNTIME TASK {args.task_id} COMPLETION VERIFICATION: {out_data.get('lifecycle_state')}")
        print(f"Contract ID: {out_data.get('contract_id')}")
        print(f"Evidence Hash: {out_data.get('evidence_hash')}")
        print(f"======================================================================")
        print(f"\nSummary:\n{pkg.get('summary')}\n")
        print(f"Instructions:\n{pkg.get('instructions')}\n")
    else:
        print(serializer.serialize(out_data))

    if not interactive:
        sys.exit(0)
    return True


def cmd_status(args: argparse.Namespace, serializer: ExecutionContractSerializer, interactive: bool = False) -> bool:
    tasks = get_all_runtime_tasks(contracts_dir=args.contracts_dir, reports_dir=args.reports_dir, state_filter=args.state)
    if args.format == "table":
        print(format_status_table(tasks))
    else:
        out = {
            "timestamp": datetime.now().isoformat(),
            "count": len(tasks),
            "state_filter": args.state,
            "tasks": tasks
        }
        print(serializer.serialize(out))

    if not interactive:
        sys.exit(0)
    return True


def cmd_inspect(args: argparse.Namespace, serializer: ExecutionContractSerializer, interactive: bool = False) -> bool:
    cmd = [
        PYTHON_EXE, "src/tools/runtime/inspect_runtime_contract.py",
        "--task-id", args.task_id,
        "--contracts-dir", args.contracts_dir,
        "--reports-dir", args.reports_dir
    ]
    res = run_command(cmd)
    if res.returncode != 0:
        print(res.stderr or res.stdout)
        if not interactive:
            sys.exit(1)
        return False

    print(res.stdout)
    if not interactive:
        sys.exit(0)
    return True


def input_list(prompt: str) -> List[str]:
    raw = input(prompt).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def interactive_console_loop(serializer: ExecutionContractSerializer) -> None:
    banner = """
======================================================================
             DETERMINISTIC RUNTIME CONTROL CONSOLE (UX)
======================================================================
1. Start Runtime Task (Assign Worker & Copy Prompt)
2. Finish Runtime Task (Verify Post-Task Validation)
3. Inspect Active Task Status Overview
4. Inspect Specific Execution Contract
0. Exit Console
======================================================================"""

    while True:
        print(banner)
        choice = input("Select an option [0-4]: ").strip()
        if choice == "0":
            print("\nExiting Runtime Control Console. Goodbye!\n")
            break
        elif choice == "1":
            print("\n--- Start Runtime Task ---")
            task_id = input("Task ID (e.g. TASK-100): ").strip()
            if not task_id:
                print("Task ID cannot be empty.")
                continue
            actor_id = input("Worker Actor ID [WORKER-01]: ").strip() or "WORKER-01"
            allow_read = input_list("Allowed Read Paths (comma-separated) [src/,tests/,ai_runtime/]: ") or ["src/", "tests/", "ai_runtime/"]
            allow_write = input_list("Allowed Write Paths (comma-separated) [src/,tests/,ai_runtime/]: ") or ["src/", "tests/", "ai_runtime/"]
            expected_output = input_list("Expected Output Files (comma-separated): ")
            duration_mins = input("Duration in minutes [60]: ").strip()
            duration_mins = int(duration_mins) if duration_mins.isdigit() else 60

            ns = argparse.Namespace(
                task_id=task_id, actor_id=actor_id, request_file=None,
                allow_read=allow_read, allow_write=allow_write, expected_output=expected_output,
                allow_command=None, forbid_pattern=None, duration_mins=duration_mins,
                inbox_dir="ai_runtime/inbox", contracts_dir="ai_runtime/contracts", format="text"
            )
            print()
            cmd_start(ns, serializer, interactive=True)

        elif choice == "2":
            print("\n--- Finish Runtime Task ---")
            task_id = input("Task ID (e.g. TASK-100): ").strip()
            if not task_id:
                print("Task ID cannot be empty.")
                continue
            worker_id = input("Worker Actor ID [WORKER-01]: ").strip() or "WORKER-01"
            actual_output = input_list("Actual Output Files (comma-separated): ")
            if not actual_output:
                print("At least one actual output file must be specified.")
                continue

            ns = argparse.Namespace(
                task_id=task_id, worker_id=worker_id, actual_output=actual_output,
                reports_dir="ai_runtime/reports", contracts_dir="ai_runtime/contracts", root_dir=".", format="text"
            )
            print()
            cmd_finish(ns, serializer, interactive=True)

        elif choice == "3":
            print("\n--- Inspect Active Task Status Overview ---")
            state_filter = input("State Filter [press Enter for all, or ACTIVE, EXPIRED, VALIDATED_COMPLETION]: ").strip() or None
            ns = argparse.Namespace(
                contracts_dir="ai_runtime/contracts", reports_dir="ai_runtime/reports",
                state=state_filter, format="table"
            )
            print()
            cmd_status(ns, serializer, interactive=True)

        elif choice == "4":
            print("\n--- Inspect Specific Execution Contract ---")
            task_id = input("Task ID (e.g. TASK-100): ").strip()
            if not task_id:
                print("Task ID cannot be empty.")
                continue
            ns = argparse.Namespace(
                task_id=task_id, contracts_dir="ai_runtime/contracts", reports_dir="ai_runtime/reports"
            )
            print()
            cmd_inspect(ns, serializer, interactive=True)

        else:
            print("Invalid option. Please enter a number between 0 and 4.")


def main():
    serializer = ExecutionContractSerializer()

    # If no subcommands/arguments provided, enter interactive loop UX
    if len(sys.argv) == 1:
        try:
            interactive_console_loop(serializer)
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting Runtime Control Console. Goodbye!\n")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Deterministic Runtime Control Console CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Console subcommand.")

    # Subcommand: create
    parser_create = subparsers.add_parser("create", help="Create a controller request.")
    parser_create.add_argument("--task-id", required=True, help="Task identifier.")
    parser_create.add_argument("--title", required=True, help="Task title.")
    parser_create.add_argument("--objective", required=True, help="Primary objective.")
    parser_create.add_argument("--rationale", required=True, help="Architectural rationale.")
    parser_create.add_argument("--scope", nargs="+", required=True, help="In-scope items.")
    parser_create.add_argument("--candidate-modules", nargs="+", required=True, help="Candidate module paths.")
    parser_create.add_argument("--tests", nargs="+", required=True, help="Test file paths.")
    parser_create.add_argument("--validation", nargs="+", required=True, help="Required validation items.")
    parser_create.add_argument("--acceptance", nargs="+", required=True, help="Acceptance criteria items.")
    parser_create.add_argument("--next-task", default=None, help="Next task reference.")
    parser_create.add_argument("--output-file", default=None, help="Output file path.")
    parser_create.add_argument("--inbox-dir", default="ai_runtime/inbox", help="Inbox directory.")

    # Subcommand: start
    parser_start = subparsers.add_parser("start", help="Start a runtime task.")
    parser_start.add_argument("--task-id", required=True, help="Task identifier.")
    parser_start.add_argument("--actor-id", required=True, help="Assigned worker actor ID.")
    parser_start.add_argument("--request-file", default=None, help="Path to controller request md file.")
    parser_start.add_argument("--allow-read", nargs="*", default=[], help="Allowed read paths.")
    parser_start.add_argument("--allow-write", nargs="*", default=[], help="Allowed write paths.")
    parser_start.add_argument("--expected-output", nargs="*", default=[], help="Expected output file paths.")
    parser_start.add_argument("--allow-command", nargs="*", default=None, help="Allowed shell commands.")
    parser_start.add_argument("--forbid-pattern", nargs="*", default=None, help="Forbidden action patterns.")
    parser_start.add_argument("--duration-mins", type=int, default=60, help="Contract duration in minutes.")
    parser_start.add_argument("--inbox-dir", default="ai_runtime/inbox", help="Inbox directory.")
    parser_start.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser_start.add_argument("--format", default="text", choices=["text", "json"], help="Output format.")

    # Subcommand: finish
    parser_finish = subparsers.add_parser("finish", help="Finish post-task verification.")
    parser_finish.add_argument("--task-id", required=True, help="Task identifier.")
    parser_finish.add_argument("--worker-id", required=True, help="Worker actor ID.")
    parser_finish.add_argument("--actual-output", nargs="+", required=True, help="List of actual output file paths.")
    parser_finish.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")
    parser_finish.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser_finish.add_argument("--root-dir", default=".", help="Root directory.")
    parser_finish.add_argument("--format", default="text", choices=["text", "json"], help="Output format.")

    # Subcommand: status
    parser_status = subparsers.add_parser("status", help="Inspect overall runtime task status.")
    parser_status.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser_status.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")
    parser_status.add_argument("--state", default=None, help="Optional state filter.")
    parser_status.add_argument("--format", default="table", choices=["table", "json"], help="Output format.")

    # Subcommand: inspect
    parser_inspect = subparsers.add_parser("inspect", help="Inspect a specific runtime contract.")
    parser_inspect.add_argument("--task-id", required=True, help="Task identifier.")
    parser_inspect.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser_inspect.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args, serializer)
    elif args.command == "start":
        cmd_start(args, serializer)
    elif args.command == "finish":
        cmd_finish(args, serializer)
    elif args.command == "status":
        cmd_status(args, serializer)
    elif args.command == "inspect":
        cmd_inspect(args, serializer)


if __name__ == "__main__":
    main()
