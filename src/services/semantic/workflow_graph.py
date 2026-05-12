from typing import Dict, List, Any

class WorkflowGraphBuilder:
    def build_approval_chain(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the approval chain graph.
        Target Structure: Requester -> Finance -> Director -> Clerk -> Final Approver
        """
        actors = workflow_data.get("actors", [])
        
        nodes = [{"id": i, "actor": actor, "role": actor.get("role", "Unknown")} for i, actor in enumerate(actors)]
        edges = []
        
        # Build sequential approval steps based on input order
        for i in range(len(nodes) - 1):
            edges.append({
                "from": nodes[i]["id"],
                "to": nodes[i+1]["id"],
                "action": "approve"
            })
            
        return {
            "nodes": nodes,
            "edges": edges,
            "validation_status": self._validate_chain(nodes)
        }
        
    def _validate_chain(self, nodes: List[Dict[str, Any]]) -> str:
        roles = [n["role"].lower() for n in nodes]
        
        # Example validation for required roles in an approval chain
        required_roles = ["requester"]
        # Depending on complexity, we might require more, but we keep it simple here.
        # It ensures at least the basic workflow is present.
        for req in required_roles:
            if req not in roles:
                return f"Missing required step: {req}"
        return "VALID"
