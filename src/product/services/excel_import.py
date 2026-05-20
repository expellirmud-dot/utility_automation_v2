from typing import List, Dict, Any

from src.product.services.budget_import import BudgetImportService


class ExcelImportService:
    @staticmethod
    def parse_budget_lines(file_content: bytes) -> List[Dict[str, Any]]:
        preview = BudgetImportService.preview_budget_lines(
            file_content=file_content,
            fiscal_year_be=0,
            sheet_name=None,
        )
        if not preview["valid"]:
            raise ValueError("; ".join(preview["errors"]))
        return [
            {
                "department": row["department"],
                "division": row["division"],
                "expense_type": row["expense_type"],
                "appropriation_category": row["appropriation_category"],
                "initial_amount": row["initial_amount"],
            }
            for row in preview["rows"]
        ]
