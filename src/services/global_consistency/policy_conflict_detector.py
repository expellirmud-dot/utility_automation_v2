class PolicyConflictDetector:
    def detect(self, rules: list):
        conflicts = []

        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                r1 = rules[i]
                r2 = rules[j]

                # simple contradiction check
                if r1.get("type") == "APPROVAL_LIMIT" and r2.get("type") == "APPROVAL_LIMIT":
                    if r1.get("value") != r2.get("value"):
                        conflicts.append({
                            "rule_a": r1.get("id"),
                            "rule_b": r2.get("id"),
                            "type": "CONFLICT_LIMIT"
                        })

        return conflicts
