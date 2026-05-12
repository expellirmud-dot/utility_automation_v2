class RollbackManager:
    def __init__(self, graph_engine):
        self.graph_engine = graph_engine

    def rollback_to(self, target_version_id: str, actor: str, reason: str):
        return self.graph_engine._rollback_version(target_version_id, actor, reason)
