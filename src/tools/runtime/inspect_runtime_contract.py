import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, Any, Optional

from src.services.governance.execution_contract.execution_contract_validator import ExecutionContractValidator
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def inspect_contract_lifecycle(
    task_id: str,
    contracts_dir: str = "ai_runtime/contracts",
    reports_dir: str = "ai_runtime/reports",
    reference_time: Optional[datetime] = None,
    include_contents: bool = False
) -> Dict[str, Any]:
    now = reference_time or datetime.now()
    serializer = ExecutionContractSerializer()

    contract_path = os.path.join(contracts_dir, f"{task_id}.json")
    evidence_path = os.path.join(reports_dir, f"{task_id}-evidence.json")
    transcript_path = os.path.join(reports_dir, f"{task_id}-execution-transcript.md")
    trace_path = os.path.join(reports_dir, f"{task_id}-tool-trace.json")
    report_path = os.path.join(reports_dir, f"{task_id}-worker-report.md")
    validation_output_path = os.path.join(reports_dir, f"{task_id}-validation-output.txt")
    runtime_manifest_path = os.path.join(reports_dir, f"{task_id}-runtime-manifest.json")
    certification_artifact_path = os.path.join("output", "certification", "certification_artifact.json")

    reports_status = {
        "evidence_json": os.path.exists(evidence_path),
        "execution_transcript": os.path.exists(transcript_path),
        "tool_trace": os.path.exists(trace_path),
        "worker_report": os.path.exists(report_path),
        "validation_output": os.path.exists(validation_output_path),
        "runtime_manifest": os.path.exists(runtime_manifest_path),
        "certification_artifact": os.path.exists(certification_artifact_path)
    }

    artifact_contents = {}
    if include_contents:
        for key, path in [
            ("evidence_json", evidence_path),
            ("execution_transcript", transcript_path),
            ("tool_trace", trace_path),
            ("worker_report", report_path),
            ("validation_output", validation_output_path),
            ("runtime_manifest", runtime_manifest_path),
            ("certification_artifact", certification_artifact_path)
        ]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        artifact_contents[key] = f.read()
                except Exception:
                    artifact_contents[key] = None

    if not os.path.exists(contract_path):
        return {
            "task_id": task_id,
            "contract_id": None,
            "state": "ISSUANCE_PENDING",
            "contract": None,
            "evidence_found": reports_status["evidence_json"],
            "reports": reports_status,
            "artifact_contents": artifact_contents if include_contents else None,
            "summary": f"No active contract found for {task_id}. Issuance is pending."
        }

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract_data = json.load(f)
        contract = serializer.deserialize_contract(contract_data)
        contract_dict = serializer.to_dict(contract)
    except Exception as e:
        return {
            "task_id": task_id,
            "contract_id": None,
            "state": "CORRUPT_CONTRACT",
            "contract": None,
            "evidence_found": reports_status["evidence_json"],
            "reports": reports_status,
            "summary": f"Contract file exists but failed to deserialize: {str(e)}"
        }

    is_expired = now > contract.expires_at

    if not reports_status["evidence_json"]:
        state = "EXPIRED" if is_expired else "ACTIVE"
        summary = f"Contract {contract.contract_id} is {state.lower()}."
        return {
            "task_id": task_id,
            "contract_id": contract.contract_id,
            "state": state,
            "contract": contract_dict,
            "evidence_found": False,
            "evidence": None,
            "reports": reports_status,
            "artifact_contents": artifact_contents if include_contents else None,
            "summary": summary
        }

    try:
        with open(evidence_path, "r", encoding="utf-8") as f:
            evidence_data = json.load(f)
        evidence = serializer.deserialize_evidence(evidence_data)
        evidence_dict = serializer.to_dict(evidence)
    except Exception as e:
        return {
            "task_id": task_id,
            "contract_id": contract.contract_id,
            "state": "CORRUPT_EVIDENCE",
            "contract": contract_dict,
            "evidence_found": True,
            "evidence": None,
            "reports": reports_status,
            "artifact_contents": artifact_contents if include_contents else None,
            "summary": f"Evidence file exists but failed to deserialize: {str(e)}"
        }

    validator = ExecutionContractValidator()
    try:
        validator.validate_completion(contract, evidence)
        state = "VALIDATED_COMPLETION"
        summary = f"Contract {contract.contract_id} completed successfully and evidence is fully validated."
    except Exception as e:
        state = "EVIDENCE_VALIDATION_FAILED"
        summary = f"Completion evidence failed validation against contract: {str(e)}"

    return {
        "task_id": task_id,
        "contract_id": contract.contract_id,
        "state": state,
        "contract": contract_dict,
        "evidence_found": True,
        "evidence": evidence_dict,
        "reports": reports_status,
        "artifact_contents": artifact_contents if include_contents else None,
        "summary": summary
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic Runtime Contract Lifecycle Inspector CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. TASK-080).")
    parser.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts directory.")
    parser.add_argument("--reports-dir", default="ai_runtime/reports", help="Reports directory.")
    parser.add_argument("--reference-time", default=None, help="Optional reference time in ISO format.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    ref_time = None
    if args.reference_time:
        try:
            ref_time = datetime.fromisoformat(args.reference_time)
        except ValueError as e:
            err = {"success": False, "error": f"Invalid reference time format: {e}"}
            print(serializer.serialize(err))
            sys.exit(1)

    result = inspect_contract_lifecycle(
        task_id=args.task_id,
        contracts_dir=args.contracts_dir,
        reports_dir=args.reports_dir,
        reference_time=ref_time
    )

    print(serializer.serialize(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
