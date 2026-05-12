from src.services.event_sourcing.event_sourcing_service import EventSourcingService
from datetime import datetime, timezone
from src.models.event_model import DomainEvent
import uuid
import dataclasses

class IntegratedPipeline:
    def __init__(self, semantic_pipeline, governance):
        self.semantic = semantic_pipeline
        self.governance = governance
        self.event_service = EventSourcingService()

    def process(self, input_data):
        result = self.semantic.process_with_governance(input_data)

        # Ensure safe serialization of result object
        payload = {}
        for k, v in result.items():
            if hasattr(v, "__dict__"):
                payload[k] = dataclasses.asdict(v) if dataclasses.is_dataclass(v) else v.__dict__
            elif isinstance(v, list):
                # handle basic lists safely
                payload[k] = v
            else:
                payload[k] = v

        aggregate_id = input_data.get("id", str(uuid.uuid4()))

        # emit event
        self.event_service.emit(
            DomainEvent(
                event_id=str(uuid.uuid4()),
                aggregate_id=aggregate_id,
                event_type="DECISION_MADE",
                payload=payload,
                timestamp=datetime.now(timezone.utc),
                version=1
            )
        )

        return result
