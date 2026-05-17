import sys
import argparse
from src.services.governance.execution_contract.controller_request_validator import ControllerRequestValidator
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def main():
    parser = argparse.ArgumentParser(description="Deterministic Controller Request Completeness and Governance Gate.")
    parser.add_argument("--request-file", required=True, help="Path to the controller request markdown artifact.")

    args = parser.parse_args()
    validator = ControllerRequestValidator()
    serializer = ExecutionContractSerializer()

    result = validator.validate_request_file(args.request_file)
    print(serializer.serialize(result))

    if not result["is_valid"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
