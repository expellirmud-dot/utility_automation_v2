from .incident_review_models import IncidentReviewItem


MOCK_INCIDENTS: tuple[IncidentReviewItem, ...] = (
    IncidentReviewItem(
        incident_id="INC-1001",
        title="Voltage drift detected on feeder F-12",
        severity="high",
        status="under_review",
        summary="Telemetry indicates sustained voltage drift above configured threshold.",
        operator_note="Escalated for operator awareness; awaiting field confirmation.",
    ),
    IncidentReviewItem(
        incident_id="INC-1002",
        title="Intermittent sensor heartbeat loss",
        severity="medium",
        status="queued",
        summary="Heartbeat packets dropped for sensor cluster SC-4 in two cycles.",
        operator_note="No control action allowed in this console; monitor only.",
    ),
    IncidentReviewItem(
        incident_id="INC-1003",
        title="Policy conflict surfaced in dry-run",
        severity="low",
        status="resolved_pending_review",
        summary="Conflict detected in simulation replay; no runtime mutation performed.",
        operator_note="Resolution evidence attached by mock provider.",
    ),
)
