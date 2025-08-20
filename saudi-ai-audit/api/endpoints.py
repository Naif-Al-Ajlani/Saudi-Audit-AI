"""
FastAPI endpoints for Saudi AI Audit Platform
Handles decision logging, reporting, and audit verification
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import json

from audit.core import HashChainedLedger
from modules.procurement.models import ProcurementDecision
from modules.procurement.bias_detector import BiasDetector
from utils.arabic import format_bilingual_response
from utils.hijri import get_hijri_date
from utils.saudi_validators import validate_national_id
from api.errors import create_error_response

app = FastAPI(
    title="Saudi AI Audit Platform",
    description="نظام تدقيق الذكاء الاصطناعي للحكومة السعودية",
    version="1.0.0",
    docs_url="/docs" if app.debug else None,  # Disable in production
    redoc_url=None  # Disable redoc for security
)

# Global instances
ledger = HashChainedLedger()
bias_detector = BiasDetector()

class DecisionLogRequest(BaseModel):
    decision_type: str = Field(..., regex="^(procurement|sharia|aml)$")
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    model_version: str
    reasoning_ar: str = Field(..., min_length=10)
    reasoning_en: Optional[str] = None
    user_id: str = Field(..., regex="^[0-9]{10}$")  # National ID format
    timestamp_override: Optional[datetime] = None

class AuditVerificationRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    decision_type: Optional[str] = None

@app.get("/health")
async def health_check():
    """نقطة فحص صحة النظام / System health check"""
    try:
        # Quick performance test
        start_time = datetime.now()
        await ledger.verify_chain_integrity()
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return format_bilingual_response(
            message_ar="النظام يعمل بشكل طبيعي",
            message_en="System operational",
            data={
                "status": "healthy",
                "response_time_ms": response_time,
                "chain_integrity": "verified",
                "timestamp_hijri": get_hijri_date(),
                "timestamp_gregorian": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=create_error_response(
                "فشل في فحص صحة النظام",
                "System health check failed",
                str(e)
            )
        )

@app.post("/decision/log")
async def log_decision(request: DecisionLogRequest, background_tasks: BackgroundTasks):
    """تسجيل قرار الذكاء الاصطناعي / Log AI decision"""
    start_time = datetime.now()
    
    try:
        # Validate user
        if not validate_national_id(request.user_id):
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "رقم الهوية الوطنية غير صحيح",
                    "Invalid National ID",
                    f"ID: {request.user_id}"
                )
            )
        
        # Create audit entry
        audit_entry = {
            "id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.user_id}",
            "timestamp_hijri": get_hijri_date(),
            "timestamp_gregorian": request.timestamp_override or datetime.now(),
            "decision_type": request.decision_type,
            "input_data": request.input_data,
            "output_data": request.output_data,
            "model_version": request.model_version,
            "reasoning": {
                "ar": request.reasoning_ar,
                "en": request.reasoning_en or ""
            },
            "user_id": request.user_id,
            "performance_metrics": {
                "processing_time_ms": 0  # Will be updated
            }
        }
        
        # Log decision (must be <50ms)
        entry_id = await ledger.append_entry(audit_entry)
        
        # Background bias detection
        if request.decision_type == "procurement":
            background_tasks.add_task(
                run_bias_detection,
                request.input_data,
                request.output_data,
                entry_id
            )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return format_bilingual_response(
            message_ar="تم تسجيل القرار بنجاح",
            message_en="Decision logged successfully",
            data={
                "entry_id": entry_id,
                "processing_time_ms": processing_time,
                "next_backup": ledger.get_next_backup_time(),
                "chain_hash": ledger.get_latest_hash()
            }
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "فشل في تسجيل القرار",
                "Failed to log decision",
                str(e),
                {"processing_time_ms": processing_time}
            )
        )

@app.get("/report/daily")
async def generate_daily_report(
    date: Optional[str] = None,
    format: str = "json",
    department: Optional[str] = None
):
    """تقرير يومي / Generate daily report"""
    start_time = datetime.now()
    
    try:
        target_date = datetime.fromisoformat(date) if date else datetime.now().date()
        
        # Get daily statistics
        stats = await ledger.get_daily_statistics(target_date)
        bias_report = await bias_detector.generate_daily_bias_report(target_date)
        
        report_data = {
            "report_date_hijri": get_hijri_date(target_date),
            "report_date_gregorian": target_date.isoformat(),
            "total_decisions": stats["total_decisions"],
            "decisions_by_type": stats["by_type"],
            "performance_metrics": stats["performance"],
            "bias_analysis": bias_report,
            "compliance_status": "متوافق" if bias_report["compliant"] else "غير متوافق",
            "generated_at": datetime.now().isoformat(),
            "generation_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }
        
        if format == "pdf":
            # Generate PDF report (government template)
            from templates.nazaha.daily_report import generate_pdf_report
            pdf_path = await generate_pdf_report(report_data)
            return {"pdf_path": pdf_path, "data": report_data}
        
        return format_bilingual_response(
            message_ar="تم إنشاء التقرير اليومي",
            message_en="Daily report generated",
            data=report_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "فشل في إنشاء التقرير اليومي",
                "Failed to generate daily report",
                str(e)
            )
        )

@app.post("/audit/verify")
async def verify_audit_trail(request: AuditVerificationRequest):
    """التحقق من سلسلة التدقيق / Verify audit trail"""
    start_time = datetime.now()
    
    try:
        # Verify chain integrity for date range
        verification_result = await ledger.verify_range(
            request.start_date,
            request.end_date,
            request.decision_type
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return format_bilingual_response(
            message_ar="تم التحقق من سلسلة التدقيق",
            message_en="Audit trail verified",
            data={
                "verification_status": "verified" if verification_result["valid"] else "corrupted",
                "entries_checked": verification_result["entries_count"],
                "integrity_score": verification_result["integrity_score"],
                "anomalies": verification_result.get("anomalies", []),
                "verification_time_ms": processing_time,
                "period": {
                    "start_hijri": get_hijri_date(request.start_date),
                    "end_hijri": get_hijri_date(request.end_date),
                    "start_gregorian": request.start_date.isoformat(),
                    "end_gregorian": request.end_date.isoformat()
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "فشل في التحقق من سلسلة التدقيق",
                "Failed to verify audit trail",
                str(e)
            )
        )

async def run_bias_detection(input_data: Dict, output_data: Dict, entry_id: str):
    """Background task for bias detection"""
    try:
        bias_result = await bias_detector.analyze_decision(input_data, output_data)
        if bias_result["bias_detected"]:
            # Log bias alert
            await ledger.log_bias_alert(entry_id, bias_result)
    except Exception as e:
        # Log error but don't fail the main request
        print(f"Bias detection failed for entry {entry_id}: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return exc.detail

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return create_error_response(
        "خطأ داخلي في النظام",
        "Internal system error",
        str(exc)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")