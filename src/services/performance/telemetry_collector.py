import time
from collections import defaultdict

class TelemetryCollector:
    def __init__(self):
        self.timings = defaultdict(list)

    def time_block(self, stage_name):
        # Allow nested class definition or use a simple context manager
        class Timer:
            def __enter__(inner):
                inner.start = time.time()
                return inner

            def __exit__(inner, exc_type, exc_val, exc_tb):
                duration = time.time() - inner.start
                self.timings[stage_name].append(duration)

        return Timer()

    def get_stats(self):
        stats = {}
        for stage, times in self.timings.items():
            if not times:
                continue
            stats[stage] = {
                "avg": sum(times) / len(times),
                "max": max(times),
                "min": min(times),
                "calls": len(times),
                "samples": times
            }
        return stats
