from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime
import argparse

from src.tools.runtime.runtime_task_status import get_all_runtime_tasks
from src.tools.runtime.inspect_runtime_contract import inspect_contract_lifecycle
from src.tools.runtime.create_controller_request import create_controller_request
from src.tools.runtime.start_runtime_task import start_runtime_task
from src.tools.runtime.finish_runtime_task import finish_runtime_task

runtime_console_router = APIRouter(prefix="/ops/api", tags=["Runtime Console"])

class RuntimeTaskSummaryResponse(BaseModel):
    timestamp: str
    count: int
    tasks: List[dict[str, Any]]

class RuntimeContractDetailResponse(BaseModel):
    task: dict[str, Any]

class CreateTaskPayload(BaseModel):
    task_id: str
    title: str
    objective: str
    rationale: str
    scope: List[str]
    candidate_modules: List[str]
    tests: List[str]
    validation: List[str]
    acceptance: List[str]
    next_task: Optional[str] = None
    output_file: Optional[str] = None

class StartTaskPayload(BaseModel):
    task_id: str
    actor_id: str
    request_file: Optional[str] = None
    title: Optional[str] = None
    objective: Optional[str] = None
    rationale: Optional[str] = None
    scope: List[str] = Field(default_factory=list)
    candidate_modules: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)
    validation: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    next_task: Optional[str] = None
    allow_read: List[str] = Field(default_factory=list)
    allow_write: List[str] = Field(default_factory=list)
    expected_output: List[str] = Field(default_factory=list)
    allow_command: Optional[List[str]] = None
    forbid_pattern: Optional[List[str]] = None
    duration_mins: int = 60

class FinishTaskPayload(BaseModel):
    task_id: str
    worker_id: str
    actual_output: List[str]

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
def get_runtime_task_detail(task_id: str, include_contents: bool = False) -> RuntimeContractDetailResponse:
    """
    Read-only operator surface for inspecting a specific runtime execution contract and its evidence.
    """
    detail = inspect_contract_lifecycle(task_id, contracts_dir="ai_runtime/contracts", reports_dir="ai_runtime/reports", include_contents=include_contents)
    return RuntimeContractDetailResponse(task=detail)

@runtime_console_router.post("/runtime-tasks/create")
def api_create_task(payload: CreateTaskPayload) -> dict[str, Any]:
    args = argparse.Namespace(**payload.model_dump())
    result = create_controller_request(args)
    if result.get("status") == "FAILED":
        raise HTTPException(status_code=500, detail=result)
    return result

@runtime_console_router.post("/runtime-tasks/start")
def api_start_task(payload: StartTaskPayload) -> dict[str, Any]:
    args_dict = payload.model_dump()
    args_dict["inbox_dir"] = "ai_runtime/inbox"
    args_dict["contracts_dir"] = "ai_runtime/contracts"
    args = argparse.Namespace(**args_dict)
    
    result = start_runtime_task(args)
    if result.get("status") == "FAILED":
        raise HTTPException(status_code=500, detail=result)
    return result

@runtime_console_router.post("/runtime-tasks/finish")
def api_finish_task(payload: FinishTaskPayload) -> dict[str, Any]:
    args_dict = payload.model_dump()
    args_dict["reports_dir"] = "ai_runtime/reports"
    args_dict["contracts_dir"] = "ai_runtime/contracts"
    args_dict["root_dir"] = "."
    args = argparse.Namespace(**args_dict)
    
    result = finish_runtime_task(args)
    if result.get("status") == "FAILED":
        raise HTTPException(status_code=500, detail=result)
    return result
