import re

class CleanupService:
    @staticmethod
    def cleanup(text):
        # O -> 0, l -> 1
        text = text.replace('O', '0').replace('l', '1')
        
        # Remove duplicate spaces
        text = re.sub(r' +', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
