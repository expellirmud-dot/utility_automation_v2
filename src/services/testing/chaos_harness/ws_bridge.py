import asyncio
import json
import websockets
from typing import Set, Dict, Any

class CDMLWebSocketBridge:
    """
    Real-time event broadcaster:
    ChaosController -> DAG Dashboard UI
    """

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set = set()

    async def register(self, websocket):
        self.clients.add(websocket)

    async def unregister(self, websocket):
        self.clients.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.clients:
            return

        payload = json.dumps(message)
        await asyncio.gather(
            *[client.send(payload) for client in self.clients],
            return_exceptions=True
        )

    async def handler(self, websocket):
        await self.register(websocket)
        try:
            async for _ in websocket:
                pass  # UI -> backend control (optional)
        finally:
            await self.unregister(websocket)

    async def start(self):
        return await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
