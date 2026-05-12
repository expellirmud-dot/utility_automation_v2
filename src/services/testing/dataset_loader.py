import os

class DatasetLoader:
    @staticmethod
    def get_all_pdfs(base_path="datasets"):
        pdfs = []
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".pdf"):
                    pdfs.append(os.path.join(root, file))
        return pdfs
