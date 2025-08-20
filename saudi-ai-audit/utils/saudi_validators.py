"""
Saudi Arabia specific validators for government compliance
National ID, Iqama, Commercial Registration, IBAN validation
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date

class SaudiValidators:
    """
    أدوات التحقق السعودية
    Saudi-specific validation utilities
    """

    @staticmethod
    def validate_national_id(id_number: str) -> bool:
        """
        التحقق من رقم الهوية الوطنية
        Validate Saudi National ID (10 digits with checksum)
        """
        if not id_number:
            return False
            
        # Clean the input
        clean_id = re.sub(r'\s+', '', id_number)
        
        # Check basic format: starts with 1 or 2, followed by 9 more digits
        if not re.match(r'^[12]\d{9}$', clean_id):
            return False
            
        # Checksum algorithm
        total = 0
        for i, digit in enumerate(clean_id[:-1]):
            if i % 2 == 0:
                doubled = int(digit) * 2
                total += doubled if doubled < 10 else doubled - 9
            else:
                total += int(digit)
                
        checksum = (10 - (total % 10)) % 10
        return checksum == int(clean_id[-1])

    @staticmethod
    def validate_iqama_number(iqama: str) -> bool:
        """
        التحقق من رقم الإقامة
        Validate Saudi Iqama (Residence) number
        """
        
    Returns:
        True if valid Iqama number
    """
    
        """
        التحقق من رقم الإقامة
        Validate Saudi Iqama (Residence) number
        """
        if not iqama or not isinstance(iqama, str):
            return False
        
        # Remove spaces and ensure it's exactly 10 digits
        clean_iqama = re.sub(r'\s+', '', iqama)
        
        if not re.match(r'^\d{10}$', clean_iqama):
            return False
        
        # First digit should be 3, 4, 5, 6, 7, 8, or 9 for residents
        if clean_iqama[0] not in ['3', '4', '5', '6', '7', '8', '9']:
            return False
        
        return SaudiValidators._validate_saudi_id_checksum(clean_iqama)

    @staticmethod
    def validate_commercial_registration(cr_number: str) -> bool:
    """
    Validate Saudi Commercial Registration number
    
    Args:
        cr_number: Commercial Registration number
        
    Returns:
        True if valid CR number
    """
    
        """
        التحقق من رقم السجل التجاري
        Validate Saudi Commercial Registration number
        """
        if not cr_number or not isinstance(cr_number, str):
            return False
        
        # Remove spaces and ensure it's exactly 10 digits
        clean_cr = re.sub(r'\s+', '', cr_number)
        
        if not re.match(r'^\d{10}$', clean_cr):
            return False
        
        # First digit typically indicates the region
        # Valid first digits: 1-9 (0 is not used)
        if clean_cr[0] == '0':
            return False
        
        # Additional validation could include region-specific checks
        return True

    @staticmethod
    def validate_iban(iban: str) -> bool:
    """
    Validate Saudi IBAN (International Bank Account Number)
    
    Args:
        iban: IBAN string
        
    Returns:
        True if valid Saudi IBAN
    """
    
        """
        التحقق من رقم الآيبان السعودي
        Validate Saudi IBAN (International Bank Account Number)
        """
        if not iban or not isinstance(iban, str):
            return False
        
        # Remove spaces and convert to uppercase
        clean_iban = re.sub(r'\s+', '', iban.upper())
        
        # Saudi IBAN format: SA followed by 2 check digits and 18 digits
        if not re.match(r'^SA\d{20}$', clean_iban):
            return False
        
        # IBAN checksum validation (MOD-97)
        return SaudiValidators._validate_iban_checksum(clean_iban)

    @staticmethod
    def validate_phone_number(phone: str, mobile_only: bool = False) -> Dict[str, Any]:
    """
    Validate Saudi phone number
    
    Args:
        phone: Phone number string
        mobile_only: Only accept mobile numbers
        
    Returns:
        Validation result with details
    """
    
        """
        التحقق من رقم الهاتف السعودي
        Validate Saudi phone number
        """
        result = {
            "valid": False,
            "formatted": "",
            "type": "",
            "carrier": "",
            "errors": []
        }
        
        if not phone:
            result["errors"].append("رقم الهاتف مطلوب")
            return result
        
        # Clean phone number
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Remove country code if present
        if clean_phone.startswith('+966'):
            clean_phone = clean_phone[4:]
        elif clean_phone.startswith('966'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('00966'):
            clean_phone = clean_phone[5:]
        
        # Add leading 0 if missing
        if not clean_phone.startswith('0'):
            clean_phone = '0' + clean_phone
        
        # Validate format
        if not re.match(r'^0\d{9}$', clean_phone):
            result["errors"].append("صيغة رقم الهاتف غير صحيحة")
            return result
        
        # Determine phone type
        first_digits = clean_phone[:3]
        
        if first_digits in ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059']:
            result["type"] = "mobile"
            result["carrier"] = SaudiValidators._get_mobile_carrier(first_digits)
        elif first_digits in ['011', '012', '013', '014', '016', '017']:
            if mobile_only:
                result["errors"].append("مطلوب رقم جوال فقط")
                return result
            result["type"] = "landline"
            result["carrier"] = "STC"
        else:
            result["errors"].append("رقم الهاتف غير مُعرَّف")
            return result
        
        result["valid"] = True
        result["formatted"] = f"+966{clean_phone[1:]}"
        
        return result

    @staticmethod
    def validate_postal_code(postal_code: str, city: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate Saudi postal code
    
    Args:
        postal_code: Postal code string
        city: Optional city name for additional validation
        
    Returns:
        Validation result
    """
    
        """
        التحقق من الرمز البريدي السعودي
        Validate Saudi postal code
        """
        result = {
            "valid": False,
            "formatted": "",
            "region": "",
            "errors": []
        }
        
        if not postal_code:
            result["errors"].append("الرمز البريدي مطلوب")
            return result
        
        # Clean postal code
        clean_code = re.sub(r'\s+', '', postal_code)
        
        # Saudi postal codes are 5 digits
        if not re.match(r'^\d{5}$', clean_code):
            result["errors"].append("الرمز البريدي يجب أن يكون 5 أرقام")
            return result
        
        # First two digits indicate the region
        region_code = clean_code[:2]
        region = SaudiValidators._get_region_from_postal_code(region_code)
        
        if not region:
            result["errors"].append("رمز المنطقة غير صحيح")
            return result
        
        result.update({
            "valid": True,
            "formatted": clean_code,
            "region": region,
            "region_code": region_code
        })
        
        return result

    @staticmethod
    def validate_hijri_date(hijri_date: str) -> Dict[str, Any]:
    """
    Validate Hijri date format and logical constraints
    
    Args:
        hijri_date: Hijri date in YYYY-MM-DD format
        
    Returns:
        Validation result
    """
    
        """
        التحقق من التاريخ الهجري
        Validate Hijri date format and logical constraints
        """
        result = {
            "valid": False,
            "errors": [],
            "normalized": "",
            "components": {}
        }
        
        if not hijri_date:
            result["errors"].append("التاريخ الهجري مطلوب")
            return result
        
        # Check format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', hijri_date):
            result["errors"].append("صيغة التاريخ يجب أن تكون YYYY-MM-DD")
            return result
        
        try:
            year, month, day = map(int, hijri_date.split('-'))
            
            # Validate year (reasonable range)
            if year < 1300 or year > 1500:
                result["errors"].append(f"السنة الهجرية خارج النطاق المقبول: {year}")
            
            # Validate month
            if month < 1 or month > 12:
                result["errors"].append(f"الشهر غير صحيح: {month}")
            
            # Validate day
            if day < 1 or day > 30:  # Hijri months are max 30 days
                result["errors"].append(f"اليوم غير صحيح: {day}")
            
            # Special validation for specific months
            if month == 12 and day > 29:  # Dhu al-Hijjah varies
                result["errors"].append("ذو الحجة قد يكون 29 أو 30 يوماً")
            
            if not result["errors"]:
                result.update({
                    "valid": True,
                    "normalized": hijri_date,
                    "components": {
                        "year": year,
                        "month": month,
                        "day": day
                    }
                })
        
        except ValueError:
            result["errors"].append("تاريخ غير صحيح")
        
        return result

    @staticmethod
    def validate_tax_number(tax_number: str) -> Dict[str, Any]:
    """
    Validate Saudi VAT/Tax number
    
    Args:
        tax_number: Tax number string
        
    Returns:
        Validation result
    """
    
        """
        التحقق من الرقم الضريبي
        Validate Saudi VAT/Tax number
        """
        result = {
            "valid": False,
            "formatted": "",
            "errors": []
        }
        
        if not tax_number:
            result["errors"].append("الرقم الضريبي مطلوب")
            return result
        
        # Clean tax number
        clean_tax = re.sub(r'\s+', '', tax_number)
        
        # Saudi VAT numbers are 15 digits
        if not re.match(r'^\d{15}$', clean_tax):
            result["errors"].append("الرقم الضريبي يجب أن يكون 15 رقماً")
            return result
        
        # Basic checksum validation (simplified)
        if not SaudiValidators._validate_tax_number_checksum(clean_tax):
            result["errors"].append("الرقم الضريبي غير صحيح")
            return result
        
        result.update({
            "valid": True,
            "formatted": clean_tax
        })
        
        return result

    @staticmethod
    def validate_government_entity_code(entity_code: str) -> Dict[str, Any]:
    """
    Validate government entity code
    
    Args:
        entity_code: Government entity code
        
    Returns:
        Validation result
    """
    
        """
        التحقق من رمز الجهة الحكومية
        Validate government entity code
        """
        result = {
            "valid": False,
            "entity_type": "",
            "ministry": "",
            "errors": []
        }
        
        if not entity_code:
            result["errors"].append("رمز الجهة الحكومية مطلوب")
            return result
        
        # Clean entity code
        clean_code = entity_code.strip().upper()
        
        # Government entity codes follow specific patterns
        if re.match(r'^MIN\d{3}$', clean_code):  # Ministry
            result["entity_type"] = "ministry"
            result["ministry"] = SaudiValidators._get_ministry_from_code(clean_code)
        elif re.match(r'^AGY\d{3}$', clean_code):  # Agency
            result["entity_type"] = "agency"
        elif re.match(r'^UNI\d{3}$', clean_code):  # University
            result["entity_type"] = "university"
        else:
            result["errors"].append("رمز الجهة الحكومية غير صحيح")
            return result
        
        result["valid"] = True
        
        return result

    @staticmethod
    def validate_document_fields(document_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate government document fields
    
    Args:
        document_data: Document data dictionary
        required_fields: List of required field names
        
    Returns:
        Validation result with field-by-field analysis
    """
    
        """
        التحقق من حقول الوثائق الحكومية
        Validate government document fields
        """
        result = {
            "valid": True,
            "missing_fields": [],
            "invalid_fields": {},
            "warnings": []
        }
        
        # Check required fields
        for field in required_fields:
            if field not in document_data or not document_data[field]:
                result["missing_fields"].append(field)
                result["valid"] = False
        
        # Field-specific validation
        validators = {
            "national_id": SaudiValidators.validate_national_id,
            "iqama_number": SaudiValidators.validate_iqama_number,
            "commercial_registration": SaudiValidators.validate_commercial_registration,
            "iban": SaudiValidators.validate_iban,
            "tax_number": lambda x: SaudiValidators.validate_tax_number(x)["valid"],
            "phone_number": lambda x: SaudiValidators.validate_phone_number(x)["valid"],
            "postal_code": lambda x: SaudiValidators.validate_postal_code(x)["valid"]
        }
        
        for field, value in document_data.items():
            if field in validators and value:
                try:
                    if not validators[field](str(value)):
                        result["invalid_fields"][field] = f"قيمة غير صحيحة: {value}"
                        result["valid"] = False
                except Exception as e:
                    result["invalid_fields"][field] = f"خطأ في التحقق: {str(e)}"
                    result["valid"] = False
        
        return result

    # Private helper methods
    @staticmethod
    def _validate_saudi_id_checksum(id_number: str) -> bool:
    
        """التحقق من الرقم التحققي للهوية السعودية"""
        if len(id_number) != 10:
            return False
        
        # Simplified checksum validation
        # In real implementation, this would use the official algorithm
        total = 0
        for i, digit in enumerate(id_number[:-1]):
            weight = 2 if i % 2 == 0 else 1
            product = int(digit) * weight
            total += product if product < 10 else product - 9
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(id_number[-1])

    @staticmethod
    def _validate_iban_checksum(iban: str) -> bool:
    
        """التحقق من الآيبان باستخدام MOD-97"""
        # Move first 4 characters to end
        rearranged = iban[4:] + iban[:4]
        
        # Replace letters with numbers (A=10, B=11, etc.)
        numeric = ""
        for char in rearranged:
            if char.isalpha():
                numeric += str(ord(char) - ord('A') + 10)
            else:
                numeric += char
        
        # Calculate MOD-97
        try:
            return int(numeric) % 97 == 1
        except ValueError:
            return False

    @staticmethod
    def _validate_tax_number_checksum(tax_number: str) -> bool:
    
        """التحقق من الرقم الضريبي (مبسط)"""
        # This is a simplified validation
        # Real implementation would use the official VAT number algorithm
        if len(tax_number) != 15:
            return False
        
        # Basic digit sum validation
        digit_sum = sum(int(digit) for digit in tax_number)
        return digit_sum % 10 == 0

    @staticmethod
    def _get_mobile_carrier(prefix: str) -> str:
    
        """الحصول على شركة الجوال من رقم الهاتف"""
        carrier_map = {
            '050': 'STC',
            '051': 'STC', 
            '052': 'STC',
            '053': 'STC',
            '054': 'Mobily',
            '055': 'Mobily',
            '056': 'Zain',
            '057': 'Zain',
            '058': 'Zain',
            '059': 'Lebara/Virgin'
        }
        
        return carrier_map.get(prefix, 'Unknown')

    @staticmethod
    def _get_region_from_postal_code(region_code: str) -> str:
    
        """الحصول على اسم المنطقة من الرمز البريدي"""
        region_map = {
            '11': 'الرياض',      # Riyadh
            '12': 'مكة المكرمة',  # Makkah
            '13': 'المنطقة الشرقية', # Eastern Province
            '14': 'المدينة المنورة', # Madinah
            '15': 'القصيم',      # Qassim
            '16': 'حائل',       # Hail
            '17': 'تبوك',       # Tabuk
            '18': 'الحدود الشمالية', # Northern Border
            '19': 'جازان',      # Jazan
            '20': 'نجران',      # Najran
            '21': 'الباحة',     # Al Bahah
            '22': 'الجوف',      # Al Jouf
            '23': 'عسير'        # Asir
        }
        
        return region_map.get(region_code, '')

    @staticmethod
    def _get_ministry_from_code(ministry_code: str) -> str:
    
        """الحصول على اسم الوزارة من الرمز"""
        ministry_map = {
            'MIN001': 'وزارة الداخلية',
            'MIN002': 'وزارة الخارجية', 
            'MIN003': 'وزارة المالية',
            'MIN004': 'وزارة التجارة',
            'MIN005': 'وزارة التعليم',
            'MIN006': 'وزارة الصحة',
            'MIN007': 'وزارة العدل',
            'MIN008': 'وزارة الدفاع'
        }
        
        return ministry_map.get(ministry_code, 'جهة حكومية غير محددة')

    @staticmethod
    def get_validation_summary() -> Dict[str, List[str]]:
    
        """الحصول على ملخص جميع أدوات التحقق المتاحة"""
        return {
            "identity_validators": [
                "validate_national_id",
                "validate_iqama_number"
            ],
            "business_validators": [
                "validate_commercial_registration", 
                "validate_tax_number",
                "validate_iban"
            ],
            "contact_validators": [
                "validate_phone_number",
                "validate_postal_code"
            ],
            "date_validators": [
                "validate_hijri_date"
            ],
            "government_validators": [
                "validate_government_entity_code",
                "validate_document_fields"
            ]
        }