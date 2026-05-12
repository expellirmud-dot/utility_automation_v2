import logging

class PipelineLogger:
    @staticmethod
    def setup():
        logging.basicConfig(
            filename='output/logs/pipeline.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    @staticmethod
    def info(msg):
        logging.info(msg)
