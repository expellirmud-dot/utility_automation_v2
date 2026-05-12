class RuleRegistry:

    def __init__(self):

        self.rules = []

    def register(self, rule):

        self.rules.append(rule)

    def all_rules(self):

        return sorted(
            self.rules,
            key=lambda r: r.priority,
            reverse=True
        )
