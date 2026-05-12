from .policy_version import POLICY_STAGES


class PromotionPipeline:
    TRANSITIONS = {
        "draft": "simulation",
        "simulation": "approved",
        "approved": "production",
    }

    def __init__(self, graph_engine):
        self.graph_engine = graph_engine

    def promote(self, version_id: str, to_stage: str, actor: str, quorum_signatures=None):
        if to_stage not in POLICY_STAGES:
            raise ValueError(f"Unsupported promotion stage: {to_stage}")

        version = self.graph_engine.get_version(version_id)
        expected_stage = self.TRANSITIONS.get(version.stage)
        if expected_stage != to_stage:
            raise ValueError(f"Invalid promotion transition: {version.stage} -> {to_stage}")

        if to_stage == "simulation":
            return self.graph_engine._promote_local(version_id, to_stage, actor)

        signatures = list(quorum_signatures or [])
        return self.graph_engine._promote_with_quorum(version_id, to_stage, actor, signatures)
