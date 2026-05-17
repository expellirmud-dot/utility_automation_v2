import sys
import argparse
from src.services.governance.execution_contract.artifact_bundle_validator import ArtifactBundleValidator
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def main():
    parser = argparse.ArgumentParser(description="Runtime Artifact Bundle Completeness and Standardization Validator CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. TASK-076).")
    parser.add_argument("--worker-id", default="WORKER-01", help="Worker/Actor ID.")
    parser.add_argument("--reports-dir", default="ai_runtime/reports", help="Directory containing runtime reports and artifacts.")
    parser.add_argument("--generate-manifest", action="store_true", help="Generate runtime manifest JSON upon successful validation.")
    parser.add_argument("--root-dir", default=".", help="Root directory for absolute path resolution.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    try:
        validator = ArtifactBundleValidator(task_id=args.task_id, worker_id=args.worker_id, root_dir=args.root_dir)
        result = validator.validate_bundle(reports_dir=args.reports_dir)

        if args.generate_manifest:
            manifest = validator.generate_manifest(reports_dir=args.reports_dir, save=True)
            result["manifest"] = manifest

        print(serializer.serialize(result))
        sys.exit(0)

    except Exception as e:
        err = {"is_valid": False, "task_id": args.task_id, "error": str(e)}
        print(serializer.serialize(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
