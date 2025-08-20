"""
NAZAHA Anti-Corruption Authority daily report generator
Government-compliant PDF templates with Arabic support
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, red, green, orange
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utils.arabic import format_arabic_for_pdf, clean_arabic_text
from utils.hijri import get_hijri_date_formatted, format_government_date

class NAZAHAReportGenerator:
    """
    NAZAHA-compliant report generator with exact government formatting
    2.5cm headers, official letterhead, Arabic RTL support
    """
    
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
        
        # Government margins (2.5cm as specified)
        self.margin_top = 2.5 * cm
        self.margin_bottom = 2.5 * cm
        self.margin_left = 2.5 * cm
        self.margin_right = 2.5 * cm
        
        # NAZAHA official colors
        self.nazaha_green = colors.Color(0, 0.5, 0.2)  # Official NAZAHA green
        self.nazaha_gold = colors.Color(0.8, 0.7, 0.1)  # Saudi gold
        
        # Register Arabic fonts (if available)
        self._register_arabic_fonts()
        
        # Style configuration
        self.styles = self._create_government_styles()

    def _register_arabic_fonts(self):
        """Register Arabic fonts for PDF generation"""
        try:
            # Try to register common Arabic fonts
            # In production, these would be installed system fonts
            arabic_fonts = [
                "NotoSansArabic-Regular.ttf",
                "Arial-Unicode-MS.ttf",
                "Tahoma.ttf"
            ]
            
            for font_file in arabic_fonts:
                font_path = Path(f"fonts/{font_file}")
                if font_path.exists():
                    pdfmetrics.registerFont(TTFont('Arabic', str(font_path)))
                    break
            else:
                # Fallback to system default
                print("Warning: No Arabic fonts found, using system default")
                
        except Exception as e:
            print(f"Font registration error: {e}")

    def _create_government_styles(self):
        """Create government-compliant text styles"""
        
        styles = getSampleStyleSheet()
        
        # Arabic title style
        styles.add(ParagraphStyle(
            name='ArabicTitle',
            parent=styles['Title'],
            fontName='Arabic',
            fontSize=18,
            alignment=TA_CENTER,
            textColor=self.nazaha_green,
            spaceAfter=20,
            rightIndent=0,
            leftIndent=0
        ))
        
        # Arabic header style
        styles.add(ParagraphStyle(
            name='ArabicHeader',
            parent=styles['Heading1'],
            fontName='Arabic',
            fontSize=14,
            alignment=TA_RIGHT,
            textColor=black,
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Arabic body text
        styles.add(ParagraphStyle(
            name='ArabicBody',
            parent=styles['Normal'],
            fontName='Arabic',
            fontSize=11,
            alignment=TA_RIGHT,
            textColor=black,
            spaceAfter=6,
            leading=16
        ))
        
        # English body text
        styles.add(ParagraphStyle(
            name='EnglishBody',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            textColor=colors.grey,
            spaceAfter=6
        ))
        
        # Government classification style
        styles.add(ParagraphStyle(
            name='Classification',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=red,
            fontName='Helvetica-Bold'
        ))
        
        return styles

    async def generate_pdf_report(self, report_data: Dict[str, Any]) -> str:
        """
        Generate PDF report in NAZAHA format
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            Path to generated PDF file
        """
        
        # Create output directory
        output_dir = Path("reports/daily")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        report_date = report_data.get("report_date_gregorian", datetime.now().date().isoformat())
        filename = f"nazaha_daily_report_{report_date.replace('-', '')}.pdf"
        output_path = output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right,
            title=f"NAZAHA Daily Report - {report_date}",
            author="Saudi AI Audit Platform"
        )
        
        # Build document content
        story = []
        
        # Add government header
        story.extend(self._create_government_header())
        
        # Add report title
        story.extend(self._create_report_title(report_data))
        
        # Add executive summary
        story.extend(self._create_executive_summary(report_data))
        
        # Add detailed analysis
        story.extend(self._create_detailed_analysis(report_data))
        
        # Add recommendations
        story.extend(self._create_recommendations(report_data))
        
        # Add footer
        story.extend(self._create_government_footer(report_data))
        
        # Build PDF
        doc.build(story)
        
        return str(output_path)

    def _create_government_header(self) -> List:
        """Create official government header with letterhead"""
        
        elements = []
        
        # Classification marking
        classification = Paragraph(
            "سري - للاستخدام الحكومي الداخلي فقط<br/>CONFIDENTIAL - INTERNAL GOVERNMENT USE ONLY",
            self.styles['Classification']
        )
        elements.append(classification)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Saudi emblem placeholder (would include actual emblem in production)
        emblem_text = Paragraph(
            "شعار المملكة العربية السعودية",
            self.styles['ArabicBody']
        )
        elements.append(emblem_text)
        elements.append(Spacer(1, 0.3 * cm))
        
        # Government header
        header_lines = [
            "المملكة العربية السعودية",
            "الهيئة الوطنية لمكافحة الفساد (نزاهة)",
            "إدارة الرقابة والتدقيق الرقمي"
        ]
        
        for line in header_lines:
            formatted_line = format_arabic_for_pdf(line)
            p = Paragraph(formatted_line, self.styles['ArabicHeader'])
            elements.append(p)
        
        # English header
        english_header = Paragraph(
            "Kingdom of Saudi Arabia<br/>National Anti-Corruption Commission (NAZAHA)<br/>Digital Monitoring and Audit Department",
            self.styles['EnglishBody']
        )
        elements.append(english_header)
        elements.append(Spacer(1, 1 * cm))
        
        return elements

    def _create_report_title(self, report_data: Dict[str, Any]) -> List:
        """Create report title section"""
        
        elements = []
        
        # Main title in Arabic
        title_ar = "التقرير اليومي لمراقبة الذكاء الاصطناعي في المشتريات الحكومية"
        title_formatted = format_arabic_for_pdf(title_ar)
        title = Paragraph(title_formatted, self.styles['ArabicTitle'])
        elements.append(title)
        
        # English title
        title_en = Paragraph(
            "Daily AI Monitoring Report for Government Procurement",
            self.styles['EnglishBody']
        )
        elements.append(title_en)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Date information
        report_date_hijri = report_data.get("report_date_hijri", "")
        report_date_gregorian = report_data.get("report_date_gregorian", "")
        
        date_text = f"تاريخ التقرير: {report_date_gregorian} الموافق {report_date_hijri}"
        date_formatted = format_arabic_for_pdf(date_text)
        date_para = Paragraph(date_formatted, self.styles['ArabicBody'])
        elements.append(date_para)
        
        elements.append(Spacer(1, 1 * cm))
        
        return elements

    def _create_executive_summary(self, report_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        
        elements = []
        
        # Section title
        summary_title = format_arabic_for_pdf("الملخص التنفيذي")
        title = Paragraph(summary_title, self.styles['ArabicHeader'])
        elements.append(title)
        
        # Key metrics table
        metrics_data = [
            ["المؤشر", "القيمة", "الحالة"],
            [
                format_arabic_for_pdf("إجمالي القرارات المحللة"),
                str(report_data.get("total_decisions", 0)),
                format_arabic_for_pdf("مكتمل")
            ],
            [
                format_arabic_for_pdf("تنبيهات التحيز"),
                str(report_data.get("bias_alerts_triggered", 0)),
                format_arabic_for_pdf("تحت المراجعة")
            ],
            [
                format_arabic_for_pdf("معدل الامتثال"),
                f"{report_data.get('overall_compliance_score', 1.0) * 100:.1f}%",
                format_arabic_for_pdf("متوافق")
            ]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[6*cm, 3*cm, 3*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.nazaha_green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Compliance status
        compliance_status = report_data.get("compliance_status", "متوافق")
        status_color = green if compliance_status == "متوافق" else red
        
        status_text = f"حالة الامتثال: {compliance_status}"
        status_formatted = format_arabic_for_pdf(status_text)
        status_para = Paragraph(
            f'<font color="{status_color.hexval()}">{status_formatted}</font>',
            self.styles['ArabicBody']
        )
        elements.append(status_para)
        
        elements.append(Spacer(1, 1 * cm))
        
        return elements

    def _create_detailed_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create detailed analysis section"""
        
        elements = []
        
        # Section title
        analysis_title = format_arabic_for_pdf("التحليل التفصيلي")
        title = Paragraph(analysis_title, self.styles['ArabicHeader'])
        elements.append(title)
        
        # Bias analysis
        bias_analysis = report_data.get("bias_analysis", {})
        
        # Regional bias section
        regional_title = format_arabic_for_pdf("تحليل التحيز الإقليمي")
        regional_para = Paragraph(regional_title, self.styles['ArabicBody'])
        elements.append(regional_para)
        
        regional_compliant = bias_analysis.get("regional_compliant", True)
        regional_status = "متوافق" if regional_compliant else "غير متوافق"
        regional_color = green if regional_compliant else red
        
        regional_text = f"الحالة: {regional_status}"
        regional_formatted = format_arabic_for_pdf(regional_text)
        regional_status_para = Paragraph(
            f'<font color="{regional_color.hexval()}">{regional_formatted}</font>',
            self.styles['ArabicBody']
        )
        elements.append(regional_status_para)
        
        # Performance metrics
        performance_title = format_arabic_for_pdf("مؤشرات الأداء")
        perf_para = Paragraph(performance_title, self.styles['ArabicBody'])
        elements.append(perf_para)
        
        performance_data = report_data.get("performance_metrics", {})
        avg_time = performance_data.get("avg_processing_time_ms", 0)
        sla_compliance = performance_data.get("sla_compliance_rate", 1.0)
        
        perf_text = f"متوسط وقت المعالجة: {avg_time:.1f} ملي ثانية\nمعدل الامتثال لاتفاقية مستوى الخدمة: {sla_compliance * 100:.1f}%"
        perf_formatted = format_arabic_for_pdf(perf_text)
        perf_details = Paragraph(perf_formatted, self.styles['ArabicBody'])
        elements.append(perf_details)
        
        elements.append(Spacer(1, 1 * cm))
        
        return elements

    def _create_recommendations(self, report_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        
        elements = []
        
        # Section title
        rec_title = format_arabic_for_pdf("التوصيات والإجراءات المطلوبة")
        title = Paragraph(rec_title, self.styles['ArabicHeader'])
        elements.append(title)
        
        # Recommendations list
        recommendations = report_data.get("recommendations", [
            "الاستمرار في المراقبة الدورية",
            "مراجعة القرارات المشبوهة",
            "تحديث إعدادات النظام"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"{i}. {rec}"
            rec_formatted = format_arabic_for_pdf(rec_text)
            rec_para = Paragraph(rec_formatted, self.styles['ArabicBody'])
            elements.append(rec_para)
        
        elements.append(Spacer(1, 0.5 * cm))
        
        # Next review date
        next_review = (datetime.now().date()).isoformat()
        review_text = f"تاريخ المراجعة القادمة: {next_review}"
        review_formatted = format_arabic_for_pdf(review_text)
        review_para = Paragraph(review_formatted, self.styles['ArabicBody'])
        elements.append(review_para)
        
        elements.append(Spacer(1, 1 * cm))
        
        return elements

    def _create_government_footer(self, report_data: Dict[str, Any]) -> List:
        """Create government footer with signatures and metadata"""
        
        elements = []
        
        # Signature section
        signature_title = format_arabic_for_pdf("المعتمدون")
        sig_title = Paragraph(signature_title, self.styles['ArabicHeader'])
        elements.append(sig_title)
        
        # Signature table
        signature_data = [
            [format_arabic_for_pdf("المراجع"), format_arabic_for_pdf("التوقيع"), format_arabic_for_pdf("التاريخ")],
            [format_arabic_for_pdf("مدير النظام"), "___________", datetime.now().strftime("%d/%m/%Y")],
            [format_arabic_for_pdf("مسؤول الامتثال"), "___________", datetime.now().strftime("%d/%m/%Y")]
        ]
        
        signature_table = Table(signature_data, colWidths=[4*cm, 4*cm, 4*cm])
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 1 * cm))
        
        # Document metadata
        metadata_text = f"""
        رقم التقرير: RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}
        تاريخ الإنشاء: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        نظام إنشاء التقرير: منصة تدقيق الذكاء الاصطناعي السعودية v1.0
        مستوى التصنيف: سري - للاستخدام الحكومي الداخلي
        فترة الاحتفاظ: 7 سنوات (حسب متطلبات نزاهة)
        """
        
        metadata_formatted = format_arabic_for_pdf(metadata_text)
        metadata_para = Paragraph(metadata_formatted, self.styles['ArabicBody'])
        elements.append(metadata_para)
        
        # Government seal placeholder
        seal_text = format_arabic_for_pdf("ختم الهيئة الوطنية لمكافحة الفساد")
        seal_para = Paragraph(seal_text, self.styles['Classification'])
        elements.append(seal_para)
        
        return elements

# Helper function for external use
async def generate_pdf_report(report_data: Dict[str, Any]) -> str:
    """
    Generate NAZAHA daily report PDF
    
    Args:
        report_data: Report data dictionary
        
    Returns:
        Path to generated PDF
    """
    
    generator = NAZAHAReportGenerator()
    return await generator.generate_pdf_report(report_data)

# Template configuration
TEMPLATE_CONFIG = {
    "name": "NAZAHA Daily Report",
    "description": "Official NAZAHA anti-corruption daily monitoring report",
    "format": "PDF",
    "language": "Arabic/English bilingual",
    "margins": "2.5cm all sides",
    "classification": "Confidential - Internal Government Use",
    "retention_period": "7 years",
    "compliance_standards": ["NAZAHA Guidelines", "Vision 2030 Digital Standards"]
}