class SystemReconciler:
    def reconcile(self, global_state, event_store):
        corrections = []

        # rebuild truth from event store
        reconstructed_budget = 0
        for e in event_store.get_all():
            if e.event_type == "DECISION_MADE":
                payload = e.payload
                # Check for nested structure or direct access
                if "semantic_result" in payload:
                    # from TASK 016
                    semantic_res = payload["semantic_result"]
                    if "voucher" in semantic_res and "financials" in semantic_res["voucher"]:
                        net_amount = semantic_res["voucher"]["financials"].get("net", 0)
                    else:
                        net_amount = 0
                else:
                    net_amount = payload.get("net", 0)

                reconstructed_budget += net_amount

        if reconstructed_budget != global_state.used_budget:
            corrections.append({
                "type": "BUDGET_MISMATCH",
                "expected": reconstructed_budget,
                "actual": global_state.used_budget
            })

        return corrections
