from src.models.semantic.voucher_model import ValidationResult, Voucher

class ComplianceValidationLayer:
    def validate(self, voucher: Voucher) -> ValidationResult:
        errors = []
        severity = "LOW"
        
        # 1. Budget availability check
        budget_remaining = voucher.budget_context.get("remaining", float('inf'))
        net_amount = voucher.financials.get("net", 0)
        if net_amount > budget_remaining:
            errors.append("Compliance error: Budget unavailable for this payment")
            severity = "CRITICAL"
            
        # 2. Fiscal year consistency
        fiscal_year = voucher.budget_context.get("fiscal_year")
        current_year = voucher.header.get("fiscal_year")
        if fiscal_year and current_year and str(fiscal_year) != str(current_year):
            errors.append(f"Compliance error: Fiscal year mismatch ({fiscal_year} vs {current_year})")
            severity = "HIGH"
            
        # 3. Procurement rule compliance (e.g. e-bidding required for > 500k)
        if net_amount > 500000 and voucher.compliance.get("procurement_method") != "e-bidding":
            errors.append("Compliance error: Amount > 500k requires e-bidding")
            severity = "CRITICAL"
            
        # 4. Document completeness
        if not voucher.workflow.get("signatures", []):
            errors.append("Compliance error: Missing signatures")
            if severity != "CRITICAL":
                severity = "HIGH"
                
        status = "FAIL" if errors else "PASS"
        return ValidationResult(status=status, errors=errors, severity=severity)
