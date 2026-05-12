import os
from src.services.classification.ocr_header_extractor import OCRSpatialExtractor
from src.services.classification.template_fingerprint import TemplateFingerprint
from src.services.classification.confidence_scorer import ConfidenceScorer

class ProviderDetectorV2:
    PROVIDERS = {
        "NT": ["MEA", "Metropolitan Electricity", "การไฟฟ้านครหลวง"],
        "PEA": ["PEA", "Provincial Electricity", "การไฟฟ้าส่วนภูมิภาค"],
        "Water": ["PWA", "Waterworks", "การประปา"]
    }

    @staticmethod
    def detect(pdf_path):
        spatial_blocks = OCRSpatialExtractor.extract_spatial_text(pdf_path)
        layout_data = TemplateFingerprint.get_layout_intelligence(pdf_path)
        
        # Aggregate text for keyword/ocr signals
        full_text = " ".join([b[4] for b in spatial_blocks])
        filename = os.path.basename(pdf_path)
        
        results = {}
        for provider, keywords in ProviderDetectorV2.PROVIDERS.items():
            ocr_score = 1.0 if any(k in full_text for k in keywords) else 0.0
            kw_score = 1.0 if any(k in full_text or k in filename for k in keywords) else 0.0
            
            # Layout signal: map density to score
            layout_score = layout_data["header_density"] * 2 
            filename_score = 1.0 if provider in filename.upper() else 0.0
            
            signals = {"ocr": ocr_score, "keyword": kw_score, "layout": layout_score, "filename": filename_score}
            results[provider] = {"score": ConfidenceScorer.calculate(signals), "signals": signals}
            
        best_provider = max(results, key=lambda p: results[p]["score"])
        return {"provider": best_provider, **results[best_provider]}
