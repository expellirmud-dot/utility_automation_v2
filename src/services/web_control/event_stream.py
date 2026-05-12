import json

class EventStream:
    def __init__(self):
        self.subscribers = []

    async def publish(self, event):
        message = json.dumps(event)
        
        # Use a copy of the list so we can remove safely if needed
        for sub in list(self.subscribers):
            try:
                await sub.send_text(message)
            except Exception:
                self.subscribers.remove(sub)

    def subscribe(self, websocket):
        if websocket not in self.subscribers:
            self.subscribers.append(websocket)
            
    def unsubscribe(self, websocket):
        if websocket in self.subscribers:
            self.subscribers.remove(websocket)
