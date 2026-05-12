from typing import Dict, List, Callable, Any
from src.models.governance.schemas import RegressionReport, RuleDefinition

class SemanticRegressionSystem:
    def __init__(self):
        self.golden_dataset: List[Dict[str, Any]] = []

    def set_golden_dataset(self, dataset: List[Dict[str, Any]]):
        self.golden_dataset = dataset

    def compare_rules(self, evaluator_func: Callable, old_rule: RuleDefinition, new_rule: RuleDefinition) -> RegressionReport:
        total = len(self.golden_dataset)
        changed = 0
        diffs = []
        
        for case in self.golden_dataset:
            # evaluator_func takes (case, rule_params) and returns a result
            old_result = evaluator_func(case, old_rule.logic_params)
            new_result = evaluator_func(case, new_rule.logic_params)
            
            if old_result != new_result:
                changed += 1
                diffs.append({
                    "case_id": case.get("id", "unknown"),
                    "old_output": old_result,
                    "new_output": new_result
                })

        risk_score = (changed / total) * 100 if total > 0 else 0
        
        # Deployment Gate: If risk > 10%, block deploy (business requirement threshold)
        can_deploy = risk_score <= 10.0

        return RegressionReport(
            total_cases=total,
            changed_cases=changed,
            risk_score=risk_score,
            diff_summary=diffs,
            can_deploy=can_deploy
        )
