from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

class GovernanceMetrics:
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Counters
        self.decisions_total = Counter(
            'governance_decisions_total', 
            'Total number of governance decisions', 
            ['provider', 'decision'], 
            registry=self.registry
        )
        self.security_rejections_total = Counter(
            'security_rejection_total', 
            'Total number of security rejections', 
            ['reason'], 
            registry=self.registry
        )
        self.fail_closed_events_total = Counter(
            'fail_closed_events_total', 
            'Number of times the system failed closed', 
            registry=self.registry
        )
        self.rule_conflict_total = Counter(
            'rule_conflict_total', 
            'Total number of rule conflicts detected', 
            registry=self.registry
        )
        self.replay_validation_failures_total = Counter(
            'replay_validation_failures_total', 
            'Total number of replay validation failures', 
            registry=self.registry
        )
        self.replay_drift_detected_total = Counter(
            'replay_drift_detected_total', 
            'Total number of replay drifts detected', 
            registry=self.registry
        )

        # Histograms
        self.replay_recovery_seconds = Histogram(
            'replay_recovery_seconds', 
            'Time taken for replay recovery', 
            registry=self.registry
        )
        self.audit_append_latency_ms = Histogram(
            'audit_append_latency_ms', 
            'Latency of audit append operations in ms', 
            registry=self.registry
        )
        self.wal_recovery_duration_ms = Histogram(
            'wal_recovery_duration_ms', 
            'Duration of WAL recovery in ms', 
            registry=self.registry
        )

        # Gauges
        self.system_health_score = Gauge(
            'system_health_score', 
            'Current system health score (0-1)', 
            registry=self.registry
        )

    def expose_metrics(self):
        return generate_latest(self.registry).decode("utf-8")

# Singleton instance
metrics = GovernanceMetrics()
