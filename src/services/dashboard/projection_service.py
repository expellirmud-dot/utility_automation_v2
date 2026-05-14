from __future__ import annotations

from src.services.dashboard.projection_repository import DashboardProjectionRepository
from src.services.dashboard.projection_seed import (
    DASHBOARD_BUCKET,
    DASHBOARD_SEED,
    build_deterministic_dashboard_records,
)


class DashboardProjectionService:
    def __init__(
        self,
        repository: DashboardProjectionRepository | None = None,
        bucket: str = DASHBOARD_BUCKET,
        seed: int = DASHBOARD_SEED,
    ) -> None:
        self._repository = repository or DashboardProjectionRepository()
        self._bucket = bucket
        self._seed = seed

    def ensure_seeded(self) -> bool:
        return self._repository.insert_records_if_empty(
            self._bucket,
            build_deterministic_dashboard_records(self._bucket, self._seed),
        )

    def projection(self) -> dict:
        self.ensure_seeded()
        records = self._repository.list_bucket(self._bucket)

        return {
            "bucket": self._bucket,
            "stats": [record.payload for record in records if record.record_type == "stat"],
            "throughput": {
                "bars": [
                    int(record.payload["value"])
                    for record in records
                    if record.record_type == "throughput_bar"
                ],
                "summaries": [
                    record.payload
                    for record in records
                    if record.record_type == "throughput_summary"
                ],
            },
            "activity": [record.payload for record in records if record.record_type == "activity"],
            "incidents": [record.payload for record in records if record.record_type == "incident"],
            "generated_by": "deterministic_seed",
            "seed": self._seed,
        }
