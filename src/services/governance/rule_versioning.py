from typing import Dict, List, Optional, Any
from src.models.governance.schemas import RuleDefinition
from datetime import datetime

class RuleVersioningSystem:
    def __init__(self):
        # Store rules as rule_id -> list of RuleDefinition (historical versions)
        self.rules_db: Dict[str, List[RuleDefinition]] = {}

    def create_rule(self, rule_id: str, version: str, description: str, logic_params: Dict[str, Any]) -> RuleDefinition:
        if rule_id not in self.rules_db:
            self.rules_db[rule_id] = []
        
        # Check if version exists to avoid overwrite
        for rule in self.rules_db[rule_id]:
            if rule.version == version:
                raise ValueError(f"Rule version {version} already exists for {rule_id}")

        new_rule = RuleDefinition(
            rule_id=rule_id,
            version=version,
            description=description,
            logic_params=logic_params,
            status="ACTIVE"
        )
        self.rules_db[rule_id].append(new_rule)
        return new_rule

    def deactivate_rule(self, rule_id: str, version: str) -> None:
        rule = self.get_rule(rule_id, version)
        if rule:
            rule.status = "DEPRECATED"

    def get_rule(self, rule_id: str, version: str) -> Optional[RuleDefinition]:
        if rule_id in self.rules_db:
            for rule in self.rules_db[rule_id]:
                if rule.version == version:
                    return rule
        return None

    def get_active_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        # Return the latest active rule
        if rule_id in self.rules_db:
            active_rules = [r for r in self.rules_db[rule_id] if r.status == "ACTIVE"]
            if active_rules:
                # Sort by created_at desc (using index as a proxy if created_at is equal)
                active_rules.sort(key=lambda x: x.created_at, reverse=True)
                return active_rules[0]
        return None

    def rollback(self, rule_id: str, to_version: str) -> RuleDefinition:
        target = self.get_rule(rule_id, to_version)
        if not target:
            raise ValueError(f"Version {to_version} not found for {rule_id}")
        
        # Deactivate current active rules and activate the target
        if rule_id in self.rules_db:
            for rule in self.rules_db[rule_id]:
                if rule.status == "ACTIVE" and rule.version != to_version:
                    rule.status = "DEPRECATED"
        target.status = "ACTIVE"
        return target
