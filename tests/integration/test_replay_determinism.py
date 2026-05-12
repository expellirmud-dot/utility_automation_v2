from src.services.rules.rule_engine import RuleEngine
from src.services.rules.rule_registry import RuleRegistry
from src.services.rules.rule_model import Rule

def test_replay():
    reg = RuleRegistry()
    reg.register(Rule("R1", "T", 10, "ALLOW", "USER", None, "ALLOW"))
    
    e1 = RuleEngine(reg)
    e2 = RuleEngine(reg)
    
    d1 = e1.evaluate("USER", "READ", {})
    d2 = e2.evaluate("USER", "READ", {})
    
    assert d1 == d2
    print("Deterministic replay: PASSED")

if __name__ == "__main__":
    test_replay()
