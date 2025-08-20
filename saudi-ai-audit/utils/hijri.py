"""
Hijri calendar utilities for Saudi AI Audit Platform
hijri-converter integration with Ramadan and Islamic calendar handling
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, Tuple
import calendar
from hijri_converter import Hijri, Gregorian, convert

# Islamic months in Arabic
HIJRI_MONTHS_AR = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الثانية",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
]

# Islamic months in English
HIJRI_MONTHS_EN = [
    "Muharram", "Safar", "Rabi' al-awwal", "Rabi' al-thani", "Jumada al-awwal", "Jumada al-thani",
    "Rajab", "Sha'ban", "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"
]

# Special Islamic periods
SACRED_MONTHS = [1, 7, 11, 12]  # Muharram, Rajab, Dhu al-Qi'dah, Dhu al-Hijjah
RAMADAN_MONTH = 9
HAJJ_MONTHS = [10, 11, 12]  # Shawwal, Dhu al-Qi'dah, Dhu al-Hijjah

# Saudi timezone offset (UTC+3)
SAUDI_TZ_OFFSET = 3

def get_hijri_date(gregorian_date: Optional[datetime] = None) -> str:
    """
    Convert Gregorian date to Hijri format (YYYY-MM-DD)
    
    Args:
        gregorian_date: Gregorian date to convert (default: today)
        
    Returns:
        Hijri date in YYYY-MM-DD format
    """
    
    if gregorian_date is None:
        gregorian_date = datetime.now()
    
    if isinstance(gregorian_date, datetime):
        greg_date = gregorian_date.date()
    else:
        greg_date = gregorian_date
    
    try:
        hijri_date = convert.Gregorian(greg_date.year, greg_date.month, greg_date.day).to_hijri()
        return f"{hijri_date.year:04d}-{hijri_date.month:02d}-{hijri_date.day:02d}"
    except Exception:
        # Fallback for invalid dates
        return "1445-01-01"

def get_hijri_date_formatted(gregorian_date: Optional[datetime] = None, include_weekday: bool = False) -> Dict[str, str]:
    """
    Get formatted Hijri date with Arabic month names
    
    Args:
        gregorian_date: Gregorian date to convert
        include_weekday: Include weekday name
        
    Returns:
        Dictionary with formatted Hijri date information
    """
    
    if gregorian_date is None:
        gregorian_date = datetime.now()
    
    if isinstance(gregorian_date, datetime):
        greg_date = gregorian_date.date()
    else:
        greg_date = gregorian_date
    
    try:
        hijri_date = convert.Gregorian(greg_date.year, greg_date.month, greg_date.day).to_hijri()
        
        result = {
            "hijri_iso": f"{hijri_date.year:04d}-{hijri_date.month:02d}-{hijri_date.day:02d}",
            "hijri_formatted_ar": f"{hijri_date.day} {HIJRI_MONTHS_AR[hijri_date.month - 1]} {hijri_date.year}",
            "hijri_formatted_en": f"{hijri_date.day} {HIJRI_MONTHS_EN[hijri_date.month - 1]} {hijri_date.year}",
            "month_ar": HIJRI_MONTHS_AR[hijri_date.month - 1],
            "month_en": HIJRI_MONTHS_EN[hijri_date.month - 1],
            "year": hijri_date.year,
            "month": hijri_date.month,
            "day": hijri_date.day
        }
        
        if include_weekday:
            weekday_ar = get_arabic_weekday(gregorian_date.weekday() if isinstance(gregorian_date, datetime) else greg_date.weekday())
            result["weekday_ar"] = weekday_ar
        
        return result
        
    except Exception as e:
        return {
            "hijri_iso": "1445-01-01",
            "hijri_formatted_ar": "1 محرم 1445",
            "hijri_formatted_en": "1 Muharram 1445",
            "error": str(e)
        }

def hijri_to_gregorian(hijri_date_str: str) -> Optional[date]:
    """
    Convert Hijri date string to Gregorian date
    
    Args:
        hijri_date_str: Hijri date in YYYY-MM-DD format
        
    Returns:
        Gregorian date or None if conversion fails
    """
    
    try:
        year, month, day = map(int, hijri_date_str.split('-'))
        hijri_date = Hijri(year, month, day)
        gregorian_date = hijri_date.to_gregorian()
        return date(gregorian_date.year, gregorian_date.month, gregorian_date.day)
    except Exception:
        return None

def is_ramadan_period(check_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Check if given date falls during Ramadan
    
    Args:
        check_date: Date to check (default: today)
        
    Returns:
        Dictionary with Ramadan period information
    """
    
    if check_date is None:
        check_date = datetime.now()
    
    hijri_info = get_hijri_date_formatted(check_date)
    hijri_month = hijri_info.get("month", 0)
    
    result = {
        "is_ramadan": hijri_month == RAMADAN_MONTH,
        "hijri_month": hijri_month,
        "month_name_ar": hijri_info.get("month_ar", ""),
        "month_name_en": hijri_info.get("month_en", "")
    }
    
    if result["is_ramadan"]:
        # Calculate Ramadan start and end (approximate)
        current_hijri_year = hijri_info.get("year", 1445)
        ramadan_start = hijri_to_gregorian(f"{current_hijri_year}-09-01")
        ramadan_end = hijri_to_gregorian(f"{current_hijri_year}-09-30")  # Ramadan can be 29 or 30 days
        
        result.update({
            "ramadan_start": ramadan_start.isoformat() if ramadan_start else None,
            "ramadan_end": ramadan_end.isoformat() if ramadan_end else None,
            "days_remaining": None
        })
        
        if ramadan_end and check_date.date() <= ramadan_end:
            result["days_remaining"] = (ramadan_end - check_date.date()).days
    
    return result

def is_sacred_month(check_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Check if given date falls during a sacred Islamic month
    
    Args:
        check_date: Date to check (default: today)
        
    Returns:
        Dictionary with sacred month information
    """
    
    if check_date is None:
        check_date = datetime.now()
    
    hijri_info = get_hijri_date_formatted(check_date)
    hijri_month = hijri_info.get("month", 0)
    
    return {
        "is_sacred_month": hijri_month in SACRED_MONTHS,
        "sacred_months": SACRED_MONTHS,
        "current_month": hijri_month,
        "month_name_ar": hijri_info.get("month_ar", ""),
        "month_name_en": hijri_info.get("month_en", ""),
        "special_considerations": get_sacred_month_considerations(hijri_month)
    }

def is_hajj_season(check_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Check if given date falls during Hajj season
    
    Args:
        check_date: Date to check (default: today)
        
    Returns:
        Dictionary with Hajj season information
    """
    
    if check_date is None:
        check_date = datetime.now()
    
    hijri_info = get_hijri_date_formatted(check_date)
    hijri_month = hijri_info.get("month", 0)
    
    return {
        "is_hajj_season": hijri_month in HAJJ_MONTHS,
        "hajj_months": HAJJ_MONTHS,
        "current_month": hijri_month,
        "month_name_ar": hijri_info.get("month_ar", ""),
        "month_name_en": hijri_info.get("month_en", ""),
        "hajj_considerations": get_hajj_considerations(hijri_month)
    }

def get_arabic_weekday(weekday_num: int) -> str:
    """
    Get Arabic name for weekday
    
    Args:
        weekday_num: Weekday number (0=Monday, 6=Sunday)
        
    Returns:
        Arabic weekday name
    """
    
    arabic_weekdays = [
        "الاثنين",    # Monday
        "الثلاثاء",   # Tuesday  
        "الأربعاء",   # Wednesday
        "الخميس",    # Thursday
        "الجمعة",    # Friday
        "السبت",     # Saturday
        "الأحد"      # Sunday
    ]
    
    if 0 <= weekday_num <= 6:
        return arabic_weekdays[weekday_num]
    else:
        return "غير محدد"

def calculate_age_hijri(birth_date_hijri: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate age based on Hijri birth date
    
    Args:
        birth_date_hijri: Birth date in Hijri format (YYYY-MM-DD)
        reference_date: Reference date for calculation (default: today)
        
    Returns:
        Age calculation result
    """
    
    if reference_date is None:
        reference_date = datetime.now()
    
    try:
        # Convert birth date to Gregorian
        birth_gregorian = hijri_to_gregorian(birth_date_hijri)
        if not birth_gregorian:
            raise ValueError("Invalid Hijri birth date")
        
        # Calculate age in Gregorian calendar
        ref_date = reference_date.date() if isinstance(reference_date, datetime) else reference_date
        age_days = (ref_date - birth_gregorian).days
        age_years = age_days // 365
        
        # Convert current date to Hijri for Hijri age calculation
        current_hijri = get_hijri_date_formatted(reference_date)
        birth_hijri_parts = birth_date_hijri.split('-')
        birth_year = int(birth_hijri_parts[0])
        birth_month = int(birth_hijri_parts[1])
        birth_day = int(birth_hijri_parts[2])
        
        hijri_age_years = current_hijri["year"] - birth_year
        
        # Adjust for month/day if birthday hasn't occurred this year
        if (current_hijri["month"] < birth_month or 
            (current_hijri["month"] == birth_month and current_hijri["day"] < birth_day)):
            hijri_age_years -= 1
        
        return {
            "age_gregorian_years": age_years,
            "age_hijri_years": hijri_age_years,
            "age_days": age_days,
            "birth_date_hijri": birth_date_hijri,
            "birth_date_gregorian": birth_gregorian.isoformat(),
            "reference_date_hijri": current_hijri["hijri_iso"],
            "reference_date_gregorian": ref_date.isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "birth_date_hijri": birth_date_hijri
        }

def get_fiscal_year_hijri(check_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get Saudi fiscal year information based on Hijri calendar
    
    Args:
        check_date: Date to check (default: today)
        
    Returns:
        Fiscal year information
    """
    
    if check_date is None:
        check_date = datetime.now()
    
    hijri_info = get_hijri_date_formatted(check_date)
    hijri_year = hijri_info.get("year", 1445)
    hijri_month = hijri_info.get("month", 1)
    
    # Saudi fiscal year typically starts in Muharram (month 1)
    if hijri_month >= 1:
        fiscal_year = hijri_year
    else:
        fiscal_year = hijri_year - 1
    
    # Calculate fiscal year boundaries
    fiscal_start_hijri = f"{fiscal_year}-01-01"
    fiscal_end_hijri = f"{fiscal_year}-12-30"  # Approximate
    
    fiscal_start_gregorian = hijri_to_gregorian(fiscal_start_hijri)
    fiscal_end_gregorian = hijri_to_gregorian(fiscal_end_hijri)
    
    return {
        "fiscal_year_hijri": fiscal_year,
        "fiscal_start_hijri": fiscal_start_hijri,
        "fiscal_end_hijri": fiscal_end_hijri,
        "fiscal_start_gregorian": fiscal_start_gregorian.isoformat() if fiscal_start_gregorian else None,
        "fiscal_end_gregorian": fiscal_end_gregorian.isoformat() if fiscal_end_gregorian else None,
        "current_quarter": get_hijri_quarter(hijri_month),
        "days_in_fiscal_year": calculate_hijri_year_days(fiscal_year)
    }

def get_hijri_quarter(hijri_month: int) -> int:
    """
    Get Hijri calendar quarter for given month
    
    Args:
        hijri_month: Hijri month (1-12)
        
    Returns:
        Quarter number (1-4)
    """
    
    if 1 <= hijri_month <= 3:
        return 1
    elif 4 <= hijri_month <= 6:
        return 2
    elif 7 <= hijri_month <= 9:
        return 3
    elif 10 <= hijri_month <= 12:
        return 4
    else:
        return 1

def calculate_hijri_year_days(hijri_year: int) -> int:
    """
    Calculate number of days in Hijri year (354 or 355 days)
    
    Args:
        hijri_year: Hijri year
        
    Returns:
        Number of days in the year
    """
    
    # Hijri years alternate between 354 and 355 days
    # This is a simplified calculation
    if hijri_year % 2 == 0:
        return 354
    else:
        return 355

def get_sacred_month_considerations(hijri_month: int) -> List[str]:
    """
    Get special considerations for sacred months
    
    Args:
        hijri_month: Hijri month number
        
    Returns:
        List of considerations
    """
    
    considerations = []
    
    if hijri_month == 1:  # Muharram
        considerations.extend([
            "الشهر الحرام الأول",
            "تجنب القرارات المثيرة للجدل",
            "موسم التخطيط السنوي"
        ])
    elif hijri_month == 7:  # Rajab
        considerations.extend([
            "من الأشهر الحرم",
            "شهر الإعداد لرمضان"
        ])
    elif hijri_month == 9:  # Ramadan
        considerations.extend([
            "شهر رمضان المبارك",
            "ساعات عمل مختصرة",
            "تجنب الأنشطة المكثفة"
        ])
    elif hijri_month == 11:  # Dhu al-Qi'dah
        considerations.extend([
            "من الأشهر الحرم",
            "بداية موسم الحج"
        ])
    elif hijri_month == 12:  # Dhu al-Hijjah
        considerations.extend([
            "من الأشهر الحرم",
            "موسم الحج",
            "عيد الأضحى"
        ])
    
    return considerations

def get_hajj_considerations(hijri_month: int) -> List[str]:
    """
    Get Hajj season considerations
    
    Args:
        hijri_month: Hijri month number
        
    Returns:
        List of Hajj considerations
    """
    
    considerations = []
    
    if hijri_month == 10:  # Shawwal
        considerations.extend([
            "بداية أشهر الحج",
            "عيد الفطر في بداية الشهر"
        ])
    elif hijri_month == 11:  # Dhu al-Qi'dah
        considerations.extend([
            "ذو القعدة - شهر الحج",
            "استعدادات الحج",
            "زيادة السفر إلى مكة"
        ])
    elif hijri_month == 12:  # Dhu al-Hijjah
        considerations.extend([
            "ذو الحجة - موسم الحج",
            "عيد الأضحى",
            "إجازات ممتدة",
            "تجنب القرارات الحكومية المهمة"
        ])
    
    return considerations

def validate_hijri_date(hijri_date_str: str) -> Dict[str, Any]:
    """
    Validate Hijri date string format and values
    
    Args:
        hijri_date_str: Hijri date in YYYY-MM-DD format
        
    Returns:
        Validation result
    """
    
    result = {
        "valid": False,
        "errors": [],
        "normalized_date": "",
        "gregorian_equivalent": None
    }
    
    try:
        # Check format
        if not hijri_date_str or not isinstance(hijri_date_str, str):
            result["errors"].append("تاريخ هجري مطلوب")
            return result
        
        # Check pattern
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', hijri_date_str):
            result["errors"].append("صيغة التاريخ الهجري يجب أن تكون YYYY-MM-DD")
            return result
        
        # Parse components
        year, month, day = map(int, hijri_date_str.split('-'))
        
        # Validate ranges
        if year < 1000 or year > 2000:  # Reasonable range
            result["errors"].append(f"السنة الهجرية غير صحيحة: {year}")
        
        if month < 1 or month > 12:
            result["errors"].append(f"الشهر الهجري غير صحيح: {month}")
        
        if day < 1 or day > 30:  # Hijri months are max 30 days
            result["errors"].append(f"اليوم الهجري غير صحيح: {day}")
        
        if result["errors"]:
            return result
        
        # Test conversion
        gregorian_date = hijri_to_gregorian(hijri_date_str)
        if not gregorian_date:
            result["errors"].append("فشل في تحويل التاريخ الهجري")
            return result
        
        result.update({
            "valid": True,
            "normalized_date": hijri_date_str,
            "gregorian_equivalent": gregorian_date.isoformat(),
            "month_name_ar": HIJRI_MONTHS_AR[month - 1],
            "month_name_en": HIJRI_MONTHS_EN[month - 1]
        })
        
    except Exception as e:
        result["errors"].append(f"خطأ في معالجة التاريخ الهجري: {str(e)}")
    
    return result

def get_current_saudi_time() -> datetime:
    """
    Get current time in Saudi Arabia timezone (UTC+3)
    
    Returns:
        Current Saudi time
    """
    
    utc_time = datetime.utcnow()
    saudi_time = utc_time + timedelta(hours=SAUDI_TZ_OFFSET)
    return saudi_time

def format_government_date(date_obj: datetime, include_hijri: bool = True, include_time: bool = False) -> Dict[str, str]:
    """
    Format date for government documents
    
    Args:
        date_obj: Date to format
        include_hijri: Include Hijri date
        include_time: Include time
        
    Returns:
        Formatted date strings
    """
    
    result = {
        "gregorian_date_ar": "",
        "gregorian_date_en": "",
        "hijri_date_ar": "",
        "hijri_date_en": "",
        "combined_ar": "",
        "combined_en": ""
    }
    
    # Gregorian formatting
    greg_ar = f"{date_obj.day}/{date_obj.month}/{date_obj.year}"
    greg_en = date_obj.strftime("%d/%m/%Y")
    
    if include_time:
        time_str = date_obj.strftime("%H:%M")
        greg_ar += f" الساعة {time_str}"
        greg_en += f" at {time_str}"
    
    result["gregorian_date_ar"] = greg_ar
    result["gregorian_date_en"] = greg_en
    
    if include_hijri:
        hijri_info = get_hijri_date_formatted(date_obj)
        result["hijri_date_ar"] = hijri_info.get("hijri_formatted_ar", "")
        result["hijri_date_en"] = hijri_info.get("hijri_formatted_en", "")
        
        result["combined_ar"] = f"{greg_ar} الموافق {result['hijri_date_ar']}"
        result["combined_en"] = f"{greg_en} corresponding to {result['hijri_date_en']}"
    else:
        result["combined_ar"] = greg_ar
        result["combined_en"] = greg_en
    
    return result