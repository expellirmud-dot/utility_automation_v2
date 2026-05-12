class CLIDashboard:
    def render(self, data):
        print("\n===== SYSTEM DASHBOARD =====")
        print(f"STATUS: {data['system_status']}")
        print(f"HEALTH: {data['health_score']:.2f}")
        print(f"ACTIVE HEALINGS: {data['state']['active_healings']}")
        print("\nTOP BOTTLENECKS:")
        
        for b in data["bottlenecks"]["top_critical"]:
            print(f"- {b.get('stage')} | {b.get('severity')}")

        print("\nRECENT HEALING:")
        for h in data["healing"]["recent_activity"]:
            print(f"- {h.get('status')}")
