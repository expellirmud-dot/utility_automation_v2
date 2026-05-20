from sqlalchemy.orm import Session

from src.product.db.models import Case, CaseNote, CaseTimelineEvent


LIFECYCLE_STATES = (
    "intake",
    "documents_uploaded",
    "ocr_processed",
    "dika_prepared",
    "memo_generated",
    "readiness_passed",
    "elaas_prepared",
    "submitted_manual",
    "completed",
)

LEGACY_STATUS_ALIASES = {
    "draft": "intake",
    "word_generated": "memo_generated",
}

EVENT_TARGET_STATUS = {
    "document_uploaded": "documents_uploaded",
    "ocr_success": "ocr_processed",
    "dika_saved": "dika_prepared",
    "memo_generated": "memo_generated",
    "elaas_payload_saved": "elaas_prepared",
    "submitted_manually": "submitted_manual",
    "completed_manually": "completed",
}


class WorkflowLifecycleService:
    @staticmethod
    def normalize_status(status: str | None) -> str:
        if not status:
            return "intake"
        return LEGACY_STATUS_ALIASES.get(status, status)

    @staticmethod
    def _state_index(status: str) -> int:
        normalized = WorkflowLifecycleService.normalize_status(status)
        if normalized not in LIFECYCLE_STATES:
            raise ValueError(f"Unknown case lifecycle status: {status}")
        return LIFECYCLE_STATES.index(normalized)

    @staticmethod
    def _advance_case(case: Case, target_status: str) -> tuple[str, str]:
        current_status = WorkflowLifecycleService.normalize_status(case.status)
        current_index = WorkflowLifecycleService._state_index(current_status)
        target_index = WorkflowLifecycleService._state_index(target_status)
        if target_index < current_index:
            return current_status, current_status
        case.status = target_status
        return current_status, target_status

    @staticmethod
    def record_event(db: Session, case: Case, event_type: str, detail: str = "") -> CaseTimelineEvent:
        target_status = EVENT_TARGET_STATUS[event_type]
        from_status, to_status = WorkflowLifecycleService._advance_case(case, target_status)
        event = CaseTimelineEvent(
            case_id=case.id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            detail=detail,
        )
        db.add(event)
        db.commit()
        db.refresh(case)
        db.refresh(event)
        return event

    @staticmethod
    def add_note(db: Session, case: Case, note_text: str) -> CaseNote:
        note = CaseNote(case_id=case.id, note_text=note_text.strip())
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def mark_submitted(db: Session, case: Case) -> CaseTimelineEvent:
        if WorkflowLifecycleService.normalize_status(case.status) != "elaas_prepared":
            raise ValueError("Case must be elaas_prepared before manual submission")
        return WorkflowLifecycleService.record_event(
            db,
            case,
            "submitted_manually",
            "Operator marked case as manually submitted to e-LAAS.",
        )

    @staticmethod
    def mark_completed(db: Session, case: Case) -> CaseTimelineEvent:
        if WorkflowLifecycleService.normalize_status(case.status) != "submitted_manual":
            raise ValueError("Case must be submitted_manual before completion")
        return WorkflowLifecycleService.record_event(
            db,
            case,
            "completed_manually",
            "Operator marked case as completed.",
        )
