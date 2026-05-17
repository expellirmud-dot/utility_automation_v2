class ContractError(Exception):
    """Base exception for all execution contract errors."""
    pass

class ContractValidationError(ContractError):
    """Raised when a contract is structurally invalid or fails policy checks."""
    pass

class ScopeViolationError(ContractError):
    """Raised when execution evidence exceeds the declared contract scope."""
    pass

class EvidenceValidationError(ContractError):
    """Raised when completion evidence is incomplete or mismatched with the contract."""
    pass
