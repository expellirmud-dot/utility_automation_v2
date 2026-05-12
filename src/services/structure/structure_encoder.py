import numpy as np

class StructureEncoder:
    @staticmethod
    def encode(graph):
        # Flattened features: node types count, average vertical position
        node_types = [n["type"] for n in graph["nodes"]]
        type_vector = [node_types.count("header"), node_types.count("table"), node_types.count("text")]
        
        # Spatial vector: average y-coordinate of blocks
        avg_y = np.mean([n["bbox"][1] for n in graph["nodes"]])
        
        return np.array(type_vector + [avg_y])
