class AutoOptimizer:
    def __init__(self, detector, generator, selector, simulator, gate):
        self.detector = detector
        self.generator = generator
        self.selector = selector
        self.simulator = simulator
        self.gate = gate

    def optimize(self, pipeline):
        bottlenecks = self.detector.get_latest()

        strategies = self.generator.generate(bottlenecks)

        best = self.selector.select_best(strategies)

        if not best:
            return {"status": "NO_OPTIMIZATION_AVAILABLE"}

        simulation = self.simulator.simulate(pipeline, best)

        if not self.gate.approve(simulation):
            return {
                "status": "REJECTED_BY_GOVERNANCE",
                "strategy": best
            }

        pipeline.apply_permanent_change(best)

        return {
            "status": "OPTIMIZED",
            "strategy": best,
            "improvement": simulation["improvement"]
        }
