from __future__ import annotations

import random

from src.services.dashboard.projection_repository import DashboardProjectionRecord

DASHBOARD_BUCKET = "governance_dashboard"
DASHBOARD_SEED = 41041


def build_deterministic_dashboard_records(
    bucket: str = DASHBOARD_BUCKET,
    seed: int = DASHBOARD_SEED,
) -> list[DashboardProjectionRecord]:
    rng = random.Random(seed)

    health_score = round(rng.uniform(96.0, 99.4), 1)
    open_incidents = rng.randint(8, 16)
    replay_checks = rng.randint(1180, 1380)
    avg_review_seconds = rng.randint(230, 295)
    avg_minutes, avg_seconds = divmod(avg_review_seconds, 60)

    stats = [
        {
            "key": "health",
            "label": "Health Score",
            "value": f"{health_score}%",
            "delta": "+2.1%",
            "tone": "teal",
        },
        {
            "key": "incidents",
            "label": "Open Incidents",
            "value": str(open_incidents),
            "delta": "-4 today",
            "tone": "orange",
        },
        {
            "key": "replay",
            "label": "Replay Checks",
            "value": f"{replay_checks:,}",
            "delta": "100% pass",
            "tone": "emerald",
        },
        {
            "key": "review_time",
            "label": "Avg Review Time",
            "value": f"{avg_minutes}m {avg_seconds:02d}s",
            "delta": "-38s",
            "tone": "slate",
        },
    ]

    bars = [rng.randint(52, 94) for _ in range(8)]
    summaries = [
        {"label": "Replay pass rate", "value": "100%"},
        {"label": "Median queue", "value": f"{rng.randint(6, 10)}m"},
        {"label": "Open risk", "value": f"{rng.randint(2, 4)} high"},
    ]
    activity = [
        {
            "title": "Quorum approval recorded",
            "detail": "Recovery proposal REC-219 passed review",
            "time": "2 min ago",
        },
        {
            "title": "Ledger replay completed",
            "detail": "No causal mismatch detected in current window",
            "time": "14 min ago",
        },
        {
            "title": "Operator note added",
            "detail": "Incident INC-1042 updated by governance lead",
            "time": "28 min ago",
        },
        {
            "title": "Simulation finished",
            "detail": "Policy candidate generated advisory report only",
            "time": "51 min ago",
        },
    ]
    incidents = [
        {
            "id": "INC-1042",
            "title": "Invoice provider confidence drift",
            "owner": "Nara",
            "status": "Reviewing",
            "risk": "Medium",
            "age": "18m",
        },
        {
            "id": "INC-1039",
            "title": "Replay checkpoint delayed",
            "owner": "Anan",
            "status": "Queued",
            "risk": "Low",
            "age": "42m",
        },
        {
            "id": "INC-1031",
            "title": "Policy graph conflict candidate",
            "owner": "Mali",
            "status": "Blocked",
            "risk": "High",
            "age": "1h",
        },
        {
            "id": "INC-1027",
            "title": "Correction workflow needs operator note",
            "owner": "Krit",
            "status": "Resolved",
            "risk": "Low",
            "age": "2h",
        },
    ]

    records: list[DashboardProjectionRecord] = []
    records.extend(
        DashboardProjectionRecord(bucket, item["key"], "stat", index, item)
        for index, item in enumerate(stats)
    )
    records.extend(
        DashboardProjectionRecord(bucket, f"bar-{index:02d}", "throughput_bar", index, {"value": value})
        for index, value in enumerate(bars)
    )
    records.extend(
        DashboardProjectionRecord(bucket, item["label"].lower().replace(" ", "_"), "throughput_summary", index, item)
        for index, item in enumerate(summaries)
    )
    records.extend(
        DashboardProjectionRecord(bucket, f"activity-{index:02d}", "activity", index, item)
        for index, item in enumerate(activity)
    )
    records.extend(
        DashboardProjectionRecord(bucket, item["id"], "incident", index, item)
        for index, item in enumerate(incidents)
    )
    return records
