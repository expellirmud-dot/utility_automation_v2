from src.workflows.production_pipeline import ProductionPipeline
from src.services.testing.sample_loader import SampleLoader
from src.services.logging.pipeline_logger import PipelineLogger

def run_regression():
    PipelineLogger.setup()
    samples = SampleLoader.get_all_samples()
    
    total = len(samples)
    success = 0
    
    for path in samples:
        try:
            res = ProductionPipeline.run(path)
            success += 1
            PipelineLogger.info(f"Processed {path} successfully.")
        except Exception as e:
            PipelineLogger.info(f"Failed {path}: {str(e)}")
            
    print(f"Regression complete. Total: {total}, Success: {success}")

if __name__ == "__main__":
    run_regression()
