class HealingTracker:
    def summarize(self, healing_events):
        total = len(healing_events)

        success = sum(
            1 for h in healing_events if h.get("status") == "HEALED"
        )

        return {
            "total_heals": total,
            "success_rate": success / total if total else 0,
            "recent_activity": healing_events[-5:] if healing_events else []
        }
