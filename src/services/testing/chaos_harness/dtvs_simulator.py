import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Set, Optional

# --- 1. CORE TYPES ---
@dataclass
class NetworkMessage:
    sender: str
    receiver: str
    payload: Any
    msg_type: str  # event / signature / sync
    timestamp: float = field(default_factory=time.time)


# --- 2. NETWORK EMULATOR (CHAOS LAYER) ---
class NetworkEmulator:
    def __init__(self, drop_rate=0.0, latency=(0.0, 0.0), seed=42):
        self.drop_rate = drop_rate
        self.latency = latency
        self.partitions: Dict[str, Set[str]] = {}
        self.rng = random.Random(seed)

    def partition(self, group_a: Set[str], group_b: Set[str]):
        for a in group_a:
            for b in group_b:
                self.partitions.setdefault(a, set()).add(b)
                self.partitions.setdefault(b, set()).add(a)

    def can_deliver(self, sender, receiver):
        if sender in self.partitions.get(receiver, set()):
            return False
        return True

    async def transmit(self, msg: NetworkMessage, deliver_fn):
        if self.rng.random() < self.drop_rate:
            return  # dropped

        delay = self.rng.uniform(*self.latency)
        await asyncio.sleep(delay)

        if self.can_deliver(msg.sender, msg.receiver):
            await deliver_fn(msg)


# --- 3. CDML NODE SIMULATOR ---
class CDMLNode:
    def __init__(self, node_id, runtime, network, nodes_registry):
        self.id = node_id
        self.runtime = runtime
        self.network = network
        self.nodes_registry = nodes_registry
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.state_log = []
        self.running = True

    async def send(self, target, msg):
        await self.network.transmit(
            NetworkMessage(self.id, target, msg, "event"),
            deliver_fn=lambda m: self.nodes_registry[m.receiver].inbox.put_nowait(m)
        )

    async def process_inbox(self):
        while self.running:
            msg = await self.inbox.get()
            if hasattr(self.runtime, "handle_message"):
                await self.runtime.handle_message(msg.payload, self.id)

    async def run(self):
        asyncio.create_task(self.process_inbox())


# --- 4. BYZANTINE INJECTOR ---
class ByzantineInjector:
    def __init__(self, intensity=0.1, seed=42):
        self.rng = random.Random(seed)
        self.intensity = intensity

    def corrupt_event(self, event: dict):
        if self.rng.random() < self.intensity:
            event["payload"]["tampered"] = True
            event["epoch"] = -999  # invalid epoch
        return event


# --- 5. DETERMINISTIC EVENT SCHEDULER ---
class DeterministicClock:
    def __init__(self):
        self.tick = 0

    async def step(self):
        await asyncio.sleep(0)
        self.tick += 1
        return self.tick


# --- 6. CHAOS CONTROLLER ---
class ChaosController:
    def __init__(self, nodes, bridge=None):
        self.nodes = nodes
        self.clock = DeterministicClock()
        self.bridge = bridge

    async def emit_event(self, event: dict):
        if self.bridge:
            await self.bridge.broadcast({
                "type": "dag_event",
                "event_hash": event["event_hash"],
                "epoch": event["epoch"],
                "status": event["status"],
                "parents": event.get("parent_hashes", []),
                "node_id": event["node_id"]
            })

    async def broadcast(self, sender, event):
        for node_id, node in self.nodes.items():
            if node_id != sender:
                await self.nodes[sender].send(node_id, event)

    async def run_ticks(self, steps=100):
        for _ in range(steps):
            tick = await self.clock.step()
            for node in self.nodes.values():
                if hasattr(node.runtime, "on_tick"):
                    await node.runtime.on_tick(tick)


# --- 7. CONSISTENCY VERIFIER ---
class ConsistencyChecker:
    def __init__(self, nodes):
        self.nodes = nodes

    def check_convergence(self):
        states = [n.runtime.state_hash() for n in self.nodes.values() if hasattr(n.runtime, "state_hash")]
        return len(set(states)) == 1 if states else True

    def check_no_double_commit(self):
        seen = set()
        for n in self.nodes.values():
            if hasattr(n.runtime, "committed_events"):
                for e in n.runtime.committed_events():
                    if e in seen:
                        return False
                    seen.add(e)
        return True
