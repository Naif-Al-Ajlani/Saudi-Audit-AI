"""
Arabic text processing utilities for Saudi AI Audit Platform
UTF-8-sig BOM handling, RTL markers, and government text processing
"""

import re
import unicodedata
from typing import Optional, List, Dict, Any
import arabic_reshaper
from bidi.algorithm import get_display

# Arabic character ranges and patterns
ARABIC_CHARS = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
ARABIC_NUMBERS = r'[\u0660-\u0669]'  # ٠١٢٣٤٥٦٧٨٩
LATIN_NUMBERS = r'[0-9]'

# Common Arabic prefixes and suffixes
ARABIC_PREFIXES = ['ال', 'و', 'ف', 'ب', 'ك', 'ل']
FAMILY_PREFIXES = ['آل', 'بني', 'أبو', 'بن', 'ابن', 'عبد']
TRIBAL_INDICATORS = ['آل', 'بني', 'قبيلة', 'عشيرة']

# Tashkeel (diacritics) marks
TASHKEEL = r'[\u064B-\u0652\u0670\u0640]'

# Government text cleaning patterns
GOVT_CLEANUP_PATTERNS = [
    (r'\s+', ' '),  # Multiple spaces to single space
    (r'^[\s\u200E\u200F]+|[\s\u200E\u200F]+$', ''),  # Trim spaces and RTL/LTR marks
    (r'[\u200B-\u200D\uFEFF]', ''),  # Remove zero-width characters
]

def format_bilingual_response(message_ar: str, message_en: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create standardized bilingual response format
    
    Args:
        message_ar: Arabic message
        message_en: English message
        data: Additional data
        
    Returns:
        Formatted bilingual response
    """
    
    response = {
        "message": {
            "ar": clean_arabic_text(message_ar),
            "en": message_en
        },
        "timestamp": {
            "iso": "",  # Will be filled by calling function
            "hijri": ""  # Will be filled by calling function
        }
    }
    
    if data:
        response["data"] = data
    
    return response

def clean_arabic_text(text: str) -> str:
    """
    Clean Arabic text for government compliance
    
    Args:
        text: Input Arabic text
        
    Returns:
        Cleaned Arabic text
    """
    
    if not text:
        return ""
    
    # Remove BOM if present
    text = remove_bom(text)
    
    # Remove tashkeel (diacritics) for consistency
    text = remove_tashkeel(text)
    
    # Apply government cleanup patterns
    for pattern, replacement in GOVT_CLEANUP_PATTERNS:
        text = re.sub(pattern, replacement, text)
    
    # Normalize Arabic text
    text = normalize_arabic_text(text)
    
    return text.strip()

def remove_bom(text: str) -> str:
    """
    Remove UTF-8 BOM and other BOMs
    
    Args:
        text: Input text
        
    Returns:
        Text without BOM
    """
    
    # UTF-8 BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    
    # UTF-16 BE BOM
    if text.startswith('\ufffe'):
        text = text[1:]
    
    # UTF-16 LE BOM  
    if text.startswith('\ufeff'):
        text = text[1:]
    
    return text

def remove_tashkeel(text: str) -> str:
    """
    Remove Arabic diacritics (tashkeel) marks
    
    Args:
        text: Arabic text with diacritics
        
    Returns:
        Text without diacritics
    """
    
    return re.sub(TASHKEEL, '', text)

def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text for consistent processing
    
    Args:
        text: Input Arabic text
        
    Returns:
        Normalized Arabic text
    """
    
    if not text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Normalize Arabic letters
    replacements = {
        'ي': 'ي',  # Normalize different forms of yaa
        'ى': 'ي',
        'ئ': 'ئ',
        'ؤ': 'ؤ',
        'إ': 'إ',
        'أ': 'أ',
        'آ': 'آ',
        'ة': 'ة',  # Taa marbuta
        'ه': 'ه',  # Regular haa
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def ensure_windows_1256_encoding(text: str) -> str:
    """
    Ensure text is compatible with Windows-1256 encoding (for Etimad)
    
    Args:
        text: Input text
        
    Returns:
        Windows-1256 compatible text
    """
    
    try:
        # Test if text can be encoded in Windows-1256
        text.encode('windows-1256')
        return text
    except UnicodeEncodeError:
        # Replace problematic characters
        safe_text = text.encode('windows-1256', errors='replace').decode('windows-1256')
        return safe_text

def ensure_encoding(text: str, target_encoding: str = 'utf-8') -> str:
    """
    Ensure text uses specified encoding
    
    Args:
        text: Input text
        target_encoding: Target encoding
        
    Returns:
        Properly encoded text
    """
    
    if not text:
        return ""
    
    try:
        # Test encoding
        encoded = text.encode(target_encoding)
        return encoded.decode(target_encoding)
    except UnicodeEncodeError:
        # Handle encoding errors
        return text.encode(target_encoding, errors='replace').decode(target_encoding)

def convert_arabic_to_latin(text: str) -> str:
    """
    Convert Arabic text to Latin transliteration (for SAP compatibility)
    
    Args:
        text: Arabic text
        
    Returns:
        Latin transliteration
    """
    
    if not text:
        return ""
    
    # Basic Arabic to Latin mapping
    transliteration_map = {
        'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h',
        'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's',
        'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': 'a',
        'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
        'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y', 'ة': 'h', 'ء': '',
        'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ؤ': 'w', 'ئ': 'y',
        ' ': ' ', '.': '.', ',': ',', '-': '-'
    }
    
    # Convert Arabic numbers to Latin
    arabic_to_latin_numbers = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    # Clean text first
    text = clean_arabic_text(text)
    
    result = ""
    for char in text:
        if char in transliteration_map:
            result += transliteration_map[char]
        elif char in arabic_to_latin_numbers:
            result += arabic_to_latin_numbers[char]
        elif char.isascii():
            result += char
        else:
            result += char  # Keep unknown characters as-is
    
    # Clean up the result
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def extract_family_name(full_name: str) -> Optional[str]:
    """
    Extract family name from Arabic full name (for bias detection)
    
    Args:
        full_name: Full Arabic name
        
    Returns:
        Family name if found, None otherwise
    """
    
    if not full_name:
        return None
    
    # Clean the name
    name = clean_arabic_text(full_name)
    
    # Split into parts
    name_parts = name.split()
    
    if len(name_parts) < 2:
        return None
    
    # Look for family prefixes
    for i, part in enumerate(name_parts):
        if part in FAMILY_PREFIXES and i + 1 < len(name_parts):
            return f"{part} {name_parts[i + 1]}"
    
    # If no prefix found, assume last part is family name
    return name_parts[-1]

def is_tribal_name(name: str) -> bool:
    """
    Check if name contains tribal indicators (sensitive function)
    
    Args:
        name: Name to check
        
    Returns:
        True if tribal indicators found
    """
    
    if not name:
        return False
    
    name = clean_arabic_text(name)
    
    # Check for tribal indicators
    for indicator in TRIBAL_INDICATORS:
        if indicator in name:
            return True
    
    return False

def add_rtl_markers(text: str) -> str:
    """
    Add RTL (Right-to-Left) markers for proper Arabic display
    
    Args:
        text: Arabic text
        
    Returns:
        Text with RTL markers
    """
    
    if not text or not contains_arabic(text):
        return text
    
    # Add RTL mark at the beginning
    rtl_mark = '\u200F'  # Right-to-Left Mark
    return f"{rtl_mark}{text}"

def remove_rtl_markers(text: str) -> str:
    """
    Remove RTL/LTR markers from text
    
    Args:
        text: Text with markers
        
    Returns:
        Text without markers
    """
    
    if not text:
        return ""
    
    # Remove RTL and LTR marks
    rtl_ltr_marks = r'[\u200E\u200F]'
    return re.sub(rtl_ltr_marks, '', text)

def contains_arabic(text: str) -> bool:
    """
    Check if text contains Arabic characters
    
    Args:
        text: Text to check
        
    Returns:
        True if Arabic characters found
    """
    
    if not text:
        return False
    
    return bool(re.search(ARABIC_CHARS, text))

def format_arabic_for_pdf(text: str) -> str:
    """
    Format Arabic text for PDF generation (ReportLab compatibility)
    
    Args:
        text: Arabic text
        
    Returns:
        PDF-ready Arabic text
    """
    
    if not text:
        return ""
    
    # Clean the text
    text = clean_arabic_text(text)
    
    # Reshape Arabic text for proper display
    reshaped_text = arabic_reshaper.reshape(text)
    
    # Apply bidirectional algorithm
    bidi_text = get_display(reshaped_text)
    
    return bidi_text

def validate_arabic_input(text: str, min_length: int = 1, max_length: int = 1000) -> Dict[str, Any]:
    """
    Validate Arabic input for government forms
    
    Args:
        text: Arabic text to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Returns:
        Validation result
    """
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "cleaned_text": ""
    }
    
    if not text:
        result["valid"] = False
        result["errors"].append("النص مطلوب")
        return result
    
    # Clean the text
    cleaned = clean_arabic_text(text)
    result["cleaned_text"] = cleaned
    
    # Length validation
    if len(cleaned) < min_length:
        result["valid"] = False
        result["errors"].append(f"النص قصير جداً (الحد الأدنى: {min_length} أحرف)")
    
    if len(cleaned) > max_length:
        result["valid"] = False
        result["errors"].append(f"النص طويل جداً (الحد الأقصى: {max_length} أحرف)")
    
    # Check for Arabic content
    if not contains_arabic(cleaned):
        result["warnings"].append("النص لا يحتوي على أحرف عربية")
    
    # Check for suspicious patterns
    if re.search(r'[<>{}]', cleaned):
        result["warnings"].append("النص يحتوي على رموز مشبوهة")
    
    return result

def convert_arabic_numbers_to_latin(text: str) -> str:
    """
    Convert Arabic-Indic numbers to Latin numbers
    
    Args:
        text: Text with Arabic numbers
        
    Returns:
        Text with Latin numbers
    """
    
    if not text:
        return ""
    
    arabic_to_latin = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    result = text
    for arabic, latin in arabic_to_latin.items():
        result = result.replace(arabic, latin)
    
    return result

def convert_latin_numbers_to_arabic(text: str) -> str:
    """
    Convert Latin numbers to Arabic-Indic numbers
    
    Args:
        text: Text with Latin numbers
        
    Returns:
        Text with Arabic numbers
    """
    
    if not text:
        return ""
    
    latin_to_arabic = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }
    
    result = text
    for latin, arabic in latin_to_arabic.items():
        result = result.replace(latin, arabic)
    
    return result

def get_text_direction(text: str) -> str:
    """
    Determine text direction (RTL/LTR)
    
    Args:
        text: Text to analyze
        
    Returns:
        'rtl' for Arabic/RTL text, 'ltr' for Latin/LTR text
    """
    
    if not text:
        return 'ltr'
    
    arabic_count = len(re.findall(ARABIC_CHARS, text))
    latin_count = len(re.findall(r'[a-zA-Z]', text))
    
    if arabic_count > latin_count:
        return 'rtl'
    else:
        return 'ltr'

def create_government_header_text(ministry: str, department: str, document_type: str) -> str:
    """
    Create standardized government document header in Arabic
    
    Args:
        ministry: Ministry name in Arabic
        department: Department name in Arabic
        document_type: Document type in Arabic
        
    Returns:
        Formatted header text
    """
    
    header_template = """المملكة العربية السعودية
{ministry}
{department}

{document_type}"""
    
    return header_template.format(
        ministry=clean_arabic_text(ministry),
        department=clean_arabic_text(department),
        document_type=clean_arabic_text(document_type)
    )

def mask_sensitive_arabic_text(text: str, mask_char: str = '*') -> str:
    """
    Mask sensitive parts of Arabic text (for logging)
    
    Args:
        text: Text to mask
        mask_char: Character to use for masking
        
    Returns:
        Masked text
    """
    
    if not text:
        return ""
    
    # Keep first and last 2 characters, mask the middle
    if len(text) <= 4:
        return mask_char * len(text)
    
    return f"{text[:2]}{mask_char * (len(text) - 4)}{text[-2:]}"

# Government-specific text processing
class GovernmentTextProcessor:
    """
    Specialized text processor for Saudi government documents
    """
    
    def __init__(self):
        self.ministry_abbreviations = {
            "وزارة التجارة": "وت",
            "وزارة المالية": "وم", 
            "وزارة الداخلية": "ود",
            "وزارة الخارجية": "وخ"
        }
        
        self.document_types = {
            "قرار": "Decision",
            "تقرير": "Report", 
            "عقد": "Contract",
            "مراسلة": "Correspondence"
        }
    
    def process_official_document(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Process official government document text
        
        Args:
            text: Document text
            document_type: Type of document
            
        Returns:
            Processing result
        """
        
        processed = {
            "original_text": text,
            "cleaned_text": clean_arabic_text(text),
            "document_type": document_type,
            "word_count": 0,
            "character_count": 0,
            "contains_sensitive_info": False,
            "validation_errors": []
        }
        
        cleaned = processed["cleaned_text"]
        processed["word_count"] = len(cleaned.split())
        processed["character_count"] = len(cleaned)
        
        # Check for sensitive information patterns
        sensitive_patterns = [
            r'رقم الهوية:\s*\d{10}',  # National ID
            r'رقم السجل:\s*\d{10}',   # Commercial Registration
            r'رقم الحساب:\s*\d+',     # Account number
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, cleaned):
                processed["contains_sensitive_info"] = True
                break
        
        return processed