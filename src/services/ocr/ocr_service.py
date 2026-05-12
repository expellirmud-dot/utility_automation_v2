import pytesseract
from PIL import Image
import io

class OCRService:
    @staticmethod
    def perform_ocr(image_bytes, lang='tha', dpi=300):
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Grayscale preprocessing
        image = image.convert('L')
        
        # Run Tesseract
        text = pytesseract.image_to_string(image, lang=lang)
        return text
