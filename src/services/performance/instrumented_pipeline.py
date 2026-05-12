class InstrumentedPipeline:
    def __init__(self, pipeline, telemetry):
        self.pipeline = pipeline
        self.telemetry = telemetry

    def process(self, input_data):
        with self.telemetry.time_block("OCR"):
            ocr = getattr(self.pipeline, 'ocr', lambda x: x)(input_data)

        with self.telemetry.time_block("EXTRACTION"):
            extracted = getattr(self.pipeline, 'extract', lambda x: x)(ocr)

        with self.telemetry.time_block("SEMANTIC"):
            semantic = getattr(self.pipeline, 'semantic', lambda x: x)(extracted)

        with self.telemetry.time_block("FINANCIAL"):
            financial = getattr(self.pipeline, 'financial', lambda x: x)(semantic)

        with self.telemetry.time_block("GOVERNANCE"):
            decision = getattr(self.pipeline, 'governance', lambda x: x)(financial)

        return decision
