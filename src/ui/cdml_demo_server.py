"""
CDML Demo Server - Stage 5: Adversarial Reality Mode
Adds: Byzantine injection, network partition, node crash, clock drift, stochastic chaos
Run: python cdml_demo_server.py
"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import time
import hashlib
import random
import json
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import pathlib

# ── In-memory stores ──────────────────────────────────────────────────────────
committed_events: List[Dict] = []
rejected_events: List[Dict] = []     # Byzantine/fork-rejected events
chaos_log: List[Dict] = []           # Fault injection trace

# ── Adversarial State ─────────────────────────────────────────────────────────
@dataclass
class AdversarialState:
    # Node health: node_id -> "alive" | "crashed" | "byzantine" | "partitioned"
    node_status: Dict[str, str] = field(default_factory=lambda: {
        "node-1": "alive", "node-2": "alive", "node-3": "alive"
    })
    # Partition groups: nodes that cannot see each other
    partitioned_pairs: List[tuple] = field(default_factory=list)
    # Byzantine nodes actively injecting bad events
    byzantine_nodes: List[str] = field(default_factory=list)
    # Current chaos mode
    chaos_mode: str = "NORMAL"       # NORMAL | PARTITION | BYZANTINE | CRASH | RECOVERY
    # Quorum threshold (can be corrupted)
    quorum_threshold: int = 2
    # Pending/limbo events (quorum not yet reached)
    pending_quorum: List[Dict] = field(default_factory=list)
    # Crash recovery events
    recovery_log: List[Dict] = field(default_factory=list)

adversarial = AdversarialState()

# ── Constants ─────────────────────────────────────────────────────────────────
ACTIONS = [
    "approve_voucher", "reject_request", "validate_identity",
    "audit_transaction", "grant_permission", "revoke_access",
    "sync_ledger", "seal_epoch",
]
NODES = ["node-1", "node-2", "node-3"]

def _make_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

# ── Event Factory ─────────────────────────────────────────────────────────────
def make_event(epoch: int, parent_hashes: List[str], node_id: str,
               phase: str = "COMMITTED", tampered: bool = False,
               event_type: str = "normal") -> Dict:
    payload = {
        "action": random.choice(ACTIONS),
        "identity_id": f"user-{random.randint(100, 999)}",
        "amount": random.randint(100, 50000),
    }
    if tampered:
        payload["__byzantine__"] = True
        payload["forged_signature"] = "INVALID_SIG_" + str(random.randint(1000, 9999))

    content = f"{node_id}:{json.dumps(payload, sort_keys=True)}:{sorted(parent_hashes)}:{epoch}"
    event_hash = _make_hash(content)

    return {
        "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_hash": event_hash,
        "epoch": epoch,
        "phase": phase,
        "payload": payload,
        "parent_hashes": parent_hashes,
        "node_id": node_id,
        "event_type": event_type,    # normal | byzantine | crash_recovered | fork_rejected
        "quorum_signatures": [],
        "causal_depth": len(parent_hashes),
    }

def compute_projected_state(events: List[Dict]) -> Dict:
    state: Dict[str, Any] = {
        "status": "operational",
        "actions_executed": 0,
        "last_action": None,
        "approved": 0,
        "rejected": 0,
        "current_epoch": 1,
    }
    for ev in events:
        if ev["phase"] != "COMMITTED":
            continue
        action = ev["payload"].get("action", "")
        state["actions_executed"] += 1
        state["last_action"] = action
        state["current_epoch"] = max(state["current_epoch"], ev.get("epoch", 1))
        if "approve" in action:
            state["approved"] += 1
        elif "reject" in action or "revoke" in action:
            state["rejected"] += 1
    return state

# ── Chaos Mode Controllers ────────────────────────────────────────────────────
async def inject_network_partition():
    """Split cluster into 51/49 — majority keeps committing, minority stalls"""
    adversarial.chaos_mode = "PARTITION"
    adversarial.node_status["node-3"] = "partitioned"
    adversarial.partitioned_pairs = [("node-3", "node-1"), ("node-3", "node-2")]
    _log_chaos("PARTITION", "node-3 isolated (minority side)", severity="HIGH")
    print("[CHAOS] NETWORK PARTITION: node-3 isolated from majority")

async def heal_partition():
    adversarial.chaos_mode = "RECOVERY"
    adversarial.node_status["node-3"] = "alive"
    adversarial.partitioned_pairs = []
    _log_chaos("HEAL", "Partition healed, node-3 rejoining", severity="INFO")
    print("[CHAOS] PARTITION HEALED: node-3 reconnecting")

async def inject_byzantine_node():
    """Make node-2 start injecting invalid events"""
    adversarial.chaos_mode = "BYZANTINE"
    adversarial.node_status["node-2"] = "byzantine"
    adversarial.byzantine_nodes = ["node-2"]
    _log_chaos("BYZANTINE", "node-2 compromised, sending forged events", severity="CRITICAL")
    print("[CHAOS] BYZANTINE: node-2 is now injecting forged events")

async def recover_byzantine_node():
    adversarial.node_status["node-2"] = "alive"
    adversarial.byzantine_nodes = []
    adversarial.chaos_mode = "NORMAL"
    _log_chaos("RECOVERY", "node-2 isolated and restored", severity="INFO")
    print("[CHAOS] RECOVERY: node-2 expelled and system stabilized")

async def inject_node_crash(node_id: str = "node-1"):
    adversarial.chaos_mode = "CRASH"
    adversarial.node_status[node_id] = "crashed"
    _log_chaos("CRASH", f"{node_id} crashed mid-operation", severity="HIGH")
    print(f"[CHAOS] CRASH: {node_id} went offline")

async def recover_crashed_node(node_id: str = "node-1"):
    adversarial.node_status[node_id] = "alive"
    if adversarial.chaos_mode == "CRASH":
        adversarial.chaos_mode = "RECOVERY"
    _log_chaos("RECOVERY", f"{node_id} restarted, beginning LCA sync", severity="INFO")
    print(f"[CHAOS] RECOVERY: {node_id} back online")

def _log_chaos(fault_type: str, detail: str, severity: str = "INFO"):
    chaos_log.append({
        "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fault_type": fault_type,
        "detail": detail,
        "severity": severity,
        "chaos_mode": adversarial.chaos_mode,
        "node_statuses": dict(adversarial.node_status),
    })

# ── Main Event Clock (Adversarial Mode) ───────────────────────────────────────
async def adversarial_event_clock():
    epoch = 1
    frontier: List[str] = []
    tick = 0

    print("[CDML Clock] STAGE 5 ADVERSARIAL EVENT STIMULUS STARTED")

    # Schedule chaos scenarios
    asyncio.create_task(_chaos_scheduler())

    while True:
        # Non-deterministic delay (0.5–3s) to simulate stochastic timing
        delay = random.uniform(0.5, 2.5)
        await asyncio.sleep(delay)
        tick += 1

        # Advance epoch every 8 events
        if len(committed_events) > 0 and len(committed_events) % 8 == 0:
            epoch += 1
            print(f"[CDML Clock] EPOCH ADVANCED -> {epoch}")

        # Pick an alive node
        alive_nodes = [n for n, s in adversarial.node_status.items() if s == "alive"]
        if not alive_nodes:
            print("[CDML Clock] NO ALIVE NODES — system halted safely")
            await asyncio.sleep(1)
            continue

        node_id = random.choice(alive_nodes)

        # Fork probability increases under chaos
        fork_prob = 0.4 if adversarial.chaos_mode != "NORMAL" else 0.2
        parents = frontier[-2:] if len(frontier) >= 2 and random.random() < fork_prob else frontier[-1:]

        # Byzantine event injection
        if node_id in adversarial.byzantine_nodes:
            byz_event = make_event(epoch, parents, node_id,
                                   phase="REJECTED_BYZANTINE", tampered=True,
                                   event_type="byzantine")
            rejected_events.append(byz_event)
            _log_chaos("BYZANTINE_INJECT", f"Forged event from {node_id} rejected by validator",
                       severity="CRITICAL")
            print(f"[CHAOS] BYZANTINE EVENT REJECTED from {node_id}: {byz_event['event_hash'][:12]}...")
            continue

        # Partition: partitioned node cannot contribute
        is_partitioned = any(
            node_id in pair for pair in adversarial.partitioned_pairs
        )
        if is_partitioned:
            # Event goes into limbo (QUORUM_PENDING — not enough signatures)
            limbo_event = make_event(epoch, parents, node_id,
                                     phase="QUORUM_PENDING", event_type="partitioned")
            adversarial.pending_quorum.append(limbo_event)
            print(f"[CHAOS] PARTITION STALL: {node_id} event stuck in QUORUM_PENDING")
            continue

        # Normal path: commit event
        event = make_event(epoch, parents, node_id,
                           phase="COMMITTED", event_type="normal")

        # Quorum signatures (only from alive, non-partitioned nodes)
        signers = [n for n, s in adversarial.node_status.items()
                   if s == "alive" and not any(n in pair for pair in adversarial.partitioned_pairs)]
        event["quorum_signatures"] = [f"sig:{n}" for n in signers]

        committed_events.append(event)
        frontier.append(event["event_hash"])
        if len(frontier) > 20:
            frontier = frontier[-20:]

        # Flush pending_quorum after partition heals
        if adversarial.chaos_mode == "RECOVERY" and adversarial.pending_quorum:
            pending = adversarial.pending_quorum.pop(0)
            pending["phase"] = "COMMITTED"
            pending["event_type"] = "crash_recovered"
            committed_events.append(pending)
            print(f"[CHAOS] RECOVERY FLUSH: pending event now committed after LCA sync")

        state = compute_projected_state(committed_events)

async def _chaos_scheduler():
    """Fires chaos scenarios at timed intervals"""
    await asyncio.sleep(15)   # Normal operation first
    await inject_network_partition()
    await asyncio.sleep(20)   # Let partition run
    await heal_partition()
    await asyncio.sleep(10)   # Stabilize
    await inject_byzantine_node()
    await asyncio.sleep(15)   # Byzantine attack window
    await recover_byzantine_node()
    await asyncio.sleep(10)
    await inject_node_crash("node-1")
    await asyncio.sleep(12)
    await recover_crashed_node("node-1")
    # Loop
    await asyncio.sleep(30)
    asyncio.create_task(_chaos_scheduler())

# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(title="CDML Demo Server - Adversarial Stage 5")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/events")
def get_events(size: int = 50):
    return {"hits": {"hits": [{"_source": e} for e in reversed(committed_events[-size:])]}}

@app.get("/rejected")
def get_rejected():
    return {"events": rejected_events[-20:]}

@app.get("/state")
def get_state():
    if not committed_events:
        return {"status": "initialized", "actions_executed": 0}
    return compute_projected_state(committed_events)

@app.get("/chaos")
def get_chaos_status():
    return {
        "chaos_mode": adversarial.chaos_mode,
        "node_status": adversarial.node_status,
        "byzantine_nodes": adversarial.byzantine_nodes,
        "partitioned_pairs": adversarial.partitioned_pairs,
        "pending_quorum": len(adversarial.pending_quorum),
        "chaos_log": chaos_log[-20:],
        "byzantine_rejected": len(rejected_events),
        "total_committed": len(committed_events),
    }

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "cdml-adversarial-stage5", "events": len(committed_events)}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = pathlib.Path(__file__).parent / "cdml_dashboard.html"
    if html_path.exists():
        content = html_path.read_text(encoding="utf-8")
        content = content.replace('const DEMO_URL = "http://localhost:8000";', 'const DEMO_URL = "";')
        return HTMLResponse(content=content)
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(adversarial_event_clock())
    yield

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    print("[CDML] Adversarial Stage 5 Server starting on http://localhost:8000")
    print("[CDML] Dashboard: http://localhost:8000/")
    print("[CDML] Chaos Status: http://localhost:8000/chaos")
    uvicorn.run("cdml_demo_server:app", host="0.0.0.0", port=8000, log_level="warning",
                app_dir=str(pathlib.Path(__file__).parent))
