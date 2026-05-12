class CrossVoucherValidator:
    def validate(self, vouchers: list):
        issues = []
        total_usage = sum(v.get("net", 0) for v in vouchers)
        budgets = set(v.get("budget_line", "") for v in vouchers if v.get("budget_line"))

        # Cross-budget anomaly check
        if len(budgets) > 1 and total_usage > 1000000:
            issues.append("CROSS_BUDGET_OVERLOAD")

        # Duplicate payment detection
        seen = set()
        for v in vouchers:
            vendor = v.get("vendor", "")
            amount = v.get("amount", 0)
            if not vendor:
                continue
            key = (vendor, amount)
            if key in seen:
                issues.append("POSSIBLE_DUPLICATE_PAYMENT")
            seen.add(key)

        return issues
