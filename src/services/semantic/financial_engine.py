from src.models.semantic.voucher_model import ValidationResult, Voucher

class FinancialIntegrityEngine:
    def validate(self, voucher: Voucher) -> ValidationResult:
        errors = []
        severity = "LOW"
        
        financials = voucher.financials
        subtotal = financials.get("subtotal", 0)
        vat = financials.get("vat", 0)
        withholding_tax = financials.get("withholding_tax", 0)
        net = financials.get("net", 0)
        
        # 1. Rule: subtotal + vat - withholding = net
        # Accounting for floating point issues
        calculated_net = subtotal + vat - withholding_tax
        if abs(calculated_net - net) > 0.01:
            errors.append(f"Financial mismatch: subtotal ({subtotal}) + vat ({vat}) - withholding ({withholding_tax}) != net ({net})")
            severity = "CRITICAL"
            
        # 2. Rule: net <= budget_remaining
        budget_remaining = voucher.budget_context.get("remaining", float('inf'))
        if net > budget_remaining:
            errors.append(f"Budget overrun: net ({net}) exceeds budget_remaining ({budget_remaining})")
            severity = "CRITICAL"
            
        # 3. Rule: VAT valid range (e.g., 7% of subtotal)
        # Using a valid range since VAT can be 0 or 7% usually
        expected_vat = round(subtotal * 0.07, 2)
        if vat > 0 and abs(vat - expected_vat) > 0.1:
            errors.append(f"VAT mismatch: expected around {expected_vat}, got {vat}")
            if severity != "CRITICAL":
                severity = "HIGH"
                
        # 4. Rule: No negative values
        if any(v < 0 for v in [subtotal, vat, withholding_tax, net]):
            errors.append("Negative financial value detected")
            severity = "CRITICAL"
            
        status = "FAIL" if errors else "PASS"
        return ValidationResult(status=status, errors=errors, severity=severity)
