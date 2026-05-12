from src.services.global_consistency.cross_voucher_validator import CrossVoucherValidator
from src.services.global_consistency.budget_constraint_engine import BudgetConstraintEngine
from src.services.global_consistency.policy_conflict_detector import PolicyConflictDetector
from src.services.global_consistency.system_reconciler import SystemReconciler

class GlobalConsistencyEngine:
    def __init__(self):
        self.cross_validator = CrossVoucherValidator()
        self.budget_engine = BudgetConstraintEngine()
        self.policy_detector = PolicyConflictDetector()
        self.reconciler = SystemReconciler()

    def validate_system(self, global_state, vouchers, rules, event_store):
        issues = []

        # 1. Cross-voucher check
        issues += self.cross_validator.validate(vouchers)

        # 2. Budget check
        issues += self.budget_engine.validate(global_state)

        # 3. Policy conflict
        issues += self.policy_detector.detect(rules)

        # 4. Reconciliation check
        issues += self.reconciler.reconcile(global_state, event_store)

        return {
            "status": "PASS" if len(issues) == 0 else "FAIL",
            "issues": issues
        }
