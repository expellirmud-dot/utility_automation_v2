from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime

from src.tools.runtime.runtime_task_status import get_all_runtime_tasks
from src.tools.runtime.inspect_runtime_contract import inspect_contract_lifecycle

runtime_console_router = APIRouter(prefix="/ops/api", tags=["Runtime Console"])

class RuntimeTaskSummaryResponse(BaseModel):
    timestamp: str
    count: int
    tasks: List[dict[str, Any]]

class RuntimeContractDetailResponse(BaseModel):
    task: dict[str, Any]

@runtime_console_router.get("/runtime-tasks", response_model=RuntimeTaskSummaryResponse)
def get_runtime_tasks(state: Optional[str] = None) -> RuntimeTaskSummaryResponse:
    """
    Read-only operator surface for inspecting all runtime tasks.
    """
    tasks = get_all_runtime_tasks(contracts_dir="ai_runtime/contracts", reports_dir="ai_runtime/reports", state_filter=state)
    return RuntimeTaskSummaryResponse(
        timestamp=datetime.now().isoformat(),
        count=len(tasks),
        tasks=tasks
    )

@runtime_console_router.get("/runtime-tasks/{task_id}", response_model=RuntimeContractDetailResponse)
def get_runtime_task_detail(task_id: str) -> RuntimeContractDetailResponse:
    """
    Read-only operator surface for inspecting a specific runtime execution contract and its evidence.
    """
    detail = inspect_contract_lifecycle(task_id, contracts_dir="ai_runtime/contracts", reports_dir="ai_runtime/reports")
    return RuntimeContractDetailResponse(task=detail)
