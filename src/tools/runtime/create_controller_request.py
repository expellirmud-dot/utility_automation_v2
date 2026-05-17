import os
import sys
import json
import argparse
from typing import List, Dict, Any
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.services.governance.execution_contract.controller_request_validator import ControllerRequestValidator


CONSTRAINTS_LIST = [
    "ledger remains sole source of truth",
    "SQLite is projection/cache only",
    "AI advisory only",
    "no autonomous authority mutation",
    "no self-approval",
    "no hidden execution channels",
    "no frontend authority expansion",
    "preserve existing workflow"
]

NON_GOALS_LIST = [
    "autonomous task planning",
    "automatic scope invention",
    "scheduler design",
    "governance redesign",
    "promotion authority mutation",
    "freeform worker autonomy"
]

DISCIPLINE_LIST = [
    "READ-FIRST mandatory",
    "Inspect actual files first",
    "Use Serena when relevant",
    "Treat ai_runtime/inbox controller requests as READ-ONLY",
    "No implementation from memory",
    "Return exact validation output",
    "Separate evidence from assumptions"
]


def render_items(items: List[str], prefix: str = "- ") -> str:
    return "\n".join(f"{prefix}{item}" for item in items)


def create_request_content(args: argparse.Namespace) -> str:
    scope_str = render_items(args.scope)
    modules_str = "\n".join(args.candidate_modules)
    tests_str = "\n".join(args.tests)
    validation_str = render_items(args.validation)
    acceptance_str = render_items(args.acceptance)

    constraints_str = render_items(CONSTRAINTS_LIST)
    non_goals_str = render_items(NON_GOALS_LIST)
    discipline_str = "\n".join(DISCIPLINE_LIST)

    return f"""# Controller Execution Request

## Task ID
{args.task_id}

## Title
{args.title}

## Authority
Human-approved controller request

## Objective
{args.objective}

## Architectural rationale
{args.rationale}

## Scope

### In scope
{scope_str}

### Candidate modules
{modules_str}

### Runtime artifacts
ai_runtime/contracts/
ai_runtime/completions/
ai_runtime/reports/
ai_runtime/inbox/

### Tests
{tests_str}

## Constraints
{constraints_str}

## Non-goals
{non_goals_str}

## Required validation
{validation_str}

## Acceptance criteria
{acceptance_str}

## Required execution discipline
{discipline_str}

## State
APPROVED FOR IMPLEMENTATION

## Next
{args.next_task}
"""


def main():
    parser = argparse.ArgumentParser(description="Deterministic Controller Request Generator CLI.")
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. TASK-080).")
    parser.add_argument("--title", required=True, help="Task title.")
    parser.add_argument("--objective", required=True, help="Primary objective.")
    parser.add_argument("--rationale", required=True, help="Architectural rationale.")
    parser.add_argument("--scope", required=True, nargs="+", help="In-scope bullet items.")
    parser.add_argument("--candidate-modules", required=True, nargs="+", help="Candidate module paths.")
    parser.add_argument("--tests", required=True, nargs="+", help="Test file paths.")
    parser.add_argument("--validation", required=True, nargs="+", help="Required validation items.")
    parser.add_argument("--acceptance", required=True, nargs="+", help="Acceptance criteria items.")
    parser.add_argument("--next-task", default="TASK XXX [TBD]", help="Next task reference.")
    parser.add_argument("--output-file", default=None, help="Output file path (default: ai_runtime/inbox/{task_id}-controller-request.md).")

    args = parser.parse_args()
    serializer = ExecutionContractSerializer()
    validator = ControllerRequestValidator()

    output_path = args.output_file or f"ai_runtime/inbox/{args.task_id}-controller-request.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    content = create_request_content(args)

    # Validate generated content before writing to ensure 100% placeholder-free compliance
    val_res = validator.validate_request_content(content)
    if not val_res["is_valid"]:
        err = {
            "status": "FAILED",
            "task_id": args.task_id,
            "reason": f"Generated request failed internal validation: {val_res['reason']}",
            "placeholders": val_res["placeholders_found"]
        }
        print(serializer.serialize(err))
        sys.exit(1)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        err = {
            "status": "FAILED",
            "task_id": args.task_id,
            "reason": f"Failed to write output file: {str(e)}"
        }
        print(serializer.serialize(err))
        sys.exit(1)

    success_msg = {
        "status": "SUCCESS",
        "task_id": args.task_id,
        "title": args.title,
        "output_file": output_path,
        "is_valid": True
    }
    print(serializer.serialize(success_msg))
    sys.exit(0)


if __name__ == "__main__":
    main()
