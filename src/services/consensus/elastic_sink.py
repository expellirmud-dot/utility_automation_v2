"""
Elasticsearch Sink for CDML State Projection.
Follows CQRS: Write (Causal DAG) is separated from Read (Elasticsearch).
"""
import json
import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import httpx
import os
import hashlib
import time


@dataclass
class ElasticSinkConfig:
    host: str = field(default_factory=lambda: os.getenv("ELASTIC_HOST", "http://localhost:9200"))
    index_events: str = "cdml_events"
    index_state: str = "cdml_state"
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("ELASTIC_API_KEY", None))


class ElasticsearchSink:
    """
    Pushes committed CausalEvents and projected State into Elasticsearch.
    This is the Read Model of CQRS — never mutate state directly here.

    INVARIANT: Only COMMITTED events are ever indexed.
    """

    def __init__(self, config: Optional[ElasticSinkConfig] = None):
        self.cfg = config or ElasticSinkConfig()
        self._headers = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            self._headers["Authorization"] = f"ApiKey {self.cfg.api_key}"

    # -------------------------------------------------------
    async def index_committed_event(self, event) -> bool:
        """
        Called by CDMLRuntime after FinalizerKernel commits an event.
        Maps CausalEvent → Elasticsearch document.
        """
        if event.quorum_state.phase != "COMMITTED":
            # Hard guard: never index uncommitted events
            return False

        doc = {
            "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_hash": event.event_hash,
            "epoch": event.epoch,
            "phase": event.quorum_state.phase,
            "payload": event.payload,
            "parent_hashes": list(event.parent_hashes),
            "quorum_signatures": list(event.quorum_state.signatures.keys()),
        }

        url = f"{self.cfg.host}/{self.cfg.index_events}/_doc/{event.event_hash}"
        return await self._put(url, doc)

    # -------------------------------------------------------
    async def snapshot_state(self, epoch: int, projected_state: Dict[str, Any]) -> bool:
        """
        Publishes a full StateProjector snapshot for a given epoch.
        Used for Dashboard read model — latest state per epoch.
        """
        snapshot_id = f"epoch-{epoch}"
        doc = {
            "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "epoch": epoch,
            "state": projected_state,
        }

        url = f"{self.cfg.host}/{self.cfg.index_state}/_doc/{snapshot_id}"
        return await self._put(url, doc)

    # -------------------------------------------------------
    async def _put(self, url: str, doc: Dict) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.put(url, content=json.dumps(doc), headers=self._headers)
                return resp.status_code in (200, 201)
        except Exception as e:
            # Fail gracefully — Elastic unavailability must not block governance execution
            print(f"[ElasticSink] WARNING: Could not index document: {e}")
            return False

    # -------------------------------------------------------
    async def ensure_indices(self):
        """Creates indices with proper mappings if they don't exist."""
        events_mapping = {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "event_hash": {"type": "keyword"},
                    "epoch": {"type": "integer"},
                    "phase": {"type": "keyword"},
                    "payload": {"type": "object"},
                    "parent_hashes": {"type": "keyword"},
                }
            }
        }
        state_mapping = {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "epoch": {"type": "integer"},
                    "state": {"type": "object"},
                }
            }
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            for idx, mapping in [
                (self.cfg.index_events, events_mapping),
                (self.cfg.index_state, state_mapping),
            ]:
                url = f"{self.cfg.host}/{idx}"
                try:
                    resp = await client.head(url, headers=self._headers)
                    if resp.status_code == 404:
                        await client.put(url, content=json.dumps(mapping), headers=self._headers)
                        print(f"[ElasticSink] Created index: {idx}")
                except Exception as e:
                    print(f"[ElasticSink] WARNING: Could not create index {idx}: {e}")
