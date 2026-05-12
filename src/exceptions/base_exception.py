import time
from datetime import datetime

class BasePipelineException(Exception):
    def __init__(self, message, source_file, pipeline_stage, provider_name=None):
        super().__init__(message)
        self.source_file = source_file
        self.pipeline_stage = pipeline_stage
        self.provider_name = provider_name
        self.timestamp = datetime.now().isoformat()

class OCRException(BasePipelineException): pass
class ExtractionException(BasePipelineException): pass
class ValidationException(BasePipelineException): pass
class AIValidationException(BasePipelineException): pass
class SerializationException(BasePipelineException): pass
class PipelineException(BasePipelineException): pass
