import sys
import argparse
from src.services.governance.runtime_contract_guard.runtime_contract_guard import RuntimeContractGuard
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def main():
    parser = argparse.ArgumentParser(description="Active Runtime Action Enforcement CLI Gate.")
    parser.add_argument("--task-id", required=True, help="Task identifier.")
    parser.add_argument("--actor-id", required=True, help="Assigned worker actor ID.")
    parser.add_argument("--action-type", required=True, choices=["read", "write", "command", "other"], help="Action type to enforce.")
    parser.add_argument("--path", default="any", help="Target path for read or write actions.")
    parser.add_argument("--command", default=None, help="Command string for command actions.")
    parser.add_argument("--contracts-dir", default="ai_runtime/contracts", help="Contracts storage directory.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()
    guard = RuntimeContractGuard(contracts_dir=args.contracts_dir)

    try:
        result = guard.validate_action(
            task_id=args.task_id,
            worker_id=args.actor_id,
            action_type=args.action_type,
            path=args.path,
            command=args.command
        )
        out_dict = serializer.to_dict(result)
        print(serializer.serialize(out_dict))

        if not result.is_allowed:
            sys.exit(1)
        sys.exit(0)

    except Exception as e:
        err = {
            "is_allowed": False,
            "task_id": args.task_id,
            "worker_id": args.actor_id,
            "contract_id": None,
            "reason": str(e)
        }
        print(serializer.serialize(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
