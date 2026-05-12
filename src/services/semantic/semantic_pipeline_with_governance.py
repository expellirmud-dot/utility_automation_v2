from typing import Dict, Any, Optional
from src.services.semantic.semantic_pipeline import SemanticVoucherPipeline
from src.services.governance.governance_controller import GovernanceController
from src.models.semantic.voucher_model import FinalVoucherResult

class GovernanceWrappedSemanticPipeline:
    def __init__(self, controller: GovernanceController):
        self.pipeline = SemanticVoucherPipeline()
        self.controller = controller
        
        # Ensure base rules exist in Governance Layer
        if not self.controller.get_active_rule("INTENT_RULE"):
            self.controller.create_rule(
                rule_id="INTENT_RULE",
                version="1.0.0",
                description="Rule-based intent detection with keyword matching",
                logic_params={"threshold": 0.8}
            )
            
        if not self.controller.get_active_rule("FIN_INTEGRITY"):
            self.controller.create_rule(
                rule_id="FIN_INTEGRITY",
                version="1.0.0",
                description="Basic subtotal and vat matching",
                logic_params={"tolerance": 0.01}
            )
            
        if not self.controller.get_active_rule("COMPLIANCE_CHECK"):
            self.controller.create_rule(
                rule_id="COMPLIANCE_CHECK",
                version="1.0.0",
                description="Fiscal year and budget checks",
                logic_params={"require_signatures": True}
            )

    def process_with_governance(self, extracted_data: Dict[str, Any], pdf_path: Optional[str] = None) -> Dict[str, Any]:
        # Start Trace
        trace_id = self.controller.audit_engine.start_trace()
        
        # Run original pipeline (Semantic Model Understanding Layer)
        result: FinalVoucherResult = self.pipeline.process(extracted_data, pdf_path)
        
        # Log Intent Step
        intent_rule = self.controller.get_active_rule("INTENT_RULE")
        self.controller.log_decision(
            trace_id=trace_id,
            step_name="INTENT_DETECTION",
            input_data={"data": extracted_data.get("header", {})},
            rule_used="INTENT_RULE",
            rule_version=intent_rule.version if intent_rule else "UNKNOWN",
            decision=result.intent,
            reason_code=f"CONFIDENCE_{result.confidence}"
        )
        
        # Log Financial Validation Step
        fin_rule = self.controller.get_active_rule("FIN_INTEGRITY")
        fin_status = "PASS" if not any("Financial" in err for err in result.validation.errors) and not any("VAT" in err for err in result.validation.errors) and not any("Budget overrun" in err for err in result.validation.errors) and not any("Negative" in err for err in result.validation.errors) else "FAIL"
        
        self.controller.log_decision(
            trace_id=trace_id,
            step_name="FINANCIAL_VALIDATION",
            input_data={"financials": extracted_data.get("financials", {})},
            rule_used="FIN_INTEGRITY",
            rule_version=fin_rule.version if fin_rule else "UNKNOWN",
            decision=fin_status,
            reason_code="FIN_CHECK_OK" if fin_status == "PASS" else "FIN_ERRORS_DETECTED"
        )
        
        # Log Compliance Step
        comp_rule = self.controller.get_active_rule("COMPLIANCE_CHECK")
        comp_status = "PASS" if not any("Compliance" in err for err in result.validation.errors) else "FAIL"
        
        self.controller.log_decision(
            trace_id=trace_id,
            step_name="COMPLIANCE_VALIDATION",
            input_data={"compliance": extracted_data.get("compliance", {}), "workflow": extracted_data.get("workflow", {})},
            rule_used="COMPLIANCE_CHECK",
            rule_version=comp_rule.version if comp_rule else "UNKNOWN",
            decision=comp_status,
            reason_code="COMPLIANCE_OK" if comp_status == "PASS" else "COMPLIANCE_ERRORS_DETECTED"
        )
        
        # Format the output as required
        audit_flow = self.controller.audit_engine.reconstruct_flow(trace_id)
        
        audit_trace_list = [
            {
                "step_name": step.step_name,
                "rule_used": step.rule_used,
                "version": step.rule_version,
                "decision": step.decision,
                "reason_code": step.reason_code,
                "timestamp": step.timestamp.isoformat()
            } for step in audit_flow
        ]
        
        final_governance_decision = "ALLOW" if result.validation.status == "PASS" else "BLOCK"
        
        return {
            "status": result.validation.status,
            "audit_trace": audit_trace_list,
            "regression_status": {"checked": False, "score": 0.0},
            "rule_version_used": f"FIN:{fin_rule.version if fin_rule else 'UNK'}|COMP:{comp_rule.version if comp_rule else 'UNK'}",
            "governance_decision": final_governance_decision,
            "semantic_result": result
        }
