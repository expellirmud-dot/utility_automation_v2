import os
import sys
import argparse
import json
from src.services.governance.execution_contract.execution_contract_validator import ExecutionContractValidator
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def main():
    parser = argparse.ArgumentParser(description="Completion Validation CLI.")
    parser.add_argument("--evidence-file", required=True, help="Path to completion evidence JSON file.")
    parser.add_argument("--task-id", type=str, default=None, help="Task identifier to locate contract file.")
    parser.add_argument("--contract-file", type=str, default=None, help="Explicit path to execution contract JSON file.")
    parser.add_argument("--contracts-dir", type=str, default="ai_runtime/contracts", help="Contracts storage directory.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    contract_path = args.contract_file
    if not contract_path:
        if not args.task_id:
            err = {"is_valid": False, "contract_id": None, "worker_id": None, "reason": "Either --task-id or --contract-file must be specified."}
            print(serializer.serialize(err))
            sys.exit(1)
        contract_path = os.path.join(args.contracts_dir, f"{args.task_id}.json")

    if not os.path.exists(contract_path):
        err = {"is_valid": False, "contract_id": None, "worker_id": None, "reason": f"Contract file not found at {contract_path}"}
        print(serializer.serialize(err))
        sys.exit(1)

    if not os.path.exists(args.evidence_file):
        err = {"is_valid": False, "contract_id": None, "worker_id": None, "reason": f"Evidence file not found at {args.evidence_file}"}
        print(serializer.serialize(err))
        sys.exit(1)

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract_data = json.load(f)
        contract = serializer.deserialize_contract(contract_data)
    except Exception as e:
        err = {"is_valid": False, "contract_id": None, "worker_id": None, "reason": f"Failed to deserialize contract: {str(e)}"}
        print(serializer.serialize(err))
        sys.exit(1)

    try:
        with open(args.evidence_file, "r", encoding="utf-8") as f:
            evidence_data = json.load(f)
        evidence = serializer.deserialize_evidence(evidence_data)
    except Exception as e:
        err = {"is_valid": False, "contract_id": contract.contract_id, "worker_id": None, "reason": f"Failed to deserialize evidence: {str(e)}"}
        print(serializer.serialize(err))
        sys.exit(1)

    validator = ExecutionContractValidator()
    try:
        validator.validate_completion(contract, evidence)
        result = {
            "is_valid": True,
            "contract_id": contract.contract_id,
            "worker_id": evidence.worker_id,
            "reason": "Completion evidence successfully validated against execution contract."
        }
        print(serializer.serialize(result))
        sys.exit(0)
    except Exception as e:
        result = {
            "is_valid": False,
            "contract_id": contract.contract_id,
            "worker_id": evidence.worker_id,
            "reason": str(e)
        }
        print(serializer.serialize(result))
        sys.exit(1)


if __name__ == "__main__":
    main()
