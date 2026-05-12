class DecisionTimelineEngine:
    def build(self, event_log):
        timeline = []

        for e in event_log:
            timeline.append({
                "timestamp": e.get("ts"),
                "component": e.get("component"),
                "action": e.get("action"),
                "decision": e.get("decision"),
                "reason": e.get("reason")
            })

        return sorted(timeline, key=lambda x: x["timestamp"])
