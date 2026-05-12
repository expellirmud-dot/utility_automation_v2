from src.services.governance.rule_versioning import RuleVersioningSystem
from src.services.governance.audit_engine import AuditDecisionEngine
from src.services.governance.regression_system import SemanticRegressionSystem
from src.models.governance.schemas import RuleDefinition, RegressionReport
from typing import Dict, Any, Callable, Optional

class GovernanceController:
    def __init__(self):
        self.rule_system = RuleVersioningSystem()
        self.audit_engine = AuditDecisionEngine()
        self.regression_system = SemanticRegressionSystem()

    def create_rule(self, rule_id: str, version: str, description: str, logic_params: Dict[str, Any]) -> RuleDefinition:
        return self.rule_system.create_rule(rule_id, version, description, logic_params)

    def deactivate_rule(self, rule_id: str, version: str):
        self.rule_system.deactivate_rule(rule_id, version)

    def get_active_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        return self.rule_system.get_active_rule(rule_id)

    def log_decision(self, trace_id: str, step_name: str, input_data: dict, rule_used: str, rule_version: str, decision: str, reason_code: str):
        return self.audit_engine.log_step(trace_id, step_name, input_data, rule_used, rule_version, decision, reason_code)

    def run_regression(self, evaluator_func: Callable, old_version: str, new_version: str, rule_id: str) -> RegressionReport:
        old_rule = self.rule_system.get_rule(rule_id, old_version)
        new_rule = self.rule_system.get_rule(rule_id, new_version)
        if not old_rule or not new_rule:
            raise ValueError("Rule version not found")
        return self.regression_system.compare_rules(evaluator_func, old_rule, new_rule)

    def can_deploy(self, regression_report: RegressionReport) -> bool:
        # A simple deployment gate
        return regression_report.can_deploy
