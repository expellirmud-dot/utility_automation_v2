from typing import Dict, Any, List, Optional

class BudgetPreviewMatcher:
    @staticmethod
    def categorize_utility(expense_type: str) -> str:
        if not expense_type:
            return "unknown"
        exp = expense_type.strip().lower()
        if "ไฟฟ้า" in exp:
            return "electricity"
        if "ประปา" in exp:
            return "water"
        if "โทรศัพท์" in exp:
            return "phone"
        if "อินเทอร์เน็ต" in exp or "internet" in exp:
            return "internet"
        return "unknown"

    @staticmethod
    def classify_provider(provider_text: str) -> str:
        if not provider_text:
            return "unknown"
        p = provider_text.upper()
        if "PEA" in p or "การไฟฟ้า" in p:
            return "electricity"
        if "ประปา" in p or "PWA" in p:
            return "water"
        if "NT" in p or "โทรคมนาคมแห่งชาติ" in p:
            if "โทรศัพท์" in p:
                return "phone"
            if "อินเทอร์เน็ต" in p or "INTERNET" in p:
                return "internet"
            return "nt_ambiguous"
        return "unknown"

    @staticmethod
    def get_withholding_tax(canonical_type: str) -> Dict[str, Any]:
        if canonical_type == "electricity":
            return {
                "applies": False,
                "rule_id": "UTILITY_ELECTRICITY_NO_WHT",
                "display_label": "ไม่หักภาษี ณ ที่จ่าย"
            }
        elif canonical_type in ["phone", "internet", "water"]:
            return {
                "applies": True,
                "rule_id": "UTILITY_DEFAULT_WHT",
                "display_label": "หักภาษี ณ ที่จ่าย"
            }
        else:
            return {
                "applies": None,
                "rule_id": "NON_UTILITY_UNKNOWN",
                "display_label": "รอตรวจสอบ"
            }

    @staticmethod
    def match_case_to_preview(case_facts: Dict[str, Any], batch: Dict[str, Any]) -> Dict[str, Any]:
        blockers = []
        warnings = []
        missing_data = []
        
        blocker_details = []
        warning_details = []
        missing_data_details = []

        fiscal_year_be = case_facts.get("fiscal_year_be")
        expense_group = case_facts.get("expense_group")
        required_amount = case_facts.get("required_amount")
        provider = case_facts.get("provider", "")

        if not fiscal_year_be:
            blockers.append("missing fiscal_year_be")
            missing_data.append("fiscal_year_be")
            blocker_details.append({"code": "MISSING_FISCAL_YEAR_BE", "level": "blocker", "message": "ไม่พบข้อมูลปีงบประมาณ", "component": "budget_preview_matcher", "field": "fiscal_year_be", "detail": {}})
            missing_data_details.append({"code": "MISSING_FISCAL_YEAR_BE", "level": "missing_data", "message": "ไม่พบข้อมูลปีงบประมาณ", "component": "budget_preview_matcher", "field": "fiscal_year_be", "detail": {}})
        if not expense_group:
            blockers.append("missing expense_type")
            missing_data.append("expense_type")
            blocker_details.append({"code": "MISSING_EXPENSE_TYPE", "level": "blocker", "message": "ไม่พบกลุ่มค่าใช้จ่าย", "component": "budget_preview_matcher", "field": "expense_group", "detail": {}})
            missing_data_details.append({"code": "MISSING_EXPENSE_TYPE", "level": "missing_data", "message": "ไม่พบกลุ่มค่าใช้จ่าย", "component": "budget_preview_matcher", "field": "expense_group", "detail": {}})
        if required_amount is None:
            blockers.append("missing required_amount")
            missing_data.append("required_amount")
            blocker_details.append({"code": "MISSING_REQUIRED_AMOUNT", "level": "blocker", "message": "ไม่พบจำนวนเงินที่ขอเบิก", "component": "budget_preview_matcher", "field": "required_amount", "detail": {}})
            missing_data_details.append({"code": "MISSING_REQUIRED_AMOUNT", "level": "missing_data", "message": "ไม่พบจำนวนเงินที่ขอเบิก", "component": "budget_preview_matcher", "field": "required_amount", "detail": {}})

        canonical_utility_type = BudgetPreviewMatcher.categorize_utility(expense_group) if expense_group else "unknown"
        wht_rule = BudgetPreviewMatcher.get_withholding_tax(canonical_utility_type)

        case_obj = {
            "case_id": case_facts.get("case_id"),
            "fiscal_year_be": fiscal_year_be,
            "expense_type": expense_group or "",
            "canonical_utility_type": canonical_utility_type,
            "required_amount": required_amount
        }

        # Validate provider
        prov_class = BudgetPreviewMatcher.classify_provider(provider)
        if prov_class == "unknown":
            warnings.append("provider unknown")
            warning_details.append({"code": "PROVIDER_UNKNOWN", "level": "warning", "message": "ไม่รู้จักผู้ให้บริการ", "component": "budget_preview_matcher", "field": "provider", "detail": {"provider": provider}})
        elif prov_class == "nt_ambiguous":
            warnings.append("NT ambiguous")
            warning_details.append({"code": "AMBIGUOUS_NT_PROVIDER", "level": "warning", "message": "ระบุเพียง NT อาจกำกวมระหว่างโทรศัพท์กับอินเทอร์เน็ต", "component": "budget_preview_matcher", "field": "provider", "detail": {"provider": provider}})
        elif canonical_utility_type == "electricity" and prov_class in ["phone", "internet", "water"]:
            blockers.append("selected electricity but provider/bill clearly phone/internet/water")
            blocker_details.append({"code": "UTILITY_PROVIDER_MISMATCH", "level": "blocker", "message": "กลุ่มค่าใช้จ่ายกับผู้ให้บริการไม่สอดคล้องกัน", "component": "budget_preview_matcher", "field": "provider", "detail": {"expense": canonical_utility_type, "provider": prov_class}})
        elif canonical_utility_type in ["phone", "internet", "water"] and prov_class == "electricity":
            # Just keeping symmetry for the general rule
            pass

        budget_match = {
            "match_status": "no_match",
            "preview_row_id": None,
            "source_row": None,
            "expense_type": None,
            "canonical_utility_type": None,
            "work": None,
            "appropriation_category": None,
            "budget_code": None,
            "remaining_amount": None
        }

        rows = batch.get("rows", [])
        if not rows:
            blockers.append("no preview rows")
            blocker_details.append({"code": "NO_PREVIEW_ROWS", "level": "blocker", "message": "ไม่มีข้อมูลงบประมาณในระบบ", "component": "budget_preview_matcher", "field": "batch", "detail": {}})
        
        batch_fy = batch.get("metadata", {}).get("fiscal_year_be")

        matched_rows = []
        for r in rows:
            ext = r.get("extracted", {})
            r_exp = ext.get("expense_type", "")
            r_canon = BudgetPreviewMatcher.categorize_utility(r_exp)
            if r_canon == canonical_utility_type and r_canon != "unknown":
                if fiscal_year_be and batch_fy and fiscal_year_be == batch_fy:
                    matched_rows.append(r)

        if not matched_rows and canonical_utility_type != "unknown" and fiscal_year_be:
            if not any(b == "no preview rows" for b in blockers):
                blockers.append("no matching preview row for fiscal year + utility category")
                blocker_details.append({"code": "NO_MATCHING_PREVIEW_ROW", "level": "blocker", "message": "ไม่พบรายการงบประมาณที่ตรงกับกลุ่มค่าใช้จ่าย", "component": "budget_preview_matcher", "field": "budget_match", "detail": {"canonical_utility_type": canonical_utility_type, "fiscal_year_be": fiscal_year_be}})

        if canonical_utility_type in ["phone", "internet", "water"] and len(matched_rows) > 0:
            for mr in matched_rows:
                if BudgetPreviewMatcher.categorize_utility(mr.get("extracted", {}).get("expense_type", "")) == "electricity":
                    blockers.append("selected phone/internet/water but matched row is electricity")
                    blocker_details.append({"code": "UTILITY_PROVIDER_MISMATCH", "level": "blocker", "message": "กลุ่มค่าใช้จ่ายไม่ตรงกับรายการงบประมาณ", "component": "budget_preview_matcher", "field": "expense_group", "detail": {"matched": "electricity"}})

        if len(matched_rows) > 1:
            warnings.append("multiple matching rows")
            warning_details.append({"code": "MULTIPLE_MATCHING_ROWS", "level": "warning", "message": "พบรายการงบประมาณที่เข้าข่ายหลายรายการ", "component": "budget_preview_matcher", "field": "budget_match", "detail": {"count": len(matched_rows)}})
            budget_match["match_status"] = "multiple"
        elif len(matched_rows) == 1:
            r = matched_rows[0]
            budget_match["match_status"] = "matched"
            budget_match["preview_row_id"] = r.get("preview_row_id") or r.get("id")
            budget_match["source_row"] = r.get("source_row")
            ext = r.get("extracted", {})
            budget_match["expense_type"] = ext.get("expense_type")
            budget_match["canonical_utility_type"] = BudgetPreviewMatcher.categorize_utility(ext.get("expense_type", ""))
            budget_match["work"] = ext.get("work")
            budget_match["appropriation_category"] = ext.get("appropriation_category")
            budget_match["budget_code"] = ext.get("budget_code")
            budget_match["remaining_amount"] = ext.get("remaining_amount")

            if budget_match["remaining_amount"] is None:
                blockers.append("matching row has missing remaining_amount")
                blocker_details.append({"code": "MISSING_REMAINING_AMOUNT", "level": "blocker", "message": "ไม่พบงบคงเหลือในระบบ", "component": "budget_preview_matcher", "field": "remaining_amount", "detail": {}})
            elif required_amount is not None and required_amount > budget_match["remaining_amount"]:
                blockers.append("required_amount > remaining_amount")
                blocker_details.append({"code": "INSUFFICIENT_REMAINING_AMOUNT", "level": "blocker", "message": "ยอดขอเบิกมากกว่างบคงเหลือ", "component": "budget_preview_matcher", "field": "required_amount", "detail": {"required": required_amount, "remaining": budget_match["remaining_amount"]}})
                
            placeholders = r.get("placeholders", {})
            if placeholders.get("department") == "รอข้อมูลจริง" or placeholders.get("plan") == "รอข้อมูลจริง" or placeholders.get("budget") == "รอข้อมูลจริง":
                warnings.append("department/plan/budget are \"รอข้อมูลจริง\"")
                warning_details.append({"code": "PLACEHOLDER_MAPPING_FIELDS", "level": "warning", "message": "หน่วยงาน แผนงาน หรืองบ เป็นข้อมูลรอการตรวจสอบ", "component": "budget_preview_matcher", "field": "budget_match", "detail": {}})

        status = "ready"
        ready = True
        
        if blockers:
            status = "blocked"
            ready = False
        elif warnings and status == "ready":
            status = "warning"

        if missing_data:
            status = "missing_data"
            ready = False
            if budget_match["match_status"] == "no_match":
                budget_match["match_status"] = "missing_data"

        # Unique lists for plain strings (preserving original shape)
        blockers = list(dict.fromkeys(blockers))
        warnings = list(dict.fromkeys(warnings))
        missing_data = list(dict.fromkeys(missing_data))

        evidence = {
            "source_file": batch.get("metadata", {}).get("source_file"),
            "source_sheet": batch.get("metadata", {}).get("source_sheet"),
            "source_hash": batch.get("metadata", {}).get("source_hash"),
            "preview_row_id": budget_match.get("preview_row_id"),
            "source_row": budget_match.get("source_row"),
            "match_basis": ["fiscal_year_be", "canonical_utility_type"],
            "ignored_warning_only_fields": ["department", "plan", "budget"]
        }

        return {
            "status": status,
            "ready": ready,
            "case": case_obj,
            "budget_match": budget_match,
            "withholding_tax": wht_rule,
            "blockers": blockers,
            "warnings": warnings,
            "missing_data": missing_data,
            "blocker_details": blocker_details,
            "warning_details": warning_details,
            "missing_data_details": missing_data_details,
            "evidence": evidence
        }
