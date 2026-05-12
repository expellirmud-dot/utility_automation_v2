class DashboardAPI:
    def __init__(self, state, timeline, bottleneck, healing, scorer):
        self.state = state
        self.timeline = timeline
        self.bottleneck = bottleneck
        self.healing = healing
        self.scorer = scorer

    def render(self, telemetry, events, control_state, bottlenecks):
        state = self.state.build(telemetry, control_state, events)
        
        timeline = self.timeline.build(events.get("all", []))
        
        bottleneck = self.bottleneck.analyze(bottlenecks)
        
        healing = self.healing.summarize(events.get("healing", []))
        
        status, score = self.scorer.score(state)

        return {
            "system_status": status,
            "health_score": score,
            "state": state,
            "timeline": timeline,
            "bottlenecks": bottleneck,
            "healing": healing
        }
