class BudgetConstraintEngine:
    def validate(self, global_state):
        issues = []

        if global_state.used_budget > global_state.total_budget:
            issues.append("BUDGET_EXCEEDED")

        if global_state.remaining_budget() < 0:
            issues.append("NEGATIVE_BUDGET_STATE")

        return issues
