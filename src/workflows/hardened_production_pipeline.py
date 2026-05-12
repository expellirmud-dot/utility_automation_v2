import time
from src.exceptions.base_exception import OCRException, ExtractionException, ValidationException
from src.services.diagnostics.failure_snapshot_service import FailureSnapshotService
from src.models.pipeline_metrics import FailureSnapshot
from src.workflows.production_pipeline import ProductionPipeline

class HardenedProductionPipeline:
    @staticmethod
    def process_file(pdf_path):
        try:
            # Wrap standard production pipeline execution
            return ProductionPipeline.run(pdf_path)
        except Exception as e:
            # Create snapshot
            snapshot = FailureSnapshot(
                source_file=pdf_path,
                pipeline_stage=getattr(e, 'pipeline_stage', 'unknown'),
                error=str(e)
            )
            FailureSnapshotService.export(snapshot)
            return None
