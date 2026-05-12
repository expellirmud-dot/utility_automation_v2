import fitz  # PyMuPDF

class PDFService:
    @staticmethod
    def open_pdf(pdf_path):
        return fitz.open(pdf_path)

    @staticmethod
    def has_text_layer(pdf_document):
        for page in pdf_document:
            if page.get_text().strip():
                return True
        return False

    @staticmethod
    def extract_text(pdf_document):
        text = ""
        for page in pdf_document:
            text += page.get_text()
        return text

    @staticmethod
    def render_pages_as_images(pdf_document, dpi=300):
        images = []
        for page in pdf_document:
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            images.append(pix.tobytes("png"))
        return images
