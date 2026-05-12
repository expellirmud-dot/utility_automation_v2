import os

class RealDatasetLoader:
    def load(self, path):
        documents = []
        # Check if path exists for safety
        if not os.path.exists(path):
            return documents
            
        for file in os.listdir(path):
            if file.endswith(".pdf"):
                documents.append({
                    "file": file,
                    "path": os.path.join(path, file),
                    "type": "REAL_DOCUMENT"
                })
        return documents
