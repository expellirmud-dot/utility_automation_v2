from collections import Counter

class AuditAnalytics:

    def __init__(self, events):
        self.events = events

    def decision_distribution(self):

        return Counter([e["decision"] for e in self.events])

    def role_activity(self):

        return Counter([e["role"] for e in self.events])
