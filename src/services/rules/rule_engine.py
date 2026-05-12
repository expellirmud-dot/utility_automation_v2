from .rule_matcher import RuleMatcher
from .conflict_resolver import ConflictResolver

class RuleEngine:

    def __init__(self, registry):

        self.registry = registry
        self.matcher = RuleMatcher()
        self.resolver = ConflictResolver()

    def evaluate(self,
                 role,
                 action,
                 system_state):

        matched = []

        for rule in self.registry.all_rules():

            if self.matcher.match(
                rule,
                role,
                action,
                system_state
            ):
                matched.append(rule)

        decision = self.resolver.resolve(matched)
        
        if not decision:
            return {
                "decision": "DENY",
                "rule_id": "DEFAULT_DENY",
                "rule_name": "DefaultDenyFallback",
                "priority": 0
            }

        return {
            "decision": decision.effect,
            "rule_id": decision.rule_id,
            "rule_name": decision.name,
            "priority": decision.priority
        }
