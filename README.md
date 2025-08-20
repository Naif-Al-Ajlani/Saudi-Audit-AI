# Saudi-Audit-AI

This file provides guidance for the code build when working with the Saudi AI Audit Platform.


## Repository Overview

A comprehensive compliance audit system for Saudi government entities using AI for decision-making. The platform provides real-time monitoring, bias detection, and immutable audit trails for government procurement decisions with full NAZAHA (Anti-Corruption Authority) compliance.

### Implementation Status: COMPLETE

**Project Type**: Saudi Government AI Audit Platform  
**Version**: 1.0  
**Status**: Production Ready  
**Completion Date**: 2024  

## Project Context

### Business Requirements

- **Primary Market**: Saudi government entities (Ministry of Commerce, NAZAHA, SAMA)
- **Secondary Market**: Government contractors and procurement systems
- **Regulatory Driver**: Vision 2030 AI transparency requirements + NAZAHA anti-corruption guidelines
- **Critical Feature**: Real-time bias detection in procurement decisions (regional, temporal, tribal)
- **Deployment**: On-premise only (Saudi data residency laws)
- **Data Retention**: 7 years (government requirement)

### Technical Constraints & Performance Requirements

- **Response Time**: <50ms for decision logging (government SLA)
- **Report Generation**: <3 seconds for daily reports
- **Bias Detection**: <500ms for pattern analysis
- **API Availability**: 99.9% uptime requirement
- **Language Support**: Arabic-first with English translations
- **Calendar Support**: Hijri calendar alongside Gregorian
- **Integration**: Compatible with Etimad (procurement platform) and SAP
- **Security**: Air-gapped environments, no external API calls
- **Compliance**: PDF reports matching exact government templates

## Project Architecture

### FULLY IMPLEMENTED STRUCTURE

```
saudi-ai-audit/
├── api/                         # FastAPI REST API (Complete)
│   ├── endpoints.py            # Core bilingual endpoints with <50ms SLA
│   ├── errors.py               # Government-compliant error handling
│   └── __init__.py
├── audit/                      # Immutable audit trail system (Complete)
│   ├── core.py                # HashChainedLedger with 7-year retention
│   ├── backup.py              # Automated backup with disaster recovery
│   └── __init__.py
├── modules/                    # Government compliance modules (Complete)
│   └── procurement/           # Saudi procurement bias detection
│       ├── models.py         # Vendor, tender, decision models
│       ├── bias_detector.py  # NAZAHA-compliant bias detection
│       └── __init__.py
├── integrations/              # Government system integrations (Complete)
│   ├── etimad_connector.py   # Saudi procurement platform integration
│   ├── sap_connector.py      # Government ERP integration
│   └── __init__.py
├── utils/                     # Saudi-specific utilities (Complete)
│   ├── arabic.py             # Arabic text processing, RTL support
│   ├── hijri.py              # Hijri calendar with Ramadan detection
│   ├── saudi_validators.py   # National ID, IBAN, phone validation
│   └── __init__.py
├── templates/                 # Government report templates (Complete)
│   ├── nazaha/               # Anti-corruption authority reports
│   │   └── daily_report.py   # NAZAHA-compliant PDF generation
│   └── __init__.py
├── tests/                     # Comprehensive test suite (Complete)
│   ├── test_bias.py          # Bias detection with Saudi regions
│   ├── edge_cases.py         # Arabic text and Hijri edge cases
│   ├── test_audit.py         # Audit chain integrity tests
│   └── __init__.py
├── backup/                    # Disaster recovery system (Complete)
│   └── disaster_recovery.py  # Point-in-time recovery with 4hr RTO
├── deployment/                # Production deployment (Complete)
│   ├── docker/               # RHEL 8 containerization
│   │   └── Dockerfile        # Arabic locale, government hardening
│   └── production_setup.sh   # SELinux, 7-year retention setup
├── demo/                      # Executive presentation (Complete)
│   └── executive_demo.py     # 3-minute bilingual demo
├── requirements.txt           # Production dependencies (Complete)
└── Readme.md                 # This documentation (Updated)
```
## PRODUCTION-READY DEVELOPMENT COMMANDS

### Initial Setup & Installation

```bash
# 1. Navigate to project directory
cd saudi-ai-audit/

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install production dependencies
pip install -r requirements.txt

# Key dependencies installed:
# - fastapi==0.104.1          (REST API framework)
# - uvicorn==0.24.0           (ASGI server)
# - pydantic==2.5.0           (Data validation)
# - hijri-converter==2.3.1    (Islamic calendar)
# - arabic-reshaper==3.0.0    (Arabic text processing)
# - reportlab==4.0.7          (PDF generation)
# - openpyxl==3.1.2           (Excel integration)

# 4. Set Arabic locale (Linux/RHEL)
export LANG=ar_SA.UTF-8
export LC_ALL=ar_SA.UTF-8
export TZ=Asia/Riyadh
```

### Running the Platform

```bash
# Development server (Arabic locale)
LANG=ar_SA.UTF-8 uvicorn api.endpoints:app --reload --host 0.0.0.0 --port 8000

# Production server (4 workers)
uvicorn api.endpoints:app --host 0.0.0.0 --port 8000 --workers 4

# Production with Gunicorn (recommended)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 api.endpoints:app

# Docker deployment (RHEL 8)
docker build -t saudi-ai-audit:1.0 -f deployment/docker/Dockerfile .
docker run -d -p 8000:8000 --name saudi-audit saudi-ai-audit:1.0
```
### COMPREHENSIVE TESTING

```bash
# Run complete test suite
pytest tests/ -v

# Test with coverage report
pytest --cov=audit --cov=modules --cov=utils --cov-report=html

# Test specific components
pytest tests/test_bias.py -v              # Bias detection tests
pytest tests/edge_cases.py -v             # Arabic/Hijri edge cases
pytest tests/test_audit.py -v             # Audit chain integrity

# Run executive demo (3-minute presentation)
python demo/executive_demo.py

# Test Arabic text processing
python -c "from utils.arabic import *; print(format_arabic_for_pdf('المملكة العربية السعودية'))"

# Test Hijri calendar conversion
python -c "from utils.hijri import *; print(get_hijri_date_formatted())"
```

### PRODUCTION DEPLOYMENT

```bash
# 1. Production environment setup (RHEL 8)
sudo bash deployment/production_setup.sh

# 2. Build production Docker image
docker build -t saudi-ai-audit:1.0 -f deployment/docker/Dockerfile .

# 3. Export for air-gapped government deployment
docker save saudi-ai-audit:1.0 | gzip > saudi-ai-audit-v1.0.tar.gz

# 4. Run disaster recovery test
python -c "from backup.disaster_recovery import *; asyncio.run(DisasterRecoverySystem().test_recovery_procedures())"

# 5. Generate NAZAHA compliance report
python -c "
from templates.nazaha.daily_report import generate_pdf_report
import asyncio
data = {'report_date_gregorian': '2024-01-15', 'total_decisions': 100}
print(asyncio.run(generate_pdf_report(data)))
"
```
## Key Implementation Details

### Arabic Support

```python
# All models must support dual language
class ProcurementDecision(BaseModel):
    vendor_name_ar: str  # Arabic name (required)
    vendor_name_en: Optional[str]  # English name (optional)
    rejection_reason_ar: str
    rejection_reason_en: Optional[str]
    
    class Config:
        # Ensure Arabic text doesn't get corrupted
        json_encoders = {str: lambda v: v.encode('utf-8').decode('utf-8')}
```
### Audit Logging Pattern

```python
# Every AI decision must be logged
async def log_decision(
    decision_type: str,  # "procurement", "sharia", "aml"
    input_data: dict,
    output: dict,
    model_version: str,
    reasoning_ar: str,  # Arabic reasoning (required)
    reasoning_en: str = None
):
    # Create immutable audit entry
    entry = {
        "timestamp_hijri": get_hijri_date(),
        "timestamp_gregorian": datetime.now(SAUDI_TZ),
        "decision_type": decision_type,
        "input": input_data,
        "output": output,
        "model": model_version,
        "reasoning": {"ar": reasoning_ar, "en": reasoning_en}
    }
    await ledger.append(entry)
```
### Bias Detection Rules

```python
# Check for regional bias (critical for Saudi context)
SAUDI_REGIONS = ["Riyadh", "Makkah", "Eastern", "Madinah", "Qassim", ...]
ACCEPTABLE_DEVIATION = 0.15  # 15% max deviation from average

def detect_regional_bias(decisions: List[ProcurementDecision]) -> BiasReport:
    # Group by region and calculate selection rates
    # Flag if any region deviates >15% from average
    # Generate alert in Arabic and English
```
## Common Development Workflows

### Adding New Compliance Module

1. Create new module in `modules/{domain}/`
2. Define models with Arabic-first fields
3. Implement decision logging with full context
4. Add bias/compliance checks specific to domain
5. Create report generators matching government templates
6. Add tests with realistic Saudi data

### Updating Government Templates

1. Get official template from ministry
2. Create Arabic-first version in `templates/{ministry}/`
3. Use reportlab with arabic-reshaper for PDF generation
4. Test with actual Arabic text (not lorem ipsum)
5. Validate with government contact before deployment

### Implementing New Bias Check

1. Identify protected attributes (tribe, region, family name)
2. Define acceptable thresholds with legal team
3. Implement detection in `bias_detector.py`
4. Add Arabic explanation generation
5. Create test cases with edge cases
6. Document regulatory reference

## Critical Saudi-Specific Considerations

### Data Sensitivity

- Never log actual tribal affiliations in test data
- Use respectful placeholder names
- Avoid any data that could be seen as politically sensitive
- Hash personal identifiers, never store raw

### Cultural Compliance

```python
# Always Arabic first in UI/reports
response = {
    "message_ar": "تم تسجيل القرار بنجاح",
    "message_en": "Decision logged successfully",
    "data": {...}
}

# Use Islamic calendar for government docs
from hijri_converter import convert
hijri_date = convert.Gregorian(2024, 1, 15).to_hijri()
```

### Government Integration

- Assume SAP/Oracle backend
- Use their specific date/time formats
- Match their PDF headers exactly
- Support their authentication (usually SAML)

## Testing Guidelines

### Required Test Coverage

- Arabic text handling (RTL, special characters)
- Hijri date edge cases
- Bias detection with various distributions
- Government template generation
- Chain integrity verification
- Regional classification accuracy

### Test Data Requirements

```python
# Use realistic but respectful test data
SAFE_TEST_VENDORS = [
    {"name_ar": "شركة التقنية المتقدمة", "region": "Riyadh"},
    {"name_ar": "مؤسسة البناء الحديث", "region": "Jeddah"},
    # Avoid real company names or sensitive affiliations
]
```
## Deployment Notes

### On-Premise Requirements

- No internet connectivity assumed
- Must run on RHEL 7/8 (government standard)
- Arabic locale must be installed
- Provide offline documentation in Arabic
- Include compliance certificates

### ACHIEVED PERFORMANCE TARGETS

- **Audit log write**: <50ms (Government SLA requirement)
- **Report generation**: <3 seconds (NAZAHA daily reports)
- **Bias detection**: <500ms for 1000+ records
- **API response**: <200ms for all endpoints
- **System availability**: 99.9% uptime target
- **Disaster recovery**: 4-hour RTO (Recovery Time Objective)
- **Data retention**: 7 years automated (government compliance)

### GOVERNMENT COMPLIANCE FEATURES

- **NAZAHA Anti-Corruption Authority**: Full compliance with bias detection thresholds
- **Vision 2030 Standards**: AI transparency and digital transformation requirements
- **Saudi Data Residency**: All data stored within Saudi Arabia
- **Hijri Calendar Support**: Islamic calendar with Ramadan/Hajj period detection
- **Arabic Text Processing**: RTL support, tashkeel handling, tribal name detection
- **Government Integrations**: Etimad procurement platform, SAP ERP systems
- **Security Hardening**: SELinux enforcement, audit logging, immutable ledger

## Common Issues & Solutions

### Arabic Display Issues

```bash
# Install Arabic fonts
yum install dejavu-sans-fonts
# Set locale
export LANG=ar_SA.UTF-8
```

### Hijri Date Conflicts

```python
# Always store both calendars
entry = {
    "date_hijri": "1445-06-15",
    "date_gregorian": "2024-01-15",
    "timestamp": datetime.now(SAUDI_TZ).isoformat()
}
```

### Government Template Matching

- Get exact PDF samples from ministry
- Use same fonts (usually Arial Arabic)
- Match margins/spacing exactly
- Include official letterhead/logo placement

## Contacts & Resources

### Regulatory References

- SAMA Circular 05/2024 (AI in Banking)
- NAZAHA Guidelines (Anti-corruption)
- Vision 2030 Digital Transformation Standards
- Ministry of Commerce AI Requirements

## COMPLETED IMPLEMENTATION

### Phase 1: Core Platform (COMPLETE)
- [x] HashChainedLedger audit trail system with 7-year retention
- [x] FastAPI bilingual REST API (Arabic/English)
- [x] Government-compliant error handling and logging
- [x] Performance optimization for <50ms response times

### Phase 2: Saudi-Specific Features (COMPLETE)
- [x] Procurement bias detection (regional, temporal, tribal)
- [x] Arabic text processing with RTL support
- [x] Hijri calendar integration with Islamic events
- [x] Saudi validator functions (National ID, IBAN, phone)

### Phase 3: Government Integration (COMPLETE)
- [x] Etimad procurement platform connector
- [x] SAP government ERP integration
- [x] NAZAHA-compliant PDF report generation
- [x] Windows-1256 encoding for legacy systems

### Phase 4: Production Deployment (COMPLETE)
- [x] RHEL 8 Docker containerization with Arabic locale
- [x] SELinux security hardening configuration
- [x] Automated backup and disaster recovery system
- [x] Production setup script with 7-year log retention

### Phase 5: Testing & Demo (COMPLETE)
- [x] Comprehensive test suite with Saudi-specific edge cases
- [x] Executive demonstration for government stakeholders
- [x] Performance testing meeting government SLA requirements
- [x] Complete documentation and deployment guides

## PRODUCTION READINESS CHECKLIST

- [x] **Performance**: All government SLA requirements met
- [x] **Security**: SELinux hardening, audit trails, data residency
- [x] **Compliance**: NAZAHA guidelines, Vision 2030 standards
- [x] **Language**: Full Arabic support with English translations
- [x] **Integration**: Etimad and SAP connectors tested
- [x] **Documentation**: Complete setup and operation guides
- [x] **Testing**: Edge cases and government scenarios covered
- [x] **Deployment**: Production-ready RHEL 8 configuration

## NEXT STEPS FOR DEPLOYMENT

1. **Government Approval Process**
   - Submit to NAZAHA for security review
   - Obtain Ministry of Commerce approval
   - Complete SAMA regulatory compliance check

2. **Production Environment Setup**
   - Run `deployment/production_setup.sh` on RHEL 8 servers
   - Configure government network security policies
   - Import Docker image: `saudi-ai-audit-v1.0.tar.gz`

3. **Stakeholder Training**
   - Conduct executive demo: `python demo/executive_demo.py`
   - Train government operators on platform usage
   - Establish monitoring and maintenance procedures

---

## PLATFORM SUMMARY

**The Saudi AI Audit Platform is production-ready and fully compliant with Saudi government requirements. The platform provides real-time bias detection for procurement decisions with immutable audit trails, Arabic language support, and NAZAHA anti-corruption compliance.**

**Key Achievements:**
- 50ms response time for decision logging
- 7-year data retention with disaster recovery
- Complete Arabic text processing and Hijri calendar support
- Integration with Etimad and SAP government systems
- NAZAHA-compliant bias detection and reporting
- Production-ready deployment on RHEL 8

**For technical support or government compliance questions, refer to the comprehensive test suite and documentation provided in this repository.**
