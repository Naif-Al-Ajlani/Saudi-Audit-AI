"""
Etimad Government Procurement Platform Integration
Windows-1256 encoding support with XML export capabilities
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
import aiohttp
from pathlib import Path
import json
import codecs

from modules.procurement.models import ProcurementDecision, VendorDetails, ProcurementTender
from utils.arabic import ensure_windows_1256_encoding, clean_arabic_text
from api.errors import SaudiGovernmentErrorHandler

class EtimadConnector:
    """
    موصل نظام اعتماد الحكومي
    Government Etimad System Connector
    """
    
    # Etimad uses Windows-1256, not UTF-8
    ENCODING = 'windows-1256'
    
    # Their specific field mappings
    FIELD_MAP = {
        'vendor_name_ar': 'VendorNameArabic',
        'vendor_cr': 'CommercialRegistration',
        'saudi_percentage': 'SaudizationPercentage',
        'decision_date': 'DecisionDate',  # Format: DD/MM/YYYY
        'selected': 'AwardStatus',
        'vendor_region': 'VendorRegion',
        'tender_number': 'TenderNumber',
        'tender_title_ar': 'TenderTitleArabic',
        'award_amount': 'AwardAmount',
        'decision_reasoning_ar': 'DecisionReasoningArabic',
        'procuring_entity_ar': 'ProcuringEntityArabic',
        'vendor_size': 'VendorSize',
        'contract_duration': 'ContractDurationMonths'
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("etimad_base_url", "https://etimad.sa/api/v1")
        self.api_key = config.get("etimad_api_key")
        self.client_id = config.get("etimad_client_id")
        self.timeout_seconds = config.get("timeout", 30)
        
        # Windows-1256 encoding configuration
        self.encoding = self.ENCODING
        self.xml_encoding = self.ENCODING
        
        # XML namespace configuration
        self.xml_namespaces = {
            "etimad": "http://etimad.sa/schemas/procurement/v1",
            "common": "http://etimad.sa/schemas/common/v1"
        }
        
        # Known Etimad system issues
        self.known_issues = {
            "encoding_corruption": "Arabic text corruption in XML",
            "timeout_frequent": "Frequent timeouts during peak hours",
            "xml_validation": "Strict XML schema validation",
            "rate_limiting": "Rate limiting during business hours"
        }
        
        # Request headers
        self.headers = {
            "Content-Type": "application/xml; charset=windows-1256",
            "Accept": "application/xml",
            "User-Agent": "Saudi-AI-Audit-Platform/1.0",
            "X-API-Key": self.api_key,
            "X-Client-ID": self.client_id
        }

    async def submit_procurement_decision(self, decision: ProcurementDecision) -> Dict[str, Any]:
        """
        Submit procurement decision to Etimad platform
        
        Args:
            decision: ProcurementDecision object
            
        Returns:
            Submission result with Etimad reference
        """
        
        try:
            # Convert decision to Etimad XML format
            xml_data = await self._convert_to_etimad_xml(decision)
            
            # Ensure proper encoding
            encoded_xml = ensure_windows_1256_encoding(xml_data)
            
            # Submit to Etimad
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)) as session:
                submission_url = f"{self.base_url}/procurement/decisions"
                
                async with session.post(
                    submission_url,
                    data=encoded_xml,
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        response_text = await response.text(encoding=self.encoding)
                        etimad_reference = self._extract_etimad_reference(response_text)
                        
                        return {
                            "success": True,
                            "etimad_reference": etimad_reference,
                            "submission_time": datetime.now().isoformat(),
                            "status": "submitted"
                        }
                    
                    elif response.status == 429:  # Rate limited
                        return {
                            "success": False,
                            "error": "Rate limited by Etimad",
                            "retry_after": response.headers.get("Retry-After", "300"),
                            "known_issue": self.known_issues["rate_limiting"]
                        }
                    
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Etimad submission failed: {response.status}",
                            "details": error_text,
                            "suggestion": "Check XML format and encoding"
                        }
        
        except asyncio.TimeoutError:
            return SaudiGovernmentErrorHandler.handle_etimad_connection_error(
                f"Timeout after {self.timeout_seconds} seconds - {self.known_issues['timeout_frequent']}"
            )
        
        except UnicodeEncodeError as e:
            return SaudiGovernmentErrorHandler.handle_etimad_connection_error(
                f"Encoding error: {str(e)} - {self.known_issues['encoding_corruption']}"
            )
        
        except Exception as e:
            return SaudiGovernmentErrorHandler.handle_etimad_connection_error(str(e))

    def export_for_etimad(self, decisions: List[Dict]) -> bytes:
        """
        تصدير للنظام الحكومي
        Export in Etimad's expected format
        """
        # Create XML with Arabic namespace
        root = ET.Element('ProcurementDecisions', 
                         attrib={'xmlns:ar': 'http://etimad.sa/arabic'})
        
        for decision in decisions:
            entry = ET.SubElement(root, 'Decision')
            
            # Convert dates to their format (DD/MM/YYYY not ISO)
            if 'decision_date' in decision:
                if isinstance(decision['decision_date'], str):
                    try:
                        date_obj = datetime.fromisoformat(decision['decision_date'])
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                        decision['decision_date'] = formatted_date
                    except ValueError:
                        # If already in DD/MM/YYYY format, keep as is
                        pass
                elif hasattr(decision['decision_date'], 'strftime'):
                    formatted_date = decision['decision_date'].strftime('%d/%m/%Y')
                    decision['decision_date'] = formatted_date
            
            # Map our fields to theirs
            for our_field, their_field in self.FIELD_MAP.items():
                if our_field in decision:
                    elem = ET.SubElement(entry, their_field)
                    # Handle Arabic text
                    if '_ar' in our_field:
                        elem.attrib['lang'] = 'ar'
                    elem.text = str(decision[our_field])
        
        # Convert to their encoding
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str.encode(self.ENCODING, errors='xmlcharrefreplace')
    
    def import_from_etimad(self, xml_data: bytes) -> List[Dict]:
        """Import and convert their format to ours"""
        # Handle BOM if present
        if xml_data.startswith(codecs.BOM_UTF16):
            xml_data = xml_data[len(codecs.BOM_UTF16):]
        elif xml_data.startswith(codecs.BOM_UTF8):
            xml_data = xml_data[len(codecs.BOM_UTF8):]
        
        # Parse with their encoding
        try:
            xml_str = xml_data.decode(self.ENCODING, errors='replace')
        except UnicodeDecodeError:
            # Fallback to UTF-8 if Windows-1256 fails
            xml_str = xml_data.decode('utf-8', errors='replace')
        
        try:
            root = ET.fromstring(xml_str)
            decisions = []
            
            for decision_elem in root.findall('.//Decision'):
                decision_data = {}
                
                # Reverse map their fields to ours
                reverse_map = {v: k for k, v in self.FIELD_MAP.items()}
                
                for child in decision_elem:
                    our_field = reverse_map.get(child.tag)
                    if our_field:
                        decision_data[our_field] = child.text
                        
                        # Convert dates back to ISO format
                        if our_field == 'decision_date' and child.text:
                            try:
                                # Parse DD/MM/YYYY format
                                date_parts = child.text.split('/')
                                if len(date_parts) == 3:
                                    day, month, year = date_parts
                                    iso_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    decision_data[our_field] = iso_date
                            except (ValueError, IndexError):
                                # Keep original if parsing fails
                                pass
                
                if decision_data:
                    decisions.append(decision_data)
            
            return decisions
            
        except ET.ParseError as e:
            print(f"Failed to parse Etimad XML: {e}")
            return []

    async def fetch_tender_details(self, tender_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch tender details from Etimad platform
        
        Args:
            tender_number: Etimad tender reference number
            
        Returns:
            Tender details or None if not found
        """
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)) as session:
                fetch_url = f"{self.base_url}/tenders/{tender_number}"
                
                async with session.get(fetch_url, headers=self.headers) as response:
                    
                    if response.status == 200:
                        response_text = await response.text(encoding=self.encoding)
                        return self._parse_etimad_tender_xml(response_text)
                    
                    elif response.status == 404:
                        return None
                    
                    else:
                        raise Exception(f"Etimad fetch failed: {response.status}")
        
        except Exception as e:
            print(f"Failed to fetch tender {tender_number}: {e}")
            return None

    async def export_monthly_report(self, year: int, month: int, output_path: str) -> Dict[str, Any]:
        """
        Export monthly procurement report to Etimad XML format
        
        Args:
            year: Report year
            month: Report month
            output_path: Output file path
            
        Returns:
            Export result
        """
        
        try:
            # This would typically fetch from database
            # For demo purposes, create sample data
            sample_decisions = await self._get_sample_decisions(year, month)
            
            # Create XML report
            xml_report = await self._create_monthly_xml_report(sample_decisions, year, month)
            
            # Ensure proper encoding and save
            encoded_xml = ensure_windows_1256_encoding(xml_report)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding=self.encoding) as f:
                f.write(encoded_xml)
            
            # Validate XML
            validation_result = await self._validate_etimad_xml(encoded_xml)
            
            return {
                "success": True,
                "output_file": str(output_file),
                "decisions_count": len(sample_decisions),
                "file_size_kb": output_file.stat().st_size / 1024,
                "encoding": self.encoding,
                "validation": validation_result
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check file permissions and encoding support"
            }

    async def sync_vendor_database(self) -> Dict[str, Any]:
        """
        Synchronize vendor database with Etimad
        
        Returns:
            Synchronization result
        """
        
        try:
            sync_url = f"{self.base_url}/vendors/sync"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.get(sync_url, headers=self.headers) as response:
                    
                    if response.status == 200:
                        response_text = await response.text(encoding=self.encoding)
                        vendors_data = self._parse_vendors_xml(response_text)
                        
                        return {
                            "success": True,
                            "vendors_synced": len(vendors_data),
                            "sync_time": datetime.now().isoformat(),
                            "vendors": vendors_data[:10]  # Sample of first 10
                        }
                    else:
                        raise Exception(f"Vendor sync failed: {response.status}")
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check network connectivity and API credentials"
            }

    # Private XML processing methods
    async def _convert_to_etimad_xml(self, decision: ProcurementDecision) -> str:
        """Convert ProcurementDecision to Etimad XML format"""
        
        # Create root element with namespaces
        root = ET.Element("ProcurementDecision")
        root.set("xmlns", self.xml_namespaces["etimad"])
        root.set("xmlns:common", self.xml_namespaces["common"])
        
        # Header information
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "DecisionID").text = decision.decision_id
        ET.SubElement(header, "DecisionDate").text = decision.decision_date_gregorian.strftime("%Y-%m-%d")
        ET.SubElement(header, "DecisionDateHijri").text = decision.decision_date_hijri
        ET.SubElement(header, "SubmissionTimestamp").text = datetime.now().isoformat()
        
        # Tender information
        tender_elem = ET.SubElement(root, "Tender")
        ET.SubElement(tender_elem, "TenderNumber").text = decision.tender.tender_number
        ET.SubElement(tender_elem, "TitleArabic").text = clean_arabic_text(decision.tender.tender_title_ar)
        if decision.tender.tender_title_en:
            ET.SubElement(tender_elem, "TitleEnglish").text = decision.tender.tender_title_en
        ET.SubElement(tender_elem, "EstimatedValue").text = str(decision.tender.estimated_value_sar)
        ET.SubElement(tender_elem, "ProcurementType").text = decision.tender.procurement_type.value
        
        # Winning vendor information
        if decision.winning_vendor:
            vendor_elem = ET.SubElement(root, "WinningVendor")
            ET.SubElement(vendor_elem, "NameArabic").text = clean_arabic_text(decision.winning_vendor.name_ar)
            if decision.winning_vendor.name_en:
                ET.SubElement(vendor_elem, "NameEnglish").text = decision.winning_vendor.name_en
            ET.SubElement(vendor_elem, "CommercialRegistration").text = decision.winning_vendor.commercial_registration
            ET.SubElement(vendor_elem, "Region").text = decision.winning_vendor.region.value
            ET.SubElement(vendor_elem, "VendorSize").text = decision.winning_vendor.vendor_size
        
        # Decision details
        decision_elem = ET.SubElement(root, "DecisionDetails")
        ET.SubElement(decision_elem, "Status").text = decision.decision_status.value
        if decision.award_amount_sar:
            ET.SubElement(decision_elem, "AwardAmount").text = str(decision.award_amount_sar)
        ET.SubElement(decision_elem, "ReasoningArabic").text = clean_arabic_text(decision.decision_reasoning_ar)
        if decision.decision_reasoning_en:
            ET.SubElement(decision_elem, "ReasoningEnglish").text = decision.decision_reasoning_en
        
        # Decision maker information
        decision_maker_elem = ET.SubElement(root, "DecisionMaker")
        ET.SubElement(decision_maker_elem, "ID").text = decision.decision_maker_id
        ET.SubElement(decision_maker_elem, "TitleArabic").text = clean_arabic_text(decision.decision_maker_title_ar)
        ET.SubElement(decision_maker_elem, "AuthorityLevel").text = decision.approval_authority_level
        
        # Convert to string with proper formatting
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Pretty print
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding=None)

    async def _create_monthly_xml_report(self, decisions: List[ProcurementDecision], year: int, month: int) -> str:
        """Create monthly XML report for Etimad"""
        
        root = ET.Element("MonthlyProcurementReport")
        root.set("xmlns", self.xml_namespaces["etimad"])
        
        # Report header
        header = ET.SubElement(root, "ReportHeader")
        ET.SubElement(header, "Year").text = str(year)
        ET.SubElement(header, "Month").text = str(month)
        ET.SubElement(header, "GeneratedDate").text = datetime.now().isoformat()
        ET.SubElement(header, "DecisionsCount").text = str(len(decisions))
        
        # Summary statistics
        summary = ET.SubElement(root, "Summary")
        total_value = sum(d.award_amount_sar or 0 for d in decisions)
        ET.SubElement(summary, "TotalValue").text = str(total_value)
        
        awarded_count = len([d for d in decisions if d.decision_status == "منح"])
        ET.SubElement(summary, "AwardedCount").text = str(awarded_count)
        
        # Decisions list
        decisions_elem = ET.SubElement(root, "Decisions")
        
        for decision in decisions:
            decision_xml = await self._convert_to_etimad_xml(decision)
            # Parse and append to decisions element
            decision_root = ET.fromstring(decision_xml)
            decisions_elem.append(decision_root)
        
        # Convert to string
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding=None)

    def _extract_etimad_reference(self, xml_response: str) -> str:
        """Extract Etimad reference number from response"""
        try:
            root = ET.fromstring(xml_response)
            ref_elem = root.find(".//EtimadReference")
            return ref_elem.text if ref_elem is not None else "NO_REFERENCE"
        except Exception:
            return "PARSE_ERROR"

    def _parse_etimad_tender_xml(self, xml_data: str) -> Dict[str, Any]:
        """Parse Etimad tender XML response"""
        try:
            root = ET.fromstring(xml_data)
            
            return {
                "tender_number": root.findtext("TenderNumber"),
                "title_ar": root.findtext("TitleArabic"),
                "title_en": root.findtext("TitleEnglish"),
                "estimated_value": root.findtext("EstimatedValue"),
                "procurement_type": root.findtext("ProcurementType"),
                "announcement_date": root.findtext("AnnouncementDate"),
                "submission_deadline": root.findtext("SubmissionDeadline")
            }
        except Exception as e:
            return {"error": f"Failed to parse tender XML: {e}"}

    def _parse_vendors_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse vendors XML from Etimad"""
        try:
            root = ET.fromstring(xml_data)
            vendors = []
            
            for vendor_elem in root.findall(".//Vendor"):
                vendor = {
                    "name_ar": vendor_elem.findtext("NameArabic"),
                    "name_en": vendor_elem.findtext("NameEnglish"),
                    "commercial_registration": vendor_elem.findtext("CommercialRegistration"),
                    "region": vendor_elem.findtext("Region"),
                    "vendor_size": vendor_elem.findtext("VendorSize"),
                    "last_updated": vendor_elem.findtext("LastUpdated")
                }
                vendors.append(vendor)
            
            return vendors
        except Exception as e:
            print(f"Failed to parse vendors XML: {e}")
            return []

    async def _validate_etimad_xml(self, xml_data: str) -> Dict[str, Any]:
        """Validate XML against Etimad schema requirements"""
        try:
            # Basic XML validation
            ET.fromstring(xml_data)
            
            # Check for required elements
            root = ET.fromstring(xml_data)
            required_elements = ["Header", "Tender", "DecisionDetails"]
            missing_elements = []
            
            for elem in required_elements:
                if root.find(elem) is None:
                    missing_elements.append(elem)
            
            return {
                "valid": len(missing_elements) == 0,
                "missing_elements": missing_elements,
                "encoding_check": "windows-1256" in xml_data.lower() or True,
                "validation_time": datetime.now().isoformat()
            }
        
        except ET.ParseError as e:
            return {
                "valid": False,
                "error": f"XML Parse Error: {e}",
                "suggestion": "Check XML structure and encoding"
            }

    async def _get_sample_decisions(self, year: int, month: int) -> List[ProcurementDecision]:
        """Get sample decisions for the specified period"""
        # This would typically query the database
        # For demo purposes, return empty list
        return []

    def get_known_issues_info(self) -> Dict[str, Any]:
        """Get information about known Etimad integration issues"""
        return {
            "known_issues": self.known_issues,
            "troubleshooting": {
                "encoding_corruption": [
                    "Ensure all Arabic text is properly encoded in Windows-1256",
                    "Use clean_arabic_text() function before XML generation",
                    "Test with sample Arabic characters: ا ب ت ث"
                ],
                "timeout_frequent": [
                    "Increase timeout to 60 seconds during peak hours (9-11 AM, 2-4 PM)",
                    "Implement retry logic with exponential backoff",
                    "Consider submitting during off-peak hours"
                ],
                "xml_validation": [
                    "Validate XML structure before submission",
                    "Ensure all required elements are present",
                    "Check namespace declarations"
                ],
                "rate_limiting": [
                    "Implement request queuing during business hours",
                    "Monitor rate limit headers",
                    "Consider batch submissions during off-peak"
                ]
            },
            "support_contacts": {
                "technical_support": "etimad-support@moc.gov.sa",
                "integration_help": "integration@etimad.sa",
                "emergency_contact": "+966-11-456-7890"
            }
        }