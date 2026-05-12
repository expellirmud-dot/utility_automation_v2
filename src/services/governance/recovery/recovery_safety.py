"""
Recovery Safety Gate via AST Analysis.

Enforces fail-closed safety by detecting forbidden symbols in recovery code.
Prevents:
- append_event, commit_event, write_ledger
- promote, submit_critical_event, submit_recovery_proposal
- MeshOrchestrator mutation calls
- Direct SQLite mutation outside projection repair

S1 only allows: detect, normalize, classify, plan construction, hash, proposal object building.
"""

import ast
import inspect
from typing import List, Set, Tuple


# Forbidden function/method names that could mutate state
FORBIDDEN_SYMBOLS = {
    # Ledger writes
    "append_event",
    "commit_event",
    "write_ledger",
    "submit_event",
    "record_event",
    
    # Policy promotion
    "promote",
    "promote_policy",
    "promote_stage",
    "stage_promotion",
    
    # Mesh/Quorum submission
    "submit_critical_event",
    "submit_recovery_proposal",
    "submit_proposal",
    "request_promotion",
    "request_quorum_action",
    "submit_to_mesh",
    "call_mesh",
    
    # SQLite direct writes (outside projection rebuild)
    "execute",
    "executemany",
    "insert",
    "update",
    "delete",
    "drop",
    "create_table",
}

# Allowed detection/analysis functions
ALLOWED_SYMBOLS = {
    "detect",
    "analyze",
    "classify",
    "normalize",
    "hash",
    "compute_hash",
    "stable_hash",
    "build",
    "create",
    "construct",
    "plan",
    "verify",
    "validate",
    "check",
}

# Forbidden module/class references
FORBIDDEN_MODULES = {
    "MeshOrchestrator",
    "QuorumAuthority",
}


class RecoverySafetyViolation(Exception):
    """Raised when safety constraints are violated."""
    pass


class SafetyGate(ast.NodeVisitor):
    """AST visitor that detects forbidden symbols."""

    def __init__(self):
        self.violations: List[str] = []
        self.forbidden_calls: List[Tuple[int, str]] = []
        self.forbidden_attributes: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call):
        """Detect forbidden function calls."""
        # Direct function call: f()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_SYMBOLS:
                self.forbidden_calls.append((node.lineno, func_name))
                self.violations.append(f"Line {node.lineno}: Forbidden call '{func_name}'")
        
        # Method call: obj.method()
        elif isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if method_name in FORBIDDEN_SYMBOLS:
                self.forbidden_calls.append((node.lineno, method_name))
                self.violations.append(f"Line {node.lineno}: Forbidden method '{method_name}'")
            
            # Check for forbidden class references
            if isinstance(node.func.value, ast.Name):
                class_name = node.func.value.id
                if class_name in FORBIDDEN_MODULES:
                    self.forbidden_attributes.append((node.lineno, f"{class_name}.{method_name}"))
                    self.violations.append(
                        f"Line {node.lineno}: Forbidden mutation via {class_name}.{method_name}"
                    )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Detect forbidden attribute access."""
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            if obj_name in FORBIDDEN_MODULES:
                self.forbidden_attributes.append((node.lineno, f"{obj_name}.{node.attr}"))
                self.violations.append(
                    f"Line {node.lineno}: Access to forbidden module/class {obj_name}"
                )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Detect forbidden imports."""
        for alias in node.names:
            if alias.name.split('.')[0] in FORBIDDEN_MODULES or 'mesh' in alias.name.lower():
                self.violations.append(f"Line {node.lineno}: Forbidden import {alias.name}")

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Detect forbidden from-imports."""
        if node.module:
            if node.module.split('.')[0] in FORBIDDEN_MODULES or 'mesh' in node.module.lower():
                for alias in node.names:
                    self.violations.append(
                        f"Line {node.lineno}: Forbidden import from {node.module}: {alias.name}"
                    )

        self.generic_visit(node)

    def verify_safety(self) -> bool:
        """Return True if no violations, False otherwise."""
        return len(self.violations) == 0


def check_recovery_code_safety(code: str) -> Tuple[bool, List[str]]:
    """
    Check if recovery code is safe.

    Args:
        code: Python code string

    Returns:
        (is_safe, violations_list)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]

    gate = SafetyGate()
    gate.visit(tree)

    return gate.verify_safety(), gate.violations


def check_recovery_function_safety(func) -> Tuple[bool, List[str]]:
    """
    Check if a recovery function is safe.

    Args:
        func: A callable function

    Returns:
        (is_safe, violations_list)
    """
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError) as e:
        return False, [f"Cannot inspect function: {e}"]

    return check_recovery_code_safety(source)


class SafeRecoveryProposalBuilder:
    """
    Safe builder that enforces recovery constraints.
    Only allows object construction, normalization, hashing.
    """

    def __init__(self):
        self.allowed_operations = {
            "normalize_signal",
            "classify_diagnosis",
            "plan_steps",
            "compute_hash",
            "build_proposal",
            "build_report",
            "validate_immutability",
        }

    def normalize_signal(self, signal):
        """Allowed: normalize a signal."""
        # Normalization is a read-only operation
        return signal

    def classify_diagnosis(self, diagnosis):
        """Allowed: classify a diagnosis."""
        # Classification doesn't mutate
        return diagnosis

    def plan_steps(self, steps):
        """Allowed: plan steps (returns new sorted tuple, doesn't mutate)."""
        return tuple(sorted(steps, key=lambda s: s.sort_key()))

    def compute_hash(self, obj):
        """Allowed: compute deterministic hash."""
        from src.services.governance.recovery.recovery_report_hasher import stable_hash
        return stable_hash(obj)

    def build_proposal(self, signal, diagnosis, plan, reason):
        """Allowed: build a proposal object (no mutations)."""
        from src.services.governance.recovery.recovery_models import RecoveryProposal
        return RecoveryProposal(
            signal=signal,
            diagnosis=diagnosis,
            plan=plan,
            reason_for_proposal=reason,
        )

    def build_report(self, proposal, ai_advice=None):
        """Allowed: build a report object (no mutations)."""
        from src.services.governance.recovery.recovery_models import RecoveryReport
        return RecoveryReport(proposal=proposal, ai_advice=ai_advice)

    def validate_immutability(self, obj):
        """Allowed: verify object is frozen."""
        if not hasattr(obj, '__dataclass_fields__'):
            raise ValueError(f"Object is not a dataclass: {type(obj)}")
        
        if not getattr(obj.__class__, '__dataclass_params__').frozen:
            raise ValueError(f"Object is not frozen: {type(obj)}")
        
        return True


def enforce_fail_closed():
    """
    Fail-closed enforcement: default to safe until proven otherwise.
    This decorator can wrap recovery functions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check code safety before execution
            is_safe, violations = check_recovery_function_safety(func)
            if not is_safe:
                raise RecoverySafetyViolation(
                    f"Function {func.__name__} failed safety check:\n" +
                    "\n".join(violations)
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
