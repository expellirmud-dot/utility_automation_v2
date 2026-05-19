import os
import re
import json
from pathlib import Path
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.services.governance.execution_contract.execution_contract_validator import ExecutionContractValidator

def check_runtime_task_governance(repo_root: Path) -> tuple[bool, str]:
    """
    Validates consistency and completeness of runtime task governance artifacts.
    Exempts legacy tasks (<= TASK-096).
    """
    contracts_dir = repo_root / "ai_runtime" / "contracts"
    inbox_dir = repo_root / "ai_runtime" / "inbox"
    reports_dir = repo_root / "ai_runtime" / "reports"

    if not contracts_dir.exists():
        return True, "No contracts directory exists."

    serializer = ExecutionContractSerializer()
    validator = ExecutionContractValidator()

    for item in sorted(contracts_dir.iterdir()):
        if item.is_file() and item.suffix == ".json":
            task_id = item.stem
            
            # Extract task number
            num_match = re.search(r'\d+', task_id)
            if not num_match:
                continue
            task_num = int(num_match.group())

            # Skip legacy tasks <= 96
            if task_num <= 96:
                continue

            # 1. Matching inbox/controller request required
            inbox_path = inbox_dir / f"{task_id}-controller-request.md"
            if not inbox_path.exists():
                try:
                    rel_path = inbox_path.relative_to(repo_root)
                except ValueError:
                    rel_path = inbox_path
                return False, f"Task {task_id} contract exists but is missing matching controller request at {rel_path}"

            # 2. Check completion bundle if evidence exists
            evidence_path = reports_dir / f"{task_id}-evidence.json"
            if evidence_path.exists():
                required_reports = {
                    "execution transcript": reports_dir / f"{task_id}-execution-transcript.md",
                    "tool trace": reports_dir / f"{task_id}-tool-trace.json",
                    "worker report": reports_dir / f"{task_id}-worker-report.md",
                    "validation output": reports_dir / f"{task_id}-validation-output.txt",
                    "runtime manifest": reports_dir / f"{task_id}-runtime-manifest.json"
                }

                for name, path in required_reports.items():
                    if not path.exists():
                        try:
                            rel_path = path.relative_to(repo_root)
                        except ValueError:
                            rel_path = path
                        return False, f"Completed task {task_id} is missing required {name} at {rel_path}"

                # Validate contract-evidence consistency
                try:
                    contract_data = json.loads(item.read_text(encoding="utf-8"))
                    evidence_data = json.loads(evidence_path.read_text(encoding="utf-8"))

                    contract = serializer.deserialize_contract(contract_data)
                    evidence = serializer.deserialize_evidence(evidence_data)

                    validator.validate_completion(contract, evidence)
                except Exception as exc:
                    return False, f"Governance completion validation failed for {task_id}: {str(exc)}"

    return True, "All governed runtime tasks are consistent with governance rules."
