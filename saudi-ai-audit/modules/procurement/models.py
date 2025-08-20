"""
Procurement decision models for Saudi AI Audit Platform
Government procurement compliance with NAZAHA requirements
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from utils.saudi_validators import (
    validate_national_id, 
    validate_commercial_registration,
    validate_iban
)
from utils.hijri import get_hijri_date, hijri_to_gregorian

class RegionEnum(str, Enum):
    """Saudi administrative regions"""
    RIYADH = "الرياض"
    MAKKAH = "مكة المكرمة"
    MADINAH = "المدينة المنورة"
    QASSIM = "القصيم"
    EASTERN = "المنطقة الشرقية"
    ASIR = "عسير"
    TABUK = "تبوك"
    HAIL = "حائل"
    NORTHERN_BORDER = "الحدود الشمالية"
    JAZAN = "جازان"
    NAJRAN = "نجران"
    BAHA = "الباحة"
    JOUF = "الجوف"

class ProcurementTypeEnum(str, Enum):
    """Types of government procurement"""
    GOODS = "سلع"
    SERVICES = "خدمات"
    CONSTRUCTION = "إنشاءات"
    CONSULTING = "استشارات"
    MAINTENANCE = "صيانة"
    IT_SERVICES = "خدمات تقنية معلومات"
    MEDICAL_SUPPLIES = "مستلزمات طبية"
    SECURITY_SERVICES = "خدمات أمنية"

class DecisionStatusEnum(str, Enum):
    """Procurement decision status"""
    AWARDED = "منح"
    REJECTED = "مرفوض"
    CANCELLED = "ملغي"
    PENDING = "معلق"
    UNDER_REVIEW = "قيد المراجعة"

class VendorDetails(BaseModel):
    """Vendor information with Saudi compliance fields"""
    
    # Required bilingual fields
    name_ar: str = Field(..., min_length=2, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    
    # Registration information
    commercial_registration: str = Field(..., regex=r"^[0-9]{10}$")
    national_id_owner: Optional[str] = Field(None, regex=r"^[0-9]{10}$")
    tax_number: str = Field(..., regex=r"^[0-9]{15}$")
    
    # Location information (critical for bias detection)
    region: RegionEnum
    city_ar: str = Field(..., min_length=2, max_length=100)
    city_en: Optional[str] = Field(None, max_length=100)
    district_ar: Optional[str] = Field(None, max_length=100)
    
    # Banking information
    iban: str = Field(..., regex=r"^SA[0-9]{2}[0-9]{18}$")
    bank_name_ar: str
    bank_name_en: Optional[str] = None
    
    # Business information
    establishment_date_hijri: str = Field(..., regex=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    establishment_date_gregorian: date
    business_type_ar: str
    business_type_en: Optional[str] = None
    
    # Classification for bias detection
    vendor_size: Literal["صغير", "متوسط", "كبير"] = Field(...)  # Small, Medium, Large
    ownership_type: Literal["فردي", "شراكة", "شركة مساهمة", "حكومي"] = Field(...)
    
    # Performance history
    previous_contracts_count: int = Field(0, ge=0)
    blacklisted: bool = Field(False)
    compliance_score: float = Field(1.0, ge=0.0, le=1.0)
    
    @validator('commercial_registration')
    def validate_cr(cls, v):
        if not validate_commercial_registration(v):
            raise ValueError('Invalid commercial registration number')
        return v
    
    @validator('national_id_owner')
    def validate_owner_id(cls, v):
        if v and not validate_national_id(v):
            raise ValueError('Invalid national ID')
        return v
    
    @validator('iban')
    def validate_saudi_iban(cls, v):
        if not validate_iban(v):
            raise ValueError('Invalid Saudi IBAN')
        return v

class BidDetails(BaseModel):
    """Bid information with government requirements"""
    
    # Bid identification
    bid_reference: str = Field(..., min_length=5, max_length=50)
    submission_date_hijri: str
    submission_date_gregorian: datetime
    
    # Financial information
    bid_amount_sar: Decimal = Field(..., gt=0, decimal_places=2)
    vat_amount_sar: Decimal = Field(..., ge=0, decimal_places=2)
    total_amount_sar: Decimal = Field(..., gt=0, decimal_places=2)
    
    # Technical scoring
    technical_score: float = Field(..., ge=0.0, le=100.0)
    financial_score: float = Field(..., ge=0.0, le=100.0)
    total_score: float = Field(..., ge=0.0, le=100.0)
    
    # Compliance checks
    document_completeness: float = Field(..., ge=0.0, le=1.0)
    qualification_met: bool
    local_content_percentage: float = Field(0.0, ge=0.0, le=100.0)
    
    # Bid evaluation criteria
    meets_specifications: bool
    delivery_timeline_acceptable: bool
    payment_terms_acceptable: bool
    warranty_terms_acceptable: bool
    
    @validator('total_amount_sar')
    def validate_total(cls, v, values):
        bid_amount = values.get('bid_amount_sar', 0)
        vat_amount = values.get('vat_amount_sar', 0)
        expected_total = bid_amount + vat_amount
        if abs(v - expected_total) > 0.01:  # Allow for small rounding differences
            raise ValueError('Total amount must equal bid amount plus VAT')
        return v

class ProcurementTender(BaseModel):
    """Government tender information"""
    
    # Tender identification
    tender_number: str = Field(..., regex=r"^[A-Z0-9]{8,20}$")
    tender_title_ar: str = Field(..., min_length=10, max_length=500)
    tender_title_en: Optional[str] = Field(None, max_length=500)
    
    # Procurement details
    procurement_type: ProcurementTypeEnum
    estimated_value_sar: Decimal = Field(..., gt=0)
    
    # Timeline
    announcement_date_hijri: str
    announcement_date_gregorian: date
    submission_deadline_hijri: str
    submission_deadline_gregorian: datetime
    evaluation_period_days: int = Field(..., gt=0, le=180)
    
    # Procuring entity
    procuring_entity_ar: str = Field(..., min_length=5, max_length=200)
    procuring_entity_en: Optional[str] = Field(None, max_length=200)
    ministry_department: str
    budget_code: str = Field(..., regex=r"^[0-9]{4}-[0-9]{4}-[0-9]{4}$")
    
    # Requirements
    minimum_qualification_requirements: List[str]
    evaluation_criteria: Dict[str, float]  # Criteria name -> weight
    local_content_requirement: float = Field(0.0, ge=0.0, le=100.0)
    
    # Classification for bias analysis
    tender_category: str
    strategic_importance: Literal["عالي", "متوسط", "منخفض"]  # High, Medium, Low
    requires_security_clearance: bool = Field(False)

class ProcurementDecision(BaseModel):
    """Complete procurement decision with audit trail"""
    
    # Decision identification
    decision_id: str = Field(..., min_length=10, max_length=50)
    decision_date_hijri: str
    decision_date_gregorian: datetime
    
    # Tender and vendor information
    tender: ProcurementTender
    winning_vendor: Optional[VendorDetails] = None
    participating_vendors: List[VendorDetails] = Field(default_factory=list)
    vendor_bids: Dict[str, BidDetails] = Field(default_factory=dict)  # vendor CR -> bid
    
    # Decision details
    decision_status: DecisionStatusEnum
    award_amount_sar: Optional[Decimal] = Field(None, gt=0)
    contract_duration_months: Optional[int] = Field(None, gt=0, le=120)
    
    # Reasoning (required for transparency)
    decision_reasoning_ar: str = Field(..., min_length=50)
    decision_reasoning_en: Optional[str] = Field(None, min_length=50)
    evaluation_summary_ar: str = Field(..., min_length=20)
    evaluation_summary_en: Optional[str] = None
    
    # Decision maker information
    decision_maker_id: str = Field(..., regex=r"^[0-9]{10}$")  # National ID
    decision_maker_title_ar: str
    decision_maker_title_en: Optional[str] = None
    approval_authority_level: Literal["وزير", "وكيل", "مدير عام", "مدير", "رئيس قسم"]
    
    # Compliance and oversight
    nazaha_notification_sent: bool = Field(False)
    internal_audit_reviewed: bool = Field(False)
    objections_received: int = Field(0, ge=0)
    objections_resolved: int = Field(0, ge=0)
    
    # Performance and bias metrics (populated by AI system)
    processing_time_days: int = Field(..., gt=0)
    complexity_score: float = Field(1.0, ge=1.0, le=10.0)
    risk_assessment_score: float = Field(1.0, ge=1.0, le=10.0)
    
    # Bias detection metadata
    regional_bias_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    temporal_bias_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    vendor_size_bias_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Audit trail
    created_by_system: str = Field(default="saudi-ai-audit-v1.0")
    last_modified: datetime = Field(default_factory=datetime.now)
    version: int = Field(default=1)
    
    # Government metadata
    classification_level: Literal["سري", "محدود", "داخلي", "عام"] = Field(default="داخلي")
    retention_years: int = Field(default=7)
    
    @validator('decision_maker_id')
    def validate_decision_maker(cls, v):
        if not validate_national_id(v):
            raise ValueError('Invalid decision maker national ID')
        return v
    
    @validator('objections_resolved')
    def validate_objections(cls, v, values):
        received = values.get('objections_received', 0)
        if v > received:
            raise ValueError('Resolved objections cannot exceed received objections')
        return v
    
    @validator('participating_vendors')
    def validate_vendor_participation(cls, v):
        if len(v) < 1:
            raise ValueError('At least one vendor must participate')
        return v
    
    @validator('vendor_bids')
    def validate_bids_match_vendors(cls, v, values):
        vendors = values.get('participating_vendors', [])
        vendor_crs = {vendor.commercial_registration for vendor in vendors}
        bid_crs = set(v.keys())
        
        if bid_crs != vendor_crs:
            missing_bids = vendor_crs - bid_crs
            extra_bids = bid_crs - vendor_crs
            error_msg = []
            if missing_bids:
                error_msg.append(f"Missing bids for vendors: {missing_bids}")
            if extra_bids:
                error_msg.append(f"Bids without corresponding vendors: {extra_bids}")
            raise ValueError("; ".join(error_msg))
        return v
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "decision_id": "PROC_2024_001234",
                "decision_date_hijri": "1445-06-15",
                "decision_date_gregorian": "2024-01-15T10:30:00",
                "tender": {
                    "tender_number": "TND20240001",
                    "tender_title_ar": "توريد أجهزة حاسوب محمولة",
                    "procurement_type": "سلع",
                    "estimated_value_sar": "500000.00"
                },
                "decision_status": "منح",
                "decision_reasoning_ar": "تم اختيار العطاء الأفضل من ناحية الجودة والسعر",
                "decision_maker_id": "1234567890"
            }
        }

class BiasDetectionReport(BaseModel):
    """Bias detection analysis report"""
    
    # Report metadata
    report_id: str
    analysis_date: datetime
    analysis_period_start: date
    analysis_period_end: date
    
    # Bias analysis results
    regional_bias_detected: bool
    temporal_bias_detected: bool
    vendor_size_bias_detected: bool
    overall_bias_score: float = Field(..., ge=0.0, le=1.0)
    
    # Regional analysis
    regional_distribution: Dict[str, float]  # Region -> percentage
    expected_regional_distribution: Dict[str, float]
    regional_deviation_threshold: float = Field(0.15)  # 15% NAZAHA standard
    
    # Temporal analysis
    temporal_patterns: Dict[str, Any]
    seasonal_bias_indicators: List[str]
    
    # Vendor size analysis
    vendor_size_distribution: Dict[str, float]  # Size -> percentage
    sme_participation_rate: float  # Small/Medium Enterprise rate
    
    # Recommendations
    recommendations_ar: List[str]
    recommendations_en: List[str]
    immediate_actions_required: List[str]
    
    # Compliance status
    nazaha_compliant: bool
    ministry_notification_required: bool
    investigation_triggered: bool
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "BIAS_RPT_20240115",
                "regional_bias_detected": False,
                "overall_bias_score": 0.05,
                "nazaha_compliant": True,
                "recommendations_ar": ["الاستمرار في المراقبة الدورية"]
            }
        }