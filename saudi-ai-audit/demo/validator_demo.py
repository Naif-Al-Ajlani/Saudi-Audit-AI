"""
Saudi AI Audit Platform - Validator Demo
Demonstrates Saudi-specific validation capabilities
"""

def demo_saudi_validators():
    print("=" * 60)
    print("SAUDI VALIDATORS DEMONSTRATION")
    print("=" * 60)
    
    # Simple National ID validation demo
    print("\n[SAUDI NATIONAL ID VALIDATION]")
    test_cases = [
        ("1234567890", "Valid format - starts with 1"),
        ("2345678901", "Valid format - starts with 2"), 
        ("3456789012", "Invalid - starts with 3 (Iqama range)"),
        ("0123456789", "Invalid - starts with 0"),
        ("123456789", "Invalid - too short"),
    ]
    
    for test_id, description in test_cases:
        # Simple validation logic
        if len(test_id) == 10 and test_id[0] in ['1', '2'] and test_id.isdigit():
            status = "VALID"
        else:
            status = "INVALID"
        print(f"  ID {test_id}: {status:7} - {description}")
    
    # Saudi IBAN validation demo
    print("\n[SAUDI IBAN VALIDATION]")
    iban_cases = [
        ("SA0380000000608010167519", "Valid Saudi IBAN"),
        ("SA1234567890123456789012", "Valid format"),
        ("AE380000000608010167519", "Invalid - UAE IBAN"),
        ("SA123", "Invalid - too short"),
    ]
    
    for iban, description in iban_cases:
        if iban.startswith("SA") and len(iban) == 22 and iban[2:].isdigit():
            status = "VALID"
        else:
            status = "INVALID"
        print(f"  IBAN {iban}: {status:7} - {description}")
    
    # Phone number validation demo
    print("\n[SAUDI PHONE NUMBER VALIDATION]")
    phone_cases = [
        ("0501234567", "Valid mobile - STC"),
        ("+966501234567", "Valid with country code"),
        ("0112345678", "Valid landline"),
        ("123456", "Invalid - too short"),
    ]
    
    for phone, description in phone_cases:
        clean_phone = phone.replace("+966", "0").replace("966", "0")
        if not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone
            
        if len(clean_phone) == 10 and clean_phone[0] == "0":
            if clean_phone[:3] in ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059']:
                status = "VALID (Mobile)"
            elif clean_phone[:3] in ['011', '012', '013', '014', '016', '017']:
                status = "VALID (Landline)"
            else:
                status = "INVALID"
        else:
            status = "INVALID"
        print(f"  Phone {phone}: {status:15} - {description}")
    
    # Hijri date validation demo
    print("\n[HIJRI DATE VALIDATION]")
    hijri_cases = [
        ("1445-09-15", "Valid Ramadan date"),
        ("1445-13-01", "Invalid month (13)"),
        ("1445-09-31", "Invalid day (31)"),
        ("1300-01-01", "Valid but very old"),
    ]
    
    for date_str, description in hijri_cases:
        try:
            parts = date_str.split("-")
            if len(parts) == 3:
                year, month, day = map(int, parts)
                if 1300 <= year <= 1500 and 1 <= month <= 12 and 1 <= day <= 30:
                    status = "VALID"
                else:
                    status = "INVALID"
            else:
                status = "INVALID"
        except:
            status = "INVALID"
        print(f"  Hijri {date_str}: {status:7} - {description}")
    
    # Commercial Registration demo
    print("\n[COMMERCIAL REGISTRATION VALIDATION]")
    cr_cases = [
        ("1010123456", "Valid CR number"),
        ("2020987654", "Valid CR number"),
        ("0123456789", "Invalid - starts with 0"),
        ("123456789", "Invalid - too short"),
    ]
    
    for cr, description in cr_cases:
        if len(cr) == 10 and cr.isdigit() and cr[0] != "0":
            status = "VALID"
        else:
            status = "INVALID"
        print(f"  CR {cr}: {status:7} - {description}")
    
    print("\n" + "=" * 60)
    print("VALIDATOR DEMO COMPLETED SUCCESSFULLY")
    print("All Saudi-specific validation rules demonstrated")
    print("=" * 60)

if __name__ == "__main__":
    demo_saudi_validators()