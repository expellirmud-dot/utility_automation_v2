from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.services.web_control.event_stream import EventStream
from src.services.web_control.dashboard_api import WebDashboardAPI
from src.services.web_control.control_actions import ControlActions

app = FastAPI(title="Control Plane Web Dashboard")
event_stream = EventStream()

# Dummy Control Plane to represent the backend infrastructure
class DummyControlPlane:
    def get_state(self): return {"system_status": "STABLE", "health": 0.9}
    def override(self, d, a): return {"overridden": True, "id": d, "action": a}
    def set_threshold(self, v): return {"threshold": v}
    def pause_healing(self): return {"paused": True}
    def resume_healing(self): return {"resumed": True}
    def rollback(self, v): return {"rolled_back": v}

control_plane = DummyControlPlane()
api = WebDashboardAPI(control_plane)
actions = ControlActions(control_plane)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    event_stream.subscribe(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Simplistic handling of remote commands over WS
            if data == "pause":
                res = actions.pause_healing()
                await websocket.send_text(str(res))
            elif data == "resume":
                res = actions.resume_healing()
                await websocket.send_text(str(res))
    except WebSocketDisconnect:
        event_stream.unsubscribe(websocket)

@app.get("/api/state")
def get_state():
    return api.get_state()

@app.post("/api/override")
def override_decision(decision_id: str, action: str):
    return api.override_decision(decision_id, action)

@app.post("/api/healing/pause")
def pause_healing():
    return actions.pause_healing()

@app.post("/api/healing/resume")
def resume_healing():
    return actions.resume_healing()

@app.post("/api/healing/rollback")
def rollback(version: str):
    return actions.rollback(version)
