import json
import numpy as np
import os
from src.services.structure.document_graph_builder import DocumentGraphBuilder
from src.services.structure.structure_encoder import StructureEncoder

class ProviderClusteringEngine:
    SIGNATURE_PATH = "data/canonical_signatures.json"
    OUTLIER_THRESHOLD = 50.0 # Heuristic distance margin

    @classmethod
    def load_signatures(cls):
        if not os.path.exists(cls.SIGNATURE_PATH):
            return {}
        with open(cls.SIGNATURE_PATH, "r") as f:
            data = json.load(f)
            return {k: np.array(v) for k, v in data.items()}

    @classmethod
    def get_cluster(cls, pdf_path):
        signatures = cls.load_signatures()
        if not signatures:
            return {"provider": "unseen_template", "confidence": 0.0}

        graph = DocumentGraphBuilder.build_graph(pdf_path)
        embedding = StructureEncoder.encode(graph)
        
        distances = {k: np.linalg.norm(embedding - v) for k, v in signatures.items()}
        closest = min(distances, key=distances.get)
        min_dist = distances[closest]
        
        # Uncertainty modeling
        confidence = max(0.0, 1.0 - (min_dist / 100.0))
        uncertainty = min(1.0, min_dist / 100.0)
        
        if min_dist > cls.OUTLIER_THRESHOLD:
            return {
                "provider": "outlier_structure",
                "confidence": 0.0,
                "uncertainty": 1.0,
                "closest": closest
            }
        
        return {
            "provider": closest,
            "confidence": round(confidence, 2),
            "uncertainty": round(uncertainty, 2),
            "closest": closest
        }
