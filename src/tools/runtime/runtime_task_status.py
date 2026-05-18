import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.tools.runtime.inspect_runtime_contract import inspect_contract_lifecycle


def get_all_runtime_tasks(contracts_dir: str = "ai_runtime/contracts", reports_dir: str = "ai_runtime/reports", state_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    tasks = []
    if not os.path.exists(contracts_dir):
        return tasks

    for filename in sorted(os.listdir(contracts_dir)):
        if filename.endswith(".json"):
            task_id = filename[:-5]
            info = inspect_contract_lifecycle(task_id, contracts_dir=contracts_dir, reports_dir=reports_dir)
            if state_filter:
                if info.get("state", "").upper() == state_filter.upper():
                    tasks.append(info)
            else:
                tasks.append(info)

    return tasks


def format_status_table(tasks: List[Dict[str, Any]]) -> str:
    if not tasks:
        return "No runtime tasks found matching the criteria."

    header = f"{'Task ID':<12} | {'Contract ID':<14} | {'Actor ID':<10} | {'State':<22} | {'Reports (Tr/Tc/Rp/Ev)':<22}"
    separator = "-" * len(header)
    lines = [header, separator]

    for t in tasks:
        task_id = t.get("task_id", "UNKNOWN")
        contract_id = t.get("contract_id") or "NONE"
        state = t.get("state", "UNKNOWN")

        contract_dict = t.get("contract") or {}
        actor_id = contract_dict.get("actor_id", "UNKNOWN")

        reports = t.get("reports", {})
        tr = "Y" if reports.get("execution_transcript") else "."
        tc = "Y" if reports.get("tool_trace") else "."
        rp = "Y" if reports.get("worker_report") else "."
        ev = "Y" if reports.get("evidence_json") else "."
        reports_summary = f"{tr}  {tc}  {rp}  {ev}"

        lines.append(f"{task_id:<12} | {contract_id:<14} | {actor_id:<10} | {state:<22} | {reports_summary:<22}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Deterministic Runtime Task Status CLI.")
    parser.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")
    parser.add_argument("--state", default=None, help="Optional state filter (e.g. ACTIVE, EXPIRED, VALIDATED_COMPLETION).")
    parser.add_argument("--format", default="json", choices=["json", "table"], help="Output format.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

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

    sys.exit(0)


if __name__ == "__main__":
    main()
