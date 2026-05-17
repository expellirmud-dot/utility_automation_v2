import pytest
from src.services.governance.execution_contract.execution_contract_builder import ExecutionContractBuilder
from src.services.governance.execution_contract.execution_contract_models import ExecutionContract

def test_builder_fluent_api():
    builder = ExecutionContractBuilder(task_id="T-001", actor_id="A-001")
    contract = (
        builder.allow_read(["in1.txt", "in2.txt"])
               .allow_write(["out.txt"])
               .allow_command("ls")
               .forbid_pattern("rm -rf")
               .expect_output("out.txt")
               .set_duration(3600)
               .set_metadata("priority", "high")
               .build()
    )
    
    assert contract.task_id == "T-001"
    assert "in1.txt" in contract.scope.allowed_read_paths
    assert "out.txt" in contract.scope.allowed_write_paths
    assert "ls" in contract.scope.allowed_commands
    assert "rm -rf" in contract.scope.forbidden_patterns
    assert "out.txt" in contract.expected_outputs
    assert contract.scope.max_duration_seconds == 3600
    assert contract.metadata["priority"] == "high"
    assert contract.contract_id.startswith("CONT-")
