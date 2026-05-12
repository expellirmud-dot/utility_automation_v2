from typing import Optional
import re
from datetime import datetime

class DateParser:
    THAI_MONTHS = {
        'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
        'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
        'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
    }

    @staticmethod
    def parse(text: str) -> Optional[str]:
        # Handle format: 01/04/2569
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if match:
            day, month, year = match.groups()
            y = int(year) - 543
            return f"{y}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Handle format: 1 เม.ย. 69
        for month_name, month_num in DateParser.THAI_MONTHS.items():
            if month_name in text:
                match = re.search(r'(\d{1,2})\s+' + month_name + r'\s+(\d{2})', text)
                if match:
                    day, year = match.groups()
                    y = int(year) + 2500 - 543
                    return f"{y}-{month_num}-{day.zfill(2)}"
        
        return None
