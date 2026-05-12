import random

class ProductionLoadGenerator:
    def generate(self, n=10000):
        dataset = []
        for i in range(n):
            dataset.append({
                "doc_id": f"DOC-{i}",
                "type": random.choice(["NORMAL", "EDGE", "MALFORMED"]),
                "size": random.randint(1, 50),  # simulate OCR complexity
                "amount": random.randint(100, 100000),
                "noise": random.random() < 0.1
            })
        return dataset
