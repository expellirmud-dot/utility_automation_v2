import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.services.governance.governance_controller import GovernanceController
from src.services.semantic.semantic_pipeline_with_governance import GovernanceWrappedSemanticPipeline

def test_rule_versioning():
    controller = GovernanceController()
    rule1 = controller.create_rule("TAX_RULE", "1.0", "Base tax rule", {"rate": 0.07})
    assert rule1.version == "1.0"
    assert rule1.status == "ACTIVE"
    
    # Cannot overwrite
    with pytest.raises(ValueError):
        controller.create_rule("TAX_RULE", "1.0", "New base tax rule", {"rate": 0.10})
        
    rule2 = controller.create_rule("TAX_RULE", "2.0", "New base tax rule", {"rate": 0.10})
    controller.deactivate_rule("TAX_RULE", "1.0")
    
    active_rule = controller.get_active_rule("TAX_RULE")
    assert active_rule.version == "2.0"
    
    # Rollback
    controller.rule_system.rollback("TAX_RULE", "1.0")
    active_rule_after_rollback = controller.get_active_rule("TAX_RULE")
    assert active_rule_after_rollback.version == "1.0"

def test_audit_reconstruction():
    controller = GovernanceController()
    trace_id = controller.audit_engine.start_trace()
    
    controller.log_decision(trace_id, "STEP_1", {"data": 1}, "RULE_A", "1.0", "PASS", "OK")
    controller.log_decision(trace_id, "STEP_2", {"data": 2}, "RULE_B", "1.1", "FAIL", "ERR_1")
    
    flow = controller.audit_engine.reconstruct_flow(trace_id)
    assert len(flow) == 2
    assert flow[0].step_name == "STEP_1"
    assert flow[1].step_name == "STEP_2"
    assert flow[1].decision == "FAIL"

def test_regression_drift_and_deployment_gate():
    controller = GovernanceController()
    
    # Setup golden dataset
    dataset = [
        {"id": "1", "amount": 100},
        {"id": "2", "amount": 500},
        {"id": "3", "amount": 1000},
        {"id": "4", "amount": 2000},
    ]
    controller.regression_system.set_golden_dataset(dataset)
    
    # Rules
    controller.create_rule("THRESH_RULE", "1.0", "Base rule", {"max": 1000})
    controller.create_rule("THRESH_RULE", "2.0", "Stricter rule", {"max": 500})
    
    # Evaluator func
    def evaluator(case, params):
        return "PASS" if case["amount"] <= params["max"] else "FAIL"
        
    report = controller.run_regression(evaluator, "1.0", "2.0", "THRESH_RULE")
    
    assert report.total_cases == 4
    # Case 3 (1000): 1.0 (PASS) vs 2.0 (FAIL) -> changed!
    assert report.changed_cases == 1
    assert report.risk_score == 25.0 # 1/4 = 25%
    
    # Gate test: > 10% risk -> cannot deploy
    assert controller.can_deploy(report) is False
    assert len(report.diff_summary) == 1

def test_pipeline_integration():
    controller = GovernanceController()
    pipeline = GovernanceWrappedSemanticPipeline(controller)
    
    data = {
        "header": {"fiscal_year": "2026", "description": "ขอเบิกเงิน"},
        "budget_context": {"remaining": 5000, "fiscal_year": "2026"},
        "financials": {"subtotal": 1000, "vat": 70, "withholding_tax": 10, "net": 1060},
        "workflow": {
            "actors": [
                {"role": "requester"}, {"role": "finance"}, {"role": "director"}
            ],
            "signatures": ["sig1"]
        },
        "compliance": {"procurement_method": "general"}
    }
    
    result = pipeline.process_with_governance(data)
    
    assert result["status"] == "PASS"
    assert result["governance_decision"] == "ALLOW"
    assert "FIN:1.0.0|COMP:1.0.0" in result["rule_version_used"]
    assert len(result["audit_trace"]) >= 3
    
    # Verify exact reconstruction
    step_names = [s["step_name"] for s in result["audit_trace"]]
    assert "INTENT_DETECTION" in step_names
    assert "FINANCIAL_VALIDATION" in step_names
    assert "COMPLIANCE_VALIDATION" in step_names
