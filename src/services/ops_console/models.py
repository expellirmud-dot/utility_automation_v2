from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PanelData(BaseModel):
    panel_id: str
    title: str
    summaries: List[str] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    item_count: int = 0
    advisory_only: bool = True

class DomainPanelData(PanelData):
    domain: str
    semantic_score: float = 0.0
    health_status: str = "UNKNOWN"
    priority: int = 3
    recommendations: List[str] = Field(default_factory=list)
    evidence_links: List[str] = Field(default_factory=list)
