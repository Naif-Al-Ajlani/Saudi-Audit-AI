"""
Bilingual error handling for Saudi AI Audit Platform
Government-compliant error messages with helpdesk information
"""

from typing import Dict, Any, Optional
from datetime import datetime
from utils.hijri import get_hijri_date

# Government helpdesk contact information
HELPDESK_INFO = {
    "ar": {
        "phone": "920003344",
        "email": "support@moc.gov.sa",
        "hours": "الأحد - الخميس: 8:00 ص - 4:00 م",
        "emergency": "966114567890"
    },
    "en": {
        "phone": "920003344", 
        "email": "support@moc.gov.sa",
        "hours": "Sunday - Thursday: 8:00 AM - 4:00 PM",
        "emergency": "966114567890"
    }
}

# Standard error messages
ERROR_MESSAGES = {
    "validation_error": {
        "ar": "خطأ في التحقق من صحة البيانات",
        "en": "Data validation error"
    },
    "authentication_failed": {
        "ar": "فشل في التحقق من الهوية",
        "en": "Authentication failed"
    },
    "authorization_denied": {
        "ar": "تم رفض التفويض",
        "en": "Authorization denied"
    },
    "resource_not_found": {
        "ar": "المورد غير موجود",
        "en": "Resource not found"
    },
    "internal_error": {
        "ar": "خطأ داخلي في النظام",
        "en": "Internal system error"
    },
    "performance_timeout": {
        "ar": "تجاوز الحد الزمني المسموح",
        "en": "Performance timeout exceeded"
    },
    "chain_integrity_failure": {
        "ar": "فشل في سلامة سلسلة التدقيق",
        "en": "Audit chain integrity failure"
    },
    "bias_detection_alert": {
        "ar": "تنبيه: تم اكتشاف تحيز محتمل",
        "en": "Alert: Potential bias detected"
    },
    "regional_bias_warning": {
        "ar": "تحذير: تحيز إقليمي محتمل في القرارات",
        "en": "Warning: Potential regional bias in decisions"
    },
    "government_compliance_violation": {
        "ar": "انتهاك لمتطلبات الامتثال الحكومي",
        "en": "Government compliance violation"
    }
}

def create_error_response(
    message_ar: str,
    message_en: str,
    error_details: Optional[str] = None,
    error_code: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
    include_helpdesk: bool = True
) -> Dict[str, Any]:
    """
    Create standardized bilingual error response
    
    Args:
        message_ar: Arabic error message
        message_en: English error message  
        error_details: Technical error details
        error_code: Internal error code
        additional_data: Extra context data
        include_helpdesk: Include government helpdesk info
    
    Returns:
        Standardized error response dictionary
    """
    
    error_response = {
        "error": True,
        "timestamp_hijri": get_hijri_date(),
        "timestamp_gregorian": datetime.now().isoformat(),
        "message": {
            "ar": message_ar,
            "en": message_en
        }
    }
    
    if error_code:
        error_response["error_code"] = error_code
    
    if error_details:
        error_response["details"] = error_details
    
    if additional_data:
        error_response["context"] = additional_data
    
    if include_helpdesk:
        error_response["helpdesk"] = {
            "ar": {
                "message": "للحصول على الدعم التقني، يرجى التواصل مع:",
                "contact": HELPDESK_INFO["ar"],
                "reference_id": f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            },
            "en": {
                "message": "For technical support, please contact:",
                "contact": HELPDESK_INFO["en"],
                "reference_id": f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
    
    # Add compliance reference for government audits
    error_response["compliance"] = {
        "regulation": "Vision 2030 - Digital Transformation",
        "authority": "NAZAHA / Ministry of Commerce",
        "retention_period": "7 years",
        "classification": "Government Internal Use"
    }
    
    return error_response

def create_validation_error(field_name: str, field_value: Any, validation_rule: str) -> Dict[str, Any]:
    """Create validation-specific error response"""
    
    field_errors = {
        "national_id": {
            "ar": f"رقم الهوية الوطنية غير صحيح: {field_value}",
            "en": f"Invalid National ID: {field_value}"
        },
        "iqama_number": {
            "ar": f"رقم الإقامة غير صحيح: {field_value}",
            "en": f"Invalid Iqama number: {field_value}"
        },
        "commercial_registration": {
            "ar": f"رقم السجل التجاري غير صحيح: {field_value}",
            "en": f"Invalid Commercial Registration: {field_value}"
        },
        "iban": {
            "ar": f"رقم الآيبان غير صحيح: {field_value}",
            "en": f"Invalid IBAN: {field_value}"
        },
        "hijri_date": {
            "ar": f"التاريخ الهجري غير صحيح: {field_value}",
            "en": f"Invalid Hijri date: {field_value}"
        }
    }
    
    if field_name in field_errors:
        message_ar = field_errors[field_name]["ar"]
        message_en = field_errors[field_name]["en"]
    else:
        message_ar = f"خطأ في التحقق من صحة الحقل: {field_name}"
        message_en = f"Field validation error: {field_name}"
    
    return create_error_response(
        message_ar=message_ar,
        message_en=message_en,
        error_code="VALIDATION_ERROR",
        additional_data={
            "field": field_name,
            "value": str(field_value),
            "validation_rule": validation_rule
        }
    )

def create_performance_error(operation: str, duration_ms: float, limit_ms: float) -> Dict[str, Any]:
    """Create performance-related error response"""
    
    return create_error_response(
        message_ar=f"تجاوز العملية '{operation}' الحد الزمني المسموح",
        message_en=f"Operation '{operation}' exceeded time limit",
        error_code="PERFORMANCE_TIMEOUT",
        additional_data={
            "operation": operation,
            "duration_ms": duration_ms,
            "limit_ms": limit_ms,
            "performance_standard": "Government SLA: <50ms for logging, <3s for reports"
        }
    )

def create_bias_alert(bias_type: str, confidence: float, affected_regions: list) -> Dict[str, Any]:
    """Create bias detection alert"""
    
    bias_messages = {
        "regional": {
            "ar": "تم اكتشاف تحيز إقليمي في القرارات",
            "en": "Regional bias detected in decisions"
        },
        "tribal": {
            "ar": "تم اكتشاف تحيز قبلي محتمل",
            "en": "Potential tribal bias detected"
        },
        "temporal": {
            "ar": "تم اكتشاف تحيز زمني في القرارات",
            "en": "Temporal bias detected in decisions"
        }
    }
    
    message = bias_messages.get(bias_type, bias_messages["regional"])
    
    return create_error_response(
        message_ar=message["ar"],
        message_en=message["en"],
        error_code="BIAS_DETECTED",
        additional_data={
            "bias_type": bias_type,
            "confidence_score": confidence,
            "affected_regions": affected_regions,
            "regulatory_requirement": "NAZAHA Anti-Corruption Guidelines",
            "action_required": "Manual review and documentation required"
        }
    )

def create_compliance_violation(violation_type: str, regulation: str, details: str) -> Dict[str, Any]:
    """Create compliance violation error"""
    
    return create_error_response(
        message_ar=f"انتهاك لمتطلبات الامتثال: {violation_type}",
        message_en=f"Compliance violation: {violation_type}",
        error_code="COMPLIANCE_VIOLATION",
        additional_data={
            "violation_type": violation_type,
            "regulation": regulation,
            "details": details,
            "escalation_required": True,
            "notification_sent_to": ["compliance@moc.gov.sa", "audit@nazaha.gov.sa"]
        }
    )

# Government-specific error handlers
class SaudiGovernmentErrorHandler:
    """Error handler with Saudi government compliance features"""
    
    @staticmethod
    def handle_etimad_connection_error(error_details: str) -> Dict[str, Any]:
        """Handle Etimad integration errors"""
        return create_error_response(
            message_ar="فشل في الاتصال بنظام اعتماد",
            message_en="Failed to connect to Etimad system",
            error_code="ETIMAD_CONNECTION_ERROR",
            additional_data={
                "system": "Etimad Government Procurement",
                "encoding_issue": "Check Windows-1256 encoding",
                "xml_format": "Verify XML export format",
                "error_details": error_details,
                "support_contact": "etimad-support@moc.gov.sa"
            }
        )
    
    @staticmethod
    def handle_sap_integration_error(error_details: str) -> Dict[str, Any]:
        """Handle SAP integration errors"""
        return create_error_response(
            message_ar="فشل في التكامل مع نظام SAP",
            message_en="SAP integration failure",
            error_code="SAP_INTEGRATION_ERROR",
            additional_data={
                "system": "SAP Government Backend",
                "date_format": "Expected DD.MM.YYYY format",
                "encoding": "Windows-1252",
                "error_details": error_details,
                "support_contact": "sap-support@mof.gov.sa"
            }
        )
    
    @staticmethod
    def handle_chain_corruption(corruption_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle audit chain corruption"""
        return create_error_response(
            message_ar="تم اكتشاف تلف في سلسلة التدقيق",
            message_en="Audit chain corruption detected",
            error_code="CHAIN_CORRUPTION",
            additional_data={
                "severity": "CRITICAL",
                "immediate_action": "System quarantine initiated",
                "backup_restore": "Automatic recovery in progress",
                "corruption_details": corruption_details,
                "escalation": "Security team notified",
                "investigation_id": f"INV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            },
            include_helpdesk=True
        )