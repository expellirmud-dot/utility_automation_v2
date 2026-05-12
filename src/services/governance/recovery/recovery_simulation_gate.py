from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional, Tuple

from src.services.governance.recovery.recovery_models import (
    RecoveryPlan,
    RecoveryProposal,
    RecoveryReport,
    RecoveryStepType,
)
from src.services.governance.recovery.recovery_report_hasher import (
    compute_proposal_hash,
    compute_report_hash,
    stable_hash,
)


class RecoverySimulationRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


RISK_PRECEDENCE: Mapping[RecoverySimulationRiskLevel, int] = {
    RecoverySimulationRiskLevel.LOW: 1,
    RecoverySimulationRiskLevel.MEDIUM: 2,
    RecoverySimulationRiskLevel.HIGH: 3,
    RecoverySimulationRiskLevel.BLOCKED: 4,
}

STEP_RISK_BY_TYPE: Mapping[RecoveryStepType, RecoverySimulationRiskLevel] = {
    RecoveryStepType.ISOLATE_WORKER: RecoverySimulationRiskLevel.MEDIUM,
    RecoveryStepType.RUN_REPLAY_VERIFICATION: RecoverySimulationRiskLevel.LOW,
    RecoveryStepType.REBUILD_SQLITE_PROJECTION: RecoverySimulationRiskLevel.MEDIUM,
    RecoveryStepType.REQUEST_QUORUM_REPAIR: RecoverySimulationRiskLevel.HIGH,
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT: RecoverySimulationRiskLevel.HIGH,
    RecoveryStepType.RESTART_NODE: RecoverySimulationRiskLevel.MEDIUM,
}

STEP_WARNING_CODE_BY_TYPE: Mapping[RecoveryStepType, str] = {
    RecoveryStepType.ISOLATE_WORKER: "RISK_ISOLATE_WORKER",
    RecoveryStepType.RUN_REPLAY_VERIFICATION: "RISK_RUN_REPLAY_VERIFICATION",
    RecoveryStepType.REBUILD_SQLITE_PROJECTION: "RISK_REBUILD_SQLITE_PROJECTION",
    RecoveryStepType.REQUEST_QUORUM_REPAIR: "RISK_REQUEST_QUORUM_REPAIR",
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT: "RISK_ROLLBACK_TO_LEDGER_POINT",
    RecoveryStepType.RESTART_NODE: "RISK_RESTART_NODE",
}

STEP_WARNING_DETAIL_BY_TYPE: Mapping[RecoveryStepType, str] = {
    RecoveryStepType.ISOLATE_WORKER: "ISOLATE_WORKER_REQUIRES_OPERATOR_REVIEW",
    RecoveryStepType.RUN_REPLAY_VERIFICATION: "RUN_REPLAY_VERIFICATION_READ_ONLY_CHECK",
    RecoveryStepType.REBUILD_SQLITE_PROJECTION: "REBUILD_SQLITE_PROJECTION_CACHE_SCOPE",
    RecoveryStepType.REQUEST_QUORUM_REPAIR: "REQUEST_QUORUM_REPAIR_REQUIRES_LATER_AUTHORITY_PATH",
    RecoveryStepType.ROLLBACK_TO_LEDGER_POINT: "ROLLBACK_TO_LEDGER_POINT_REQUIRES_LATER_AUTHORITY_PATH",
    RecoveryStepType.RESTART_NODE: "RESTART_NODE_REQUIRES_OPERATOR_REVIEW",
}

UNKNOWN_STEP_WARNING_CODE = "RISK_UNKNOWN_STEP_TYPE"
UNKNOWN_STEP_WARNING_DETAIL = "UNKNOWN_STEP_TYPE_BLOCKS_HANDOFF"


@dataclass(frozen=True)
class RecoveryStepSimulation:
    step_type: str
    target: str
    risk_level: str
    warning_code: str
    warning_detail: str

    def __post_init__(self):
        if self.risk_level not in {level.value for level in RecoverySimulationRiskLevel}:
            raise ValueError(f"Invalid risk level: {self.risk_level}")

    def to_payload(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "step_type": self.step_type,
            "target": self.target,
            "warning_code": self.warning_code,
            "warning_detail": self.warning_detail,
        }


@dataclass(frozen=True)
class RecoverySimulationReport:
    proposal_hash: str
    report_hash: Optional[str]
    overall_risk: str
    ready_for_handoff: bool
    step_simulations: Tuple[RecoveryStepSimulation, ...]
    warnings: Tuple[str, ...] = ()
    blocked_reasons: Tuple[str, ...] = ()
    simulation_hash: str = field(default="")

    def __post_init__(self):
        if self.overall_risk not in {level.value for level in RecoverySimulationRiskLevel}:
            raise ValueError(f"Invalid risk level: {self.overall_risk}")
        object.__setattr__(
            self,
            "step_simulations",
            tuple(sorted(
                self.step_simulations,
                key=lambda item: (item.step_type, item.target, item.warning_code, item.warning_detail),
            )),
        )
        object.__setattr__(self, "warnings", tuple(sorted(self.warnings)))
        object.__setattr__(self, "blocked_reasons", tuple(sorted(self.blocked_reasons)))
        if not self.simulation_hash:
            object.__setattr__(self, "simulation_hash", stable_hash(self.to_hash_payload()))

    def to_hash_payload(self) -> dict:
        return {
            "blocked_reasons": list(self.blocked_reasons),
            "overall_risk": self.overall_risk,
            "proposal_hash": self.proposal_hash,
            "ready_for_handoff": self.ready_for_handoff,
            "step_simulations": [item.to_payload() for item in self.step_simulations],
            "warnings": list(self.warnings),
        }

    def to_payload(self, include_hash: bool = True) -> dict:
        payload = self.to_hash_payload()
        if self.report_hash is not None:
            payload["report_hash"] = self.report_hash
        if include_hash:
            payload["simulation_hash"] = self.simulation_hash
        return payload


class RecoverySimulationGate:
    def simulate_proposal(self, proposal: RecoveryProposal) -> RecoverySimulationReport:
        return self._simulate(proposal=proposal, report_hash=None, invalid_report_hash=False)

    def simulate_report(self, report: RecoveryReport) -> RecoverySimulationReport:
        invalid_report_hash = report.report_hash != compute_report_hash(report)
        return self._simulate(
            proposal=report.proposal,
            report_hash=report.report_hash,
            invalid_report_hash=invalid_report_hash,
        )

    def _simulate(
        self,
        proposal: RecoveryProposal,
        report_hash: Optional[str],
        invalid_report_hash: bool,
    ) -> RecoverySimulationReport:
        blocked_reasons = []
        step_simulations = []

        if not proposal.plan.steps:
            blocked_reasons.append("BLOCKED_EMPTY_PLAN")

        if proposal.proposal_hash != compute_proposal_hash(proposal):
            blocked_reasons.append("BLOCKED_INVALID_PROPOSAL_HASH")

        if invalid_report_hash:
            blocked_reasons.append("BLOCKED_INVALID_REPORT_HASH")

        for step in proposal.plan.steps:
            step_type_value = step.step_type
            try:
                step_type = RecoveryStepType(step_type_value)
            except ValueError:
                blocked_reasons.append(f"BLOCKED_UNKNOWN_STEP_TYPE:{step_type_value}")
                step_simulations.append(
                    RecoveryStepSimulation(
                        step_type=step_type_value,
                        target=step.target,
                        risk_level=RecoverySimulationRiskLevel.BLOCKED.value,
                        warning_code=UNKNOWN_STEP_WARNING_CODE,
                        warning_detail=UNKNOWN_STEP_WARNING_DETAIL,
                    )
                )
                continue

            step_simulations.append(
                RecoveryStepSimulation(
                    step_type=step_type.value,
                    target=step.target,
                    risk_level=STEP_RISK_BY_TYPE[step_type].value,
                    warning_code=STEP_WARNING_CODE_BY_TYPE[step_type],
                    warning_detail=STEP_WARNING_DETAIL_BY_TYPE[step_type],
                )
            )

        if blocked_reasons:
            overall_risk = RecoverySimulationRiskLevel.BLOCKED
        else:
            overall_risk = self._max_risk(tuple(item.risk_level for item in step_simulations))

        warnings = tuple(item.warning_code for item in step_simulations)
        return RecoverySimulationReport(
            proposal_hash=proposal.proposal_hash,
            report_hash=report_hash,
            overall_risk=overall_risk.value,
            ready_for_handoff=not blocked_reasons,
            step_simulations=tuple(step_simulations),
            warnings=warnings,
            blocked_reasons=tuple(blocked_reasons),
        )

    def _max_risk(self, risk_levels: Tuple[str, ...]) -> RecoverySimulationRiskLevel:
        if not risk_levels:
            return RecoverySimulationRiskLevel.BLOCKED
        return max(
            (RecoverySimulationRiskLevel(level) for level in risk_levels),
            key=lambda level: RISK_PRECEDENCE[level],
        )
