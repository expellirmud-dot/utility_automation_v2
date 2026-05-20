from datetime import date

def get_thai_fiscal_year(input_date: date) -> int:
    """
    Deterministically calculates the Thai fiscal year for a given date.
    The Thai fiscal year runs from October 1st to September 30th.
    If the date is in Oct, Nov, or Dec, it belongs to the *next* calendar year's fiscal year.
    Thai year (B.E.) is Gregorian Year + 543.
    """
    year = input_date.year
    month = input_date.month
    
    # If the month is October (10), November (11), or December (12), 
    # it belongs to the next fiscal year.
    if month >= 10:
        year += 1
        
    return year + 543
