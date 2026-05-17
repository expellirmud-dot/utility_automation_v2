import os
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from src.services.governance.execution_contract.execution_contract_exceptions import EvidenceValidationError
from src.services.governance.execution_contract.execution_contract_serializer import ExecutionContractSerializer


class ArtifactBundleValidator:
    """
    Enforces canonical artifact naming, schema validity, template completeness,
    and runtime manifest generation/validation for AI runtime execution artifacts.
    """

    def __init__(self, task_id: str, worker_id: str = "WORKER-01", root_dir: str = "."):
        self.task_id = task_id
        self.worker_id = worker_id
        self.root_dir = root_dir
        self.serializer = ExecutionContractSerializer()

    @staticmethod
    def get_canonical_names(task_id: str) -> Dict[str, str]:
        return {
            "execution_transcript": f"{task_id}-execution-transcript.md",
            "tool_trace": f"{task_id}-tool-trace.json",
            "worker_report": f"{task_id}-worker-report.md",
            "validation_output": f"{task_id}-validation-output.txt",
            "evidence": f"{task_id}-evidence.json",
            "runtime_manifest": f"{task_id}-runtime-manifest.json",
        }

    def compute_file_hash(self, file_path: str) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)
        return sha.hexdigest()

    @staticmethod
    def standardize_tool_trace(raw_data: Union[List[Dict[str, Any]], Dict[str, Any]], task_id: str, worker_id: str = "WORKER-01") -> Dict[str, Any]:
        """
        Converts a raw list or older dictionary trace into the canonical runtime-tool-trace-v1 schema.
        """
        if isinstance(raw_data, dict) and raw_data.get("schema_version") == "runtime-tool-trace-v1":
            return raw_data

        events = []
        if isinstance(raw_data, list):
            events = raw_data
        elif isinstance(raw_data, dict):
            if "events" in raw_data and isinstance(raw_data["events"], list):
                events = raw_data["events"]
            elif "trace" in raw_data and isinstance(raw_data["trace"], list):
                events = raw_data["trace"]
            else:
                for k, v in raw_data.items():
                    if isinstance(v, list):
                        events.extend(v)
                if not events:
                    events = [raw_data]

        return {
            "schema_version": "runtime-tool-trace-v1",
            "task_id": task_id,
            "worker_id": worker_id,
            "generated_at": datetime.now().isoformat(),
            "events": events
        }

    def validate_tool_trace_schema(self, file_path: str) -> List[Dict[str, Any]]:
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise EvidenceValidationError(f"Missing required tool trace artifact: {os.path.basename(file_path)}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise EvidenceValidationError(f"Malformed JSON in tool trace artifact: {str(e)}")

        if not isinstance(data, dict):
            raise EvidenceValidationError(f"Tool trace must be a canonical JSON object, got {type(data).__name__}")

        version = data.get("schema_version")
        if version != "runtime-tool-trace-v1":
            raise EvidenceValidationError(f"Invalid tool trace schema_version: expected runtime-tool-trace-v1, got {version}")

        task_id = data.get("task_id")
        if task_id != self.task_id:
            raise EvidenceValidationError(f"Tool trace task_id mismatch: expected {self.task_id}, got {task_id}")

        if "events" not in data or not isinstance(data["events"], list):
            raise EvidenceValidationError("Tool trace missing required list property 'events'")

        return data["events"]

    def validate_execution_transcript(self, file_path: str):
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise EvidenceValidationError(f"Missing required execution transcript artifact: {os.path.basename(file_path)}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise EvidenceValidationError(f"Failed to read execution transcript: {str(e)}")

        required_headings = [
            "Task identification",
            "Read-first inspection",
            "Files inspected",
            "Files changed",
            "Commands executed",
            "Validation summary",
            "Notes"
        ]
        missing = []
        for h in required_headings:
            if not re.search(r"^#+\s+" + re.escape(h), content, re.MULTILINE | re.IGNORECASE):
                missing.append(h)

        if missing:
            raise EvidenceValidationError(f"Execution transcript missing required template sections: {', '.join(missing)}")

    def validate_worker_report(self, file_path: str):
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise EvidenceValidationError(f"Missing required worker report artifact: {os.path.basename(file_path)}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise EvidenceValidationError(f"Failed to read worker report: {str(e)}")

        required_headings = [
            "Objective",
            "Scope completed",
            "Artifacts produced",
            "Validation results",
            "Risks",
            "Controller handoff"
        ]
        missing = []
        for h in required_headings:
            if not re.search(r"^#+\s+" + re.escape(h), content, re.MULTILINE | re.IGNORECASE):
                missing.append(h)

        if missing:
            raise EvidenceValidationError(f"Worker report missing required template sections: {', '.join(missing)}")

    def validate_validation_output(self, file_path: str):
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise EvidenceValidationError(f"Missing required validation output artifact: {os.path.basename(file_path)}")
        try:
            if os.path.getsize(full_path) == 0:
                raise EvidenceValidationError(f"Validation output artifact is empty: {os.path.basename(file_path)}")
        except Exception as e:
            raise EvidenceValidationError(f"Failed to inspect validation output artifact: {str(e)}")

    def validate_bundle(self, reports_dir: str = "ai_runtime/reports") -> Dict[str, Any]:
        names = self.get_canonical_names(self.task_id)
        
        transcript_path = os.path.join(reports_dir, names["execution_transcript"])
        trace_path = os.path.join(reports_dir, names["tool_trace"])
        report_path = os.path.join(reports_dir, names["worker_report"])
        val_output_path = os.path.join(reports_dir, names["validation_output"])

        self.validate_execution_transcript(transcript_path)
        self.validate_tool_trace_schema(trace_path)
        self.validate_worker_report(report_path)
        self.validate_validation_output(val_output_path)

        manifest_path = os.path.join(self.root_dir, reports_dir, names["runtime_manifest"])
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                if manifest_data.get("task_id") != self.task_id:
                    raise EvidenceValidationError(f"Runtime manifest task_id mismatch: expected {self.task_id}, got {manifest_data.get('task_id')}")
            except Exception as e:
                raise EvidenceValidationError(f"Malformed runtime manifest: {str(e)}")

        return {
            "is_valid": True,
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "validated_artifacts": [names["execution_transcript"], names["tool_trace"], names["worker_report"], names["validation_output"]],
            "timestamp": datetime.now().isoformat()
        }

    def generate_manifest(self, reports_dir: str = "ai_runtime/reports", save: bool = True) -> Dict[str, Any]:
        names = self.get_canonical_names(self.task_id)
        artifacts_dict = {}
        hashes_dict = {}

        abs_reports_dir = os.path.join(self.root_dir, reports_dir)
        os.makedirs(abs_reports_dir, exist_ok=True)

        for k in ["execution_transcript", "tool_trace", "worker_report", "validation_output"]:
            filename = names[k]
            full_path = os.path.join(abs_reports_dir, filename)
            if os.path.exists(full_path):
                rel = os.path.normpath(os.path.join(reports_dir, filename)).replace("\\", "/")
                artifacts_dict[k] = rel
                hashes_dict[k] = self.compute_file_hash(full_path)

        manifest = {
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "generated_at": datetime.now().isoformat(),
            "artifacts": artifacts_dict,
            "hashes": hashes_dict
        }

        if save:
            manifest_path = os.path.join(abs_reports_dir, names["runtime_manifest"])
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(self.serializer.serialize(manifest))

        return manifest
