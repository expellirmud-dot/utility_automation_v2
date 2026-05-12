import fitz

class DocumentGraphBuilder:
    @staticmethod
    def build_graph(pdf_path):
        doc = fitz.open(pdf_path)
        page = doc[0]
        blocks = page.get_text("blocks") # x0, y0, x1, y1, text, block_no, block_type
        doc.close()
        
        nodes = []
        for b in blocks:
            nodes.append({
                "type": "table" if b[6] == 1 else "text", # Heuristic block type
                "bbox": [b[0], b[1], b[2], b[3]],
                "text": b[4]
            })
            
        # Build spatial adjacency edges
        edges = []
        for i, n1 in enumerate(nodes):
            for j, n2 in enumerate(nodes):
                if i == j: continue
                # Spatial heuristic: n1 above n2
                if n1["bbox"][3] < n2["bbox"][1]:
                    edges.append({"from": i, "to": j, "relation": "above"})
                    
        return {"nodes": nodes, "edges": edges}
