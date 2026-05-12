import json

class ReplayEngine:

    def __init__(self, log_path="ledger/events.log"):
        self.log_path = log_path

    def replay(self, filter_action=None):

        events = []

        with open(self.log_path, "r") as f:
            for line in f:
                event = json.loads(line)

                if filter_action and event["action"] != filter_action:
                    continue

                events.append(event)

        return events
