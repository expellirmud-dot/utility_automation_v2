from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

from src.storage.database.database_manager import DatabaseManager


@dataclass(frozen=True)
class DashboardProjectionRecord:
    bucket: str
    stable_key: str
    record_type: str
    sort_order: int
    payload: dict


class DashboardProjectionRepository:
    def __init__(self, database_manager: type[DatabaseManager] = DatabaseManager) -> None:
        self._database_manager = database_manager

    def initialize(self) -> None:
        self._database_manager.initialize()

    def count_bucket(self, bucket: str) -> int:
        self.initialize()
        conn = self._database_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM dashboard_projection_records WHERE bucket = ?",
                (bucket,),
            )
            return int(cursor.fetchone()[0])
        finally:
            conn.close()

    def insert_records_if_empty(self, bucket: str, records: Iterable[DashboardProjectionRecord]) -> bool:
        self.initialize()
        conn = self._database_manager.get_connection()
        try:
            existing = conn.execute(
                "SELECT COUNT(*) FROM dashboard_projection_records WHERE bucket = ?",
                (bucket,),
            ).fetchone()[0]
            if existing:
                return False

            conn.executemany(
                """
                INSERT INTO dashboard_projection_records
                    (bucket, stable_key, record_type, sort_order, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.bucket,
                        record.stable_key,
                        record.record_type,
                        record.sort_order,
                        json.dumps(record.payload, ensure_ascii=False, sort_keys=True),
                    )
                    for record in records
                ],
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def list_bucket(self, bucket: str) -> list[DashboardProjectionRecord]:
        self.initialize()
        conn = self._database_manager.get_connection()
        conn.row_factory = sqlite_row_factory
        try:
            rows = conn.execute(
                """
                SELECT bucket, stable_key, record_type, sort_order, payload_json
                FROM dashboard_projection_records
                WHERE bucket = ?
                ORDER BY record_type, sort_order, stable_key
                """,
                (bucket,),
            ).fetchall()
            return [
                DashboardProjectionRecord(
                    bucket=row["bucket"],
                    stable_key=row["stable_key"],
                    record_type=row["record_type"],
                    sort_order=int(row["sort_order"]),
                    payload=json.loads(row["payload_json"]),
                )
                for row in rows
            ]
        finally:
            conn.close()


def sqlite_row_factory(cursor, row):
    return {description[0]: row[index] for index, description in enumerate(cursor.description)}
