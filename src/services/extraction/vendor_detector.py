from typing import Optional

class VendorDetector:
    KEYWORDS = {
        'NT': ['NT', 'TOT', 'CAT'],
        'Electricity': ['การไฟฟ้า', 'กฟน', 'กฟภ'],
        'Water': ['การประปา', 'กปน', 'กปภ']
    }

    @staticmethod
    def detect(text: str) -> Optional[str]:
        for vendor, keywords in VendorDetector.KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return vendor
        return None
