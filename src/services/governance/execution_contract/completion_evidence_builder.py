import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from src.services.governance.execution_contract.execution_contract_models import CompletionEvidence
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer
from src.services.governance.execution_contract.execution_contract_exceptions import EvidenceValidationError


class CompletionEvidenceBuilder:
    """
    Builds canonical CompletionEvidence manifests from runtime execution artifacts.
    Enforces deterministic hashing and physical output verification on disk.
    """

    def __init__(self, contract_id: str, worker_id: str, root_dir: str = "."):
        self.contract_id = contract_id
        self.worker_id = worker_id
        self.root_dir = root_dir
        self._actual_outputs: List[str] = []
        self._execution_trace: List[Dict[str, Any]] = []
        self._completion_timestamp: datetime = datetime.now()
        self._status: str = "SUCCESS"
        self.serializer = ExecutionContractSerializer()

    def set_status(self, status: str) -> "CompletionEvidenceBuilder":
        if status not in ("SUCCESS", "FAILED", "PARTIAL"):
            raise EvidenceValidationError(f"Invalid completion status: {status}")
        self._status = status
        return self

    def set_timestamp(self, timestamp: datetime) -> "CompletionEvidenceBuilder":
        self._completion_timestamp = timestamp
        return self

    def add_actual_outputs(self, outputs: List[str]) -> "CompletionEvidenceBuilder":
        self._actual_outputs.extend(outputs)
        return self

    def add_trace_steps(self, steps: List[Dict[str, Any]]) -> "CompletionEvidenceBuilder":
        self._execution_trace.extend(steps)
        return self

    def parse_and_add_tool_trace(self, json_content_or_file: str) -> "CompletionEvidenceBuilder":
        """
        Deterministically parses a tool trace JSON string or file path.
        Recognizes write and read actions conservatively. Fail-closed on malformed JSON.
        """
        content = json_content_or_file
        if os.path.exists(os.path.join(self.root_dir, json_content_or_file)):
            try:
                with open(os.path.join(self.root_dir, json_content_or_file), 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise EvidenceValidationError(f"Failed to read tool trace file: {str(e)}")

        try:
            data = json.loads(content)
        except Exception as e:
            raise EvidenceValidationError(f"Malformed tool trace JSON: {str(e)}")

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if "events" in data and isinstance(data["events"], list):
                items = data["events"]
            elif "trace" in data and isinstance(data["trace"], list):
                items = data["trace"]
            else:
                for k, v in data.items():
                    if isinstance(v, list):
                        items.extend(v)
                if not items:
                    items = [data]
        else:
            raise EvidenceValidationError(f"Invalid tool trace JSON structure: expected list or object, got {type(data)}")

        write_tools = {"create_text_file", "serena_create_text_file", "replace_content", "replace_lines", "delete_lines", "insert_at_line", "write_memory"}
        read_tools = {"read_file", "serena_read_file", "list_dir", "serena_list_dir", "find_file", "search_for_pattern", "read_memory", "get_symbols_overview", "find_symbol", "find_referencing_symbols", "find_implementations", "find_declaration", "get_diagnostics_for_file"}

        for item in items:
            if not isinstance(item, dict):
                continue
            tool_name = item.get("tool", "")
            action = "other"
            if any(tool_name == wt or tool_name.endswith(f"_{wt}") or tool_name.startswith(wt) for wt in write_tools):
                action = "write"
            elif any(tool_name == rt or tool_name.endswith(f"_{rt}") or tool_name.startswith(rt) for rt in read_tools):
                action = "read"
            elif "execute_shell_command" in tool_name or tool_name == "command":
                action = "command"

            args = item.get("argument", item.get("arguments", {}))
            path = args.get("relative_path", args.get("file_path", args.get("path", args.get("AbsolutePath", ""))))
            cmd = args.get("command", args.get("CommandLine", ""))

            step = {"action": action, "tool": tool_name}
            if path:
                step["path"] = path
            if cmd:
                step["command"] = cmd
            if "purpose" in item:
                step["purpose"] = item["purpose"]

            self._execution_trace.append(step)

        return self

    def parse_and_add_transcript(self, markdown_content_or_file: str) -> "CompletionEvidenceBuilder":
        """
        Parses an execution transcript markdown file for context.
        """
        content = markdown_content_or_file
        if os.path.exists(os.path.join(self.root_dir, markdown_content_or_file)):
            try:
                with open(os.path.join(self.root_dir, markdown_content_or_file), 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise EvidenceValidationError(f"Failed to read transcript file: {str(e)}")
        summary = content[:100] + "..." if len(content) > 100 else content
        self._execution_trace.append({"action": "note", "source": "transcript", "summary": summary})
        return self

    def parse_and_add_worker_report(self, markdown_content_or_file: str) -> "CompletionEvidenceBuilder":
        """
        Parses a worker report markdown file for context.
        """
        content = markdown_content_or_file
        if os.path.exists(os.path.join(self.root_dir, markdown_content_or_file)):
            try:
                with open(os.path.join(self.root_dir, markdown_content_or_file), 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise EvidenceValidationError(f"Failed to read worker report file: {str(e)}")
        summary = content[:100] + "..." if len(content) > 100 else content
        self._execution_trace.append({"action": "note", "source": "worker_report", "summary": summary})
        return self

    def build(self) -> CompletionEvidence:
        """
        Verifies all actual output files exist on physical disk and builds the deterministically hashed CompletionEvidence.
        """
        for output_path in self._actual_outputs:
            full_path = os.path.join(self.root_dir, output_path)
            if not os.path.exists(full_path):
                raise EvidenceValidationError(f"Missing required actual output file on disk: {output_path}")

        candidate = CompletionEvidence(
            contract_id=self.contract_id,
            worker_id=self.worker_id,
            actual_outputs=sorted(list(set(self._actual_outputs))),
            execution_trace=self._execution_trace,
            completion_timestamp=self._completion_timestamp,
            status=self._status,
            evidence_hash=None
        )

        computed_hash = self.serializer.compute_hash(candidate)

        return CompletionEvidence(
            contract_id=candidate.contract_id,
            worker_id=candidate.worker_id,
            actual_outputs=candidate.actual_outputs,
            execution_trace=candidate.execution_trace,
            completion_timestamp=candidate.completion_timestamp,
            status=candidate.status,
            evidence_hash=computed_hash
        )
