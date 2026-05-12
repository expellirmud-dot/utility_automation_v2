import time
from src.services.ocr.pdf_service import PDFService
from src.services.ocr.ocr_service import OCRService
from src.services.ocr.cleanup_service import CleanupService
from src.models.ocr_result import OCRResult

class ProcessPDFWorkflow:
    @staticmethod
    def run(pdf_path):
        start_time = time.time()
        
        pdf_doc = PDFService.open_pdf(pdf_path)
        page_count = len(pdf_doc)
        
        source_type = "text_layer"
        text = ""
        
        if PDFService.has_text_layer(pdf_doc):
            text = PDFService.extract_text(pdf_doc)
        else:
            source_type = "ocr"
            images = PDFService.render_pages_as_images(pdf_doc)
            for img_bytes in images:
                text += OCRService.perform_ocr(img_bytes)
        
        cleaned_text = CleanupService.cleanup(text)
        
        end_time = time.time()
        
        return OCRResult(
            source_type=source_type,
            extracted_text=cleaned_text,
            page_count=page_count,
            confidence_notes="High" if source_type == "text_layer" else "Medium",
            processing_time_ms=(end_time - start_time) * 1000
        )
