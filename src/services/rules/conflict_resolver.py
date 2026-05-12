class ConflictResolver:

    EFFECT_PRIORITY = {
        "DENY": 100,
        "ESCALATE": 90,
        "ALLOW": 10
    }

    def resolve(self, matched_rules):

        if not matched_rules:
            return None

        # highest priority rule wins
        matched_rules = sorted(
            matched_rules,
            key=lambda r: (
                r.priority,
                self.EFFECT_PRIORITY[r.effect]
            ),
            reverse=True
        )

        return matched_rules[0]
