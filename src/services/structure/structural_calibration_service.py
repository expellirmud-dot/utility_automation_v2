import os
import json
import numpy as np
from src.services.structure.document_graph_builder import DocumentGraphBuilder
from src.services.structure.structure_encoder import StructureEncoder

class StructuralCalibrationService:
    @staticmethod
    def calibrate(golden_dir="datasets/golden"):
        centroids = {}
        for provider in ["nt", "pea", "water"]:
            provider_path = os.path.join(golden_dir, provider)
            embeddings = []
            
            for file in os.listdir(provider_path):
                if file.endswith(".pdf"):
                    path = os.path.join(provider_path, file)
                    graph = DocumentGraphBuilder.build_graph(path)
                    embeddings.append(StructureEncoder.encode(graph))
            
            if embeddings:
                centroids[provider.upper()] = np.mean(embeddings, axis=0).tolist()
                
        with open("data/canonical_signatures.json", "w") as f:
            json.dump(centroids, f, indent=4)
        return centroids
