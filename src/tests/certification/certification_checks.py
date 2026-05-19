from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import ast
import os
from pathlib import Path
import subprocess
import sys

from src.services.event_sourcing.projection.state_projector import StateProjector
from src.services.mesh.mesh_orchestrator import MeshOrchestrator
from src.tests.certification.adversarial_fault_injector import AdversarialFaultInjector
from src.services.governance.certification.models import (
    CertificationCheck,
    CertificationFailure,
    CertificationResult,
)
from src.tests.certification.convergence_validator import ConvergenceValidator
from src.tests.certification.fork_resolution_tester import ForkResolutionTester
from src.tests.certification.quorum_integrity_tester import QuorumIntegrityTester
from src.tests.certification.replay_consistency_checker import ReplayConsistencyChecker
from src.tests.certification.security_dependency_checks import check_security_dependencies
from src.tests.certification.runtime_task_governance_checks import check_runtime_task_governance


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class RegisteredCertificationCheck:
    check: CertificationCheck
    run: Callable[[], CertificationResult]


def pass_result(check: CertificationCheck) -> CertificationResult:
    return CertificationResult(check=check, passed=True)


def fail_result(check: CertificationCheck, reason: str, detail: str = "") -> CertificationResult:
    return CertificationResult(
        check=check,
        passed=False,
        failure=CertificationFailure(check_key=check.key, reason=reason, detail=detail),
    )


def run_registered_checks() -> tuple[CertificationResult, ...]:
    results: list[CertificationResult] = []
    for registered in registered_checks():
        try:
            result = registered.run()
        except Exception as exc:
            result = fail_result(
                registered.check,
                reason="exception",
                detail=f"{exc.__class__.__name__}: {exc}",
            )
        results.append(result)
    return tuple(results)


def registered_checks() -> tuple[RegisteredCertificationCheck, ...]:
    return (
        _registered(10, "ledger_truth_invariant", "invariant", "Ledger remains the only source of truth.", _ledger_truth_invariant),
        _registered(20, "sqlite_projection_only_invariant", "invariant", "SQLite remains projection/cache only.", _sqlite_projection_only_invariant),
        _registered(30, "mesh_authority_invariant", "invariant", "Mesh quorum remains runtime authority.", _mesh_authority_invariant),
        _registered(40, "ai_advisory_only_invariant", "invariant", "AI remains advisory only.", _ai_advisory_only_invariant),
        _registered(50, "mesh_determinism", "validation", "Existing mesh deterministic certification checks pass.", _mesh_determinism),
        _registered(60, "pytest_pass", "validation", "Required non-certifier pytest safety suite passes.", _pytest_pass),
        _registered(70, "replay_determinism", "validation", "Replay determinism tests pass.", _replay_determinism),
        _registered(80, "projection_consistency", "validation", "Projection consistency tests pass.", _projection_consistency),
        _registered(90, "api_governance_get_only_ops", "validation", "Ops APIs remain GET-only.", _api_governance_get_only_ops),
        _registered(100, "frontend_governance_no_mutation_ui", "validation", "Frontend contains no mutation UI.", _frontend_governance_no_mutation_ui),
        _registered(110, "security_dependency_governance", "validation", "Security risks are registered and no unauthorized breaking upgrades exist.", _security_dependency_check),
        _registered(120, "runtime_task_governance_invariant", "invariant", "Runtime tasks adhere to contract governance.", _runtime_task_governance_invariant),
    )


def _registered(
    stable_order: int,
    key: str,
    category: str,
    description: str,
    run: Callable[[CertificationCheck], CertificationResult],
) -> RegisteredCertificationCheck:
    check = CertificationCheck(
        key=key,
        category=category,
        description=description,
        stable_order=stable_order,
    )
    return RegisteredCertificationCheck(check=check, run=lambda: run(check))


def _ledger_truth_invariant(check: CertificationCheck) -> CertificationResult:
    required_texts = (
        (REPO_ROOT / "PROJECT_RULES.md", "Ledger is the only source of truth"),
        (REPO_ROOT / "AI_HANDOFF.md", "Ledger is sole source of truth"),
        (REPO_ROOT / ".serena" / "memories" / "architecture.md", "Ledger is sole source of truth"),
    )
    for path, needle in required_texts:
        if needle not in _read_text(path):
            return fail_result(check, "missing_ledger_truth_statement", _relative(path))
    return pass_result(check)


def _sqlite_projection_only_invariant(check: CertificationCheck) -> CertificationResult:
    projection_reader = REPO_ROOT / "src" / "projections" / "db_projection_reader.py"
    source = _read_text(projection_reader)
    required = (
        "mode=ro",
        "\"projection_only\": True",
        "\"database_role\": \"cache_projection\"",
        "\"source_of_truth\": \"ledger\"",
    )
    for needle in required:
        if needle not in source:
            return fail_result(check, "projection_reader_contract_missing", needle)
    forbidden_sql = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE")
    upper_source = source.upper()
    for keyword in forbidden_sql:
        if keyword in upper_source:
            return fail_result(check, "mutation_sql_in_projection_reader", keyword)
    return pass_result(check)


def _mesh_authority_invariant(check: CertificationCheck) -> CertificationResult:
    source = _read_text(REPO_ROOT / "src" / "services" / "mesh" / "mesh_orchestrator.py")
    if "validate_approval" not in source or "submit_critical_event" not in source:
        return fail_result(check, "mesh_authority_contract_missing", "mesh_orchestrator.py")
    forbidden_frontend_tokens = ("MeshOrchestrator", "submit_critical_event", "validate_approval")
    frontend_root = REPO_ROOT / "frontend"
    if frontend_root.exists():
        for path in sorted(frontend_root.rglob("*")):
            if path.is_file() and path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
                text = _read_text(path)
                for token in forbidden_frontend_tokens:
                    if token in text:
                        return fail_result(check, "frontend_authority_token", f"{_relative(path)}:{token}")
    return pass_result(check)


def _ai_advisory_only_invariant(check: CertificationCheck) -> CertificationResult:
    source = _read_text(REPO_ROOT / "src" / "services" / "governance" / "simulation" / "ai_advisor.py")
    if "advis" not in source.lower():
        return fail_result(check, "ai_advisory_contract_missing", "ai_advisor.py")
    forbidden_authority_calls = ("submit_critical_event", "write_ledger", ".promote(", "execute_plan", "apply_recovery")
    ai_paths = sorted((REPO_ROOT / "src" / "services" / "ai").glob("*.py"))
    ai_paths.append(REPO_ROOT / "src" / "services" / "governance" / "simulation" / "ai_advisor.py")
    for path in ai_paths:
        source = _read_text(path)
        for token in forbidden_authority_calls:
            if token in source:
                return fail_result(check, "ai_authority_call", f"{_relative(path)}:{token}")
    return pass_result(check)


def _mesh_determinism(check: CertificationCheck) -> CertificationResult:
    orch = MeshOrchestrator()
    orch.submit_critical_event("admin", "INIT", {"val": 1}, ["n1", "n2"])
    orch.submit_critical_event("admin", "INIT", {"val": 2}, ["n1", "n2"])

    for worker in orch.workers:
        if not ReplayConsistencyChecker.check(worker.current_state, worker.event_log):
            return fail_result(check, "determinism_replay_mismatch", worker.node_id)

        replayed_once = StateProjector.project(worker.event_log)
        replayed_twice = StateProjector.project(worker.event_log + worker.event_log)
        if replayed_once.get("_state_hash") != replayed_twice.get("_state_hash"):
            return fail_result(check, "idempotent_replay_mismatch", worker.node_id)

    if not ForkResolutionTester.test_fork_safety(orch):
        return fail_result(check, "fork_safety_failed")
    if not QuorumIntegrityTester.test_quorum_threshold(orch):
        return fail_result(check, "quorum_integrity_failed")
    if not ConvergenceValidator.validate_all_nodes_converged(orch.workers + [orch.leader]):
        return fail_result(check, "convergence_failed")
    if not ConvergenceValidator.test_recovery_convergence(orch.workers[0], orch.leader):
        return fail_result(check, "anti_entropy_sync_failed")

    for worker in orch.workers:
        try:
            forged = AdversarialFaultInjector.create_forged_event(orch.leader.event_log[-1])
            worker.apply_event(forged)
            return fail_result(check, "forged_event_accepted", worker.node_id)
        except Exception:
            continue
    return pass_result(check)


def _pytest_pass(check: CertificationCheck) -> CertificationResult:
    return _run_command(
        check,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_certification_pipeline.py",
        ],
    )


def _replay_determinism(check: CertificationCheck) -> CertificationResult:
    return _run_command(check, [sys.executable, "-m", "pytest", "-q", "tests/integration/test_replay_determinism.py"])


def _projection_consistency(check: CertificationCheck) -> CertificationResult:
    return _run_command(
        check,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_projection_federation.py",
            "tests/test_db_projection_reader.py",
            "src/tests/test_projection_federation_ordering.py",
        ],
    )


def _api_governance_get_only_ops(check: CertificationCheck) -> CertificationResult:
    return _run_command(
        check,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_ops_console_shell.py",
            "tests/test_ops_domain_panel_governance.py",
            "tests/test_read_only_surface_registry.py",
        ],
    )


def _frontend_governance_no_mutation_ui(check: CertificationCheck) -> CertificationResult:
    frontend_root = REPO_ROOT / "frontend" / "operator-observatory"
    if not frontend_root.exists():
        return pass_result(check)

    forbidden_tokens = (
        "PUT",
        "PATCH",
        "DELETE",
        "Refresh",
        "Retry",
        "approve",
        "reject",
        "execute",
        "repair",
        "promote",
        "submit_critical_event",
        "MeshOrchestrator",
        "write_ledger",
    )
    
    # Strictly bind exceptions to exact files AND the exact tokens they are allowed to contain.
    bounded_mutation_exceptions = {
        "frontend/operator-observatory/app/api/ops/runtime-tasks/create/route.ts": {"POST"},
        "frontend/operator-observatory/app/api/ops/runtime-tasks/start/route.ts": {"POST"},
        "frontend/operator-observatory/app/api/ops/runtime-tasks/finish/route.ts": {"POST"},
        "frontend/operator-observatory/app/runtime-console/page.tsx": {"POST", "<button"},
        "frontend/operator-observatory/lib/backend-client.ts": {"POST"}
    }

    for path in sorted(frontend_root.rglob("*")):
        if any(part in {".next", "node_modules", "out", "dist"} for part in path.parts):
            continue
        if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx", ".css"}:
            continue
            
        rel_path = _relative(path)
        normalized_rel_path = rel_path.replace("\\", "/")
        
        allowed_mutation_tokens = set()
        for allow_path, tokens in bounded_mutation_exceptions.items():
            if normalized_rel_path.endswith(allow_path):
                allowed_mutation_tokens = tokens
                break
        
        text = _read_text(path)
        
        # Check standard forbidden tokens everywhere
        for token in forbidden_tokens:
            if token in text:
                return fail_result(check, "frontend_mutation_or_authority_token", f"{rel_path}:{token}")
                
        # Check high-risk tokens (POST and <button), strictly limiting to allowed files
        for high_risk_token in ("POST", "<button"):
            if high_risk_token in text and high_risk_token not in allowed_mutation_tokens:
                return fail_result(check, "frontend_mutation_or_authority_token", f"{rel_path}:{high_risk_token}_not_allowlisted")

    return pass_result(check)


def _runtime_task_governance_invariant(check: CertificationCheck) -> CertificationResult:
    passed, detail = check_runtime_task_governance(REPO_ROOT)
    if passed:
        return pass_result(check)
    return fail_result(check, "runtime_task_governance_violation", detail)


def _security_dependency_check(check: CertificationCheck) -> CertificationResult:
    return check_security_dependencies(REPO_ROOT, check)


def _run_command(check: CertificationCheck, command: list[str]) -> CertificationResult:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode == 0:
        return pass_result(check)

    detail = _stable_subprocess_detail(command, completed.returncode, completed.stdout, completed.stderr)
    return fail_result(check, "subprocess_failed", detail)


def _stable_subprocess_detail(command: list[str], returncode: int, stdout: str, stderr: str) -> str:
    output = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    stable_lines = [line for line in output.splitlines() if " seconds" not in line and "warnings summary" not in line]
    return "\n".join(
        [
            f"command={' '.join(command)}",
            f"returncode={returncode}",
            *stable_lines[-20:],
        ]
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def module_imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(_read_text(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return tuple(sorted(imports))
