import sys
import argparse
from datetime import datetime

from src.services.governance.execution_contract.completion_evidence_builder import CompletionEvidenceBuilder
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


def main():
    parser = argparse.ArgumentParser(description="Deterministic Completion Evidence Generator CLI.")
    parser.add_argument("--task-id", type=str, default=None, help="Task identifier.")
    parser.add_argument("--contract-id", required=True, help="Execution contract ID.")
    parser.add_argument("--worker-id", required=True, help="Worker/Actor ID.")
    parser.add_argument("--execution-transcript", type=str, default=None, help="Path to execution transcript markdown file.")
    parser.add_argument("--tool-trace-file", type=str, default=None, help="Path to tool trace JSON file.")
    parser.add_argument("--worker-report", type=str, default=None, help="Path to worker report markdown file.")
    parser.add_argument("--actual-output", nargs="*", default=[], help="List of actual output file paths.")
    parser.add_argument("--status", type=str, default="SUCCESS", help="Completion status (SUCCESS, FAILED, PARTIAL).")
    parser.add_argument("--completion-time", type=str, default=None, help="ISO format timestamp.")
    parser.add_argument("--output-file", type=str, default=None, help="Optional output JSON file path to save the generated evidence.")
    parser.add_argument("--root-dir", type=str, default=".", help="Root directory for checking physical output file existence.")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()

    if not args.actual_output:
        err = {"success": False, "error": "At least one actual output file must be specified."}
        print(serializer.serialize(err))
        sys.exit(1)

    try:
        builder = CompletionEvidenceBuilder(contract_id=args.contract_id, worker_id=args.worker_id, root_dir=args.root_dir)
        builder.set_status(args.status)

        if args.completion_time:
            try:
                dt = datetime.fromisoformat(args.completion_time)
                builder.set_timestamp(dt)
            except ValueError as e:
                raise ValueError(f"Invalid completion time format: {e}")

        builder.add_actual_outputs(args.actual_output)

        if args.tool_trace_file:
            builder.parse_and_add_tool_trace(args.tool_trace_file)

        if args.execution_transcript:
            builder.parse_and_add_transcript(args.execution_transcript)

        if args.worker_report:
            builder.parse_and_add_worker_report(args.worker_report)

        evidence = builder.build()
        out_dict = serializer.to_dict(evidence)
        json_str = serializer.serialize(out_dict)

        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(json_str)

        print(json_str)
        sys.exit(0)

    except Exception as e:
        err = {"success": False, "error": str(e)}
        print(serializer.serialize(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
