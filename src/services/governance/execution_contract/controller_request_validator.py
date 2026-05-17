import os
import re
from typing import Dict, Any, List, Tuple


class ControllerRequestValidator:
    """
    Deterministically validates controller request markdown artifacts for structural completeness
    and uninstantiated template placeholders before implementation contracts are issued.
    Enforces fail-closed governance on request authority quality.
    """

    REQUIRED_SECTIONS = [
        "Task ID",
        "Title",
        "Objective",
        "Scope",
        "Required validation",
        "Acceptance criteria"
    ]

    PLACEHOLDER_PATTERNS = [
        r"\[REPLACE[^\]]*\]",
        r"REPLACE_WITH_[A-Z_]+",
        r"<REPLACE[^>]*>",
        r"\[TODO[^\]]*\]",
        r"\[FIXME[^\]]*\]",
        r"\[\]",
        r"\[\s+\]"
    ]

    def validate_request_file(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "is_valid": False,
                "task_id": None,
                "title": None,
                "reason": f"Controller request file not found on disk: {file_path}",
                "missing_sections": self.REQUIRED_SECTIONS,
                "placeholders_found": []
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "is_valid": False,
                "task_id": None,
                "title": None,
                "reason": f"Failed to read controller request file: {str(e)}",
                "missing_sections": [],
                "placeholders_found": []
            }

        return self.validate_request_content(content, file_source=file_path)

    def validate_request_content(self, content: str, file_source: str = "content") -> Dict[str, Any]:
        lines = content.splitlines()

        # Extract sections and their contents
        sections_found = set()
        current_section = None
        section_lines: Dict[str, List[str]] = {}

        task_id = None
        title = None

        for line in lines:
            header_match = re.match(r"^##\s+(.+)$", line.strip())
            if header_match:
                current_section = header_match.group(1).strip()
                sections_found.add(current_section)
                section_lines[current_section] = []
            elif current_section:
                section_lines[current_section].append(line)
            elif re.match(r"^#\s+(.+)$", line.strip()):
                pass # Top level title

        # Verify all required sections exist
        missing = [sec for sec in self.REQUIRED_SECTIONS if sec not in sections_found]

        # Extract Task ID and Title
        if "Task ID" in section_lines:
            for l in section_lines["Task ID"]:
                s = l.strip()
                if s and not s.startswith("#"):
                    task_id = s
                    break

        if "Title" in section_lines:
            for l in section_lines["Title"]:
                s = l.strip()
                if s and not s.startswith("#"):
                    title = s
                    break

        # Check for placeholders
        placeholders = []
        for sec, slines in section_lines.items():
            for line_idx, line in enumerate(slines):
                # If section is Next, allow [TBD]
                if sec == "Next" and "[TBD]" in line:
                    continue
                if "[TBD]" in line and sec != "Next":
                    placeholders.append(f"[TBD] in section ## {sec}")

                for pat in self.PLACEHOLDER_PATTERNS:
                    matches = re.findall(pat, line)
                    for match in matches:
                        placeholders.append(f"'{match}' in section ## {sec}")

        if missing or placeholders or not task_id or not title:
            reasons = []
            if missing:
                reasons.append(f"Missing required sections: {', '.join(missing)}")
            if placeholders:
                reasons.append(f"Unresolved placeholders found: {', '.join(placeholders)}")
            if not task_id:
                reasons.append("Task ID section is empty or unparseable")
            if not title:
                reasons.append("Title section is empty or unparseable")

            return {
                "is_valid": False,
                "task_id": task_id,
                "title": title,
                "reason": "; ".join(reasons),
                "missing_sections": missing,
                "placeholders_found": placeholders
            }

        return {
            "is_valid": True,
            "task_id": task_id,
            "title": title,
            "reason": "Controller request successfully validated for structural completeness and placeholder absence.",
            "missing_sections": [],
            "placeholders_found": []
        }
