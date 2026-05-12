class RealPipelineRunner:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.results = []

    def run(self, dataset):
        for doc in dataset:
            result = self.pipeline.process(doc)
            self.results.append({
                "doc": doc["file"],
                "result": result
            })
        return self.results
