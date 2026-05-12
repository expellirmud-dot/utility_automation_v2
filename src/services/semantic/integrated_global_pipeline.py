from src.services.global_consistency.global_consistency_engine import GlobalConsistencyEngine

class GlobalPipeline:
    def __init__(self, pipeline, governance, event_service):
        self.pipeline = pipeline
        self.governance = governance
        self.event_service = event_service
        self.global_engine = GlobalConsistencyEngine()

    def process_batch(self, vouchers, rules, global_state):
        results = []

        # Process each voucher individually
        for v in vouchers:
            results.append(self.pipeline.process(v))

        # GLOBAL VALIDATION STEP
        global_check = self.global_engine.validate_system(
            global_state,
            vouchers,
            rules,
            self.event_service.store
        )

        return {
            "voucher_results": results,
            "global_validation": global_check
        }
