from src.services.classification.ocr_header_extractor import OCRHeaderExtractor
from src.services.classification.template_fingerprint import TemplateFingerprint
from src.services.classification.confidence_scorer import ConfidenceScorer

class ProviderDetectorV1:
    PROVIDERS = {
        "NT": ["MEA", "Metropolitan Electricity", "การไฟฟ้านครหลวง"],
        "PEA": ["PEA", "Provincial Electricity", "การไฟฟ้าส่วนภูมิภาค"],
        "Water": ["PWA", "Waterworks", "การประปา"]
    }

    @staticmethod
    def detect(pdf_path):
        header_text = OCRHeaderExtractor.extract_header(pdf_path)
        filename = os.path.basename(pdf_path)
        
        results = {}
        for provider, keywords in ProviderDetectorV1.PROVIDERS.items():
            ocr_score = 1.0 if any(k in header_text for k in keywords) else 0.0
            kw_score = 1.0 if any(k in header_text or k in filename for k in keywords) else 0.0
            
            # Placeholder for layout score
            layout_score = 0.5 
            filename_score = 1.0 if provider in filename.upper() else 0.0
            
            signals = {"ocr": ocr_score, "keyword": kw_score, "layout": layout_score, "filename": filename_score}
            results[provider] = {"score": ConfidenceScorer.calculate(signals), "signals": signals}
            
        best_provider = max(results, key=lambda p: results[p]["score"])
        return {"provider": best_provider, **results[best_provider]}
import os
