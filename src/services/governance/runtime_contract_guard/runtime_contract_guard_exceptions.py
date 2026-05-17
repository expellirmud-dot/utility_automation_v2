class RuntimeContractGuardError(Exception):
    """Base exception for Runtime Contract Guard errors."""
    pass

class GuardBlockedError(RuntimeContractGuardError):
    """Raised when the guard explicitly blocks execution."""
    pass

class ContractNotFoundError(GuardBlockedError):
    """Raised when the required execution contract file is missing."""
    pass

class ContractInvalidError(GuardBlockedError):
    """Raised when the contract is structurally invalid or expired."""
    pass

class IdentityMismatchError(GuardBlockedError):
    """Raised when task_id or actor_id do not match."""
    pass

class ScopeViolationError(GuardBlockedError):
    """Raised when a requested action violates the contract scope."""
    pass
