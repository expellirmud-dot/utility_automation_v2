class ControlPlaneOrchestrator:
    def __init__(self, analyzer, intent, noise, budget, scorer, engine):
        self.analyzer = analyzer
        self.intent = intent
        self.noise = noise
        self.budget = budget
        self.scorer = scorer
        self.engine = engine

    def control(self, telemetry, history, signals):
        metrics = self.analyzer.analyze(telemetry)

        intent = self.intent.detect(history)

        noise = self.noise.detect(signals)

        budget_ok = self.budget.allow()

        score = self.scorer.score(metrics)

        decision = self.engine.decide(
            score,
            intent,
            noise,
            budget_ok
        )

        return {
            "decision": decision,
            "score": score,
            "intent": intent,
            "noise": noise
        }
