import threading

class ConcurrencyEngine:
    def __init__(self, pipeline, telemetry):
        self.pipeline = pipeline
        self.telemetry = telemetry
        self.results = []
        self.lock = threading.Lock()

    def worker(self, item):
        result = self.pipeline.process(item)
        with self.lock:
            self.results.append(result)

    def run(self, dataset, threads=10):
        chunk_size = max(1, len(dataset) // threads)
        threads_list = []

        for i in range(threads):
            chunk = dataset[i * chunk_size:(i + 1) * chunk_size]
            if i == threads - 1:
                chunk = dataset[i * chunk_size:]

            t = threading.Thread(
                target=lambda c=chunk: [self.worker(x) for x in c]
            )
            threads_list.append(t)
            t.start()

        for t in threads_list:
            t.join()

        return self.results
