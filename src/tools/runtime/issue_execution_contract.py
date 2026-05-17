import sys
import argparse
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.services.governance.execution_contract.execution_contract_issuance_service import ExecutionContractIssuanceService
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def parse_metadata(meta_args: Optional[List[str]]) -> Dict[str, Any]:
    if not meta_args:
        return {}
    if len(meta_args) == 1 and meta_args[0].strip().startswith('{'):
        try:
            return json.loads(meta_args[0])
        except Exception as e:
            raise ValueError(f"Malformed JSON metadata: {str(e)}")
    result = {}
    for item in meta_args:
        if '=' not in item:
            raise ValueError(f"Malformed metadata entry (expected key=val or valid JSON): {item}")
        k, v = item.split('=', 1)
        result[k.strip()] = v.strip()
    return result


def main():
    parser = argparse.ArgumentParser(description="Deterministic Controller Contract Issuance CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier.")
    parser.add_argument("--actor-id", required=True, help="Assigned worker actor ID.")
    parser.add_argument("--allow-read", nargs="*", default=[], help="Allowed read paths.")
    parser.add_argument("--allow-write", nargs="*", default=[], help="Allowed write paths.")
    parser.add_argument("--expected-output", nargs="*", default=[], help="Expected output file paths.")
    parser.add_argument("--allow-command", nargs="*", default=None, help="Allowed shell commands.")
    parser.add_argument("--forbid-pattern", nargs="*", default=None, help="Forbidden action patterns.")
    parser.add_argument("--metadata", nargs="*", default=None, help="Optional metadata as key=val pairs or JSON string.")
    parser.add_argument("--duration-mins", type=int, default=60, help="Contract validity duration in minutes.")
    parser.add_argument("--reference-time", type=str, default=None, help="Deterministic reference timestamp in ISO format.")
    parser.add_argument("--contract-id", type=str, default=None, help="Deterministic contract ID override.")
    parser.add_argument("--contracts-dir", type=str, default="ai_runtime/contracts", help="Contracts storage directory.")

    args = parser.parse_args()

    serializer = ExecutionContractSerializer()

    # Enforcement of fail-closed constraints
    if not args.allow_read and not args.allow_write:
        err = {"success": False, "error": "Contract scope must allow at least one read or write path."}
        print(serializer.serialize(err))
        sys.exit(1)

    if not args.expected_output:
        err = {"success": False, "error": "At least one expected output path must be specified."}
        print(serializer.serialize(err))
        sys.exit(1)

    ref_time = None
    if args.reference_time:
        try:
            ref_time = datetime.fromisoformat(args.reference_time)
        except ValueError as e:
            err = {"success": False, "error": f"Invalid reference time format: {e}"}
            print(serializer.serialize(err))
            sys.exit(1)

    try:
        meta = parse_metadata(args.metadata)
    except ValueError as e:
        err = {"success": False, "error": str(e)}
        print(serializer.serialize(err))
        sys.exit(1)

    try:
        service = ExecutionContractIssuanceService(contracts_dir=args.contracts_dir)
        contract = service.issue_contract(
            task_id=args.task_id,
            actor_id=args.actor_id,
            read_paths=args.allow_read,
            write_paths=args.allow_write,
            expected_outputs=args.expected_output,
            commands=args.allow_command,
            forbidden_patterns=args.forbid_pattern,
            validity_duration_minutes=args.duration_mins,
            metadata=meta,
            reference_time=ref_time,
            contract_id=args.contract_id
        )

        out_dict = serializer.to_dict(contract)
        print(serializer.serialize(out_dict))
        sys.exit(0)

    except Exception as e:
        err = {"success": False, "error": str(e)}
        print(serializer.serialize(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
