from typing import Optional
import re

class AmountParser:
    @staticmethod
    def parse(text: str) -> Optional[float]:
        # Replace O with 0 and l with 1
        clean_text = text.replace('O', '0').replace('l', '1')
        
        # Match digits, commas, and decimal points
        # Specifically look for common currency formatting
        # Exclude small numbers that might be dates (like 69 from the date)
        # For this prototype, keep it simple but improved
        matches = re.findall(r'(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', clean_text)
        
        if matches:
            val = matches[-1].replace(',', '')
            try:
                return float(val)
            except ValueError:
                return None
        return None
