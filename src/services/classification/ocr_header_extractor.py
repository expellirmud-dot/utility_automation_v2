import fitz

class OCRSpatialExtractor:
    @staticmethod
    def extract_spatial_text(pdf_path):
        doc = fitz.open(pdf_path)
        page = doc[0]
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, "text", block_no, block_type)
        doc.close()
        return blocks
