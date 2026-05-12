from typing import Dict, Any, Optional
from src.models.semantic.voucher_model import Voucher, FinalVoucherResult, ValidationResult
from src.services.semantic.financial_engine import FinancialIntegrityEngine
from src.services.semantic.intent_engine import IntentDetectionEngine
from src.services.semantic.workflow_graph import WorkflowGraphBuilder
from src.services.semantic.compliance_engine import ComplianceValidationLayer
from src.services.structure.document_graph_builder import DocumentGraphBuilder

class SemanticVoucherPipeline:
    def __init__(self):
        self.financial_engine = FinancialIntegrityEngine()
        self.intent_engine = IntentDetectionEngine()
        self.workflow_builder = WorkflowGraphBuilder()
        self.compliance_engine = ComplianceValidationLayer()

    def process(self, extracted_data: Dict[str, Any], pdf_path: Optional[str] = None) -> FinalVoucherResult:
        audit_trace = []
        
        # 1. OCR -> Structure (using DocumentGraphBuilder if pdf provided)
        if pdf_path:
            try:
                graph_structure = DocumentGraphBuilder.build_graph(pdf_path)
                audit_trace.append(f"Built document graph with {len(graph_structure['nodes'])} nodes.")
            except Exception as e:
                audit_trace.append(f"Failed to build document graph: {str(e)}")

        # 2. Intent Detection
        intent, confidence = self.intent_engine.detect(extracted_data)
        audit_trace.append(f"Intent detected: {intent} (Confidence: {confidence})")

        # 3. Semantic Mapping
        voucher = Voucher(
            intent=intent,
            header=extracted_data.get("header", {}),
            budget_context=extracted_data.get("budget_context", {}),
            financials=extracted_data.get("financials", {}),
            workflow=extracted_data.get("workflow", {}),
            compliance=extracted_data.get("compliance", {})
        )
        audit_trace.append("Mapped extracted data to Semantic Voucher model.")

        # 4. Workflow Graph Generation
        workflow_graph = self.workflow_builder.build_approval_chain(voucher.workflow)
        audit_trace.append(f"Generated workflow graph. Status: {workflow_graph.get('validation_status')}")

        # 5. Financial Validation
        fin_validation = self.financial_engine.validate(voucher)
        for err in fin_validation.errors:
            audit_trace.append(f"Financial Error: {err}")

        # 6. Compliance Validation
        comp_validation = self.compliance_engine.validate(voucher)
        for err in comp_validation.errors:
            audit_trace.append(f"Compliance Error: {err}")

        # Merge Validations
        all_errors = fin_validation.errors + comp_validation.errors
        status = "FAIL" if all_errors else "PASS"
        severity = "LOW"
        if fin_validation.severity == "CRITICAL" or comp_validation.severity == "CRITICAL":
            severity = "CRITICAL"
        elif fin_validation.severity == "HIGH" or comp_validation.severity == "HIGH":
            severity = "HIGH"

        merged_validation = ValidationResult(
            status=status,
            errors=all_errors,
            severity=severity
        )
        audit_trace.append(f"Validation completed. Status: {status}")

        return FinalVoucherResult(
            voucher=voucher,
            validation=merged_validation,
            intent=intent,
            confidence=confidence,
            audit_trace=audit_trace
        )
