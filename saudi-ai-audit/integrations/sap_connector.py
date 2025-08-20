"""
SAP Government Backend Integration
DD.MM.YYYY date format and Windows-1252 encoding support
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import xml.etree.ElementTree as ET
from pathlib import Path

from modules.procurement.models import ProcurementDecision, VendorDetails
from utils.arabic import convert_arabic_to_latin, ensure_encoding
from api.errors import SaudiGovernmentErrorHandler

class SAPConnector:
    """
    Integration with Saudi Government SAP backend systems
    Handles legacy date formats and Windows-1252 encoding
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.sap_host = config.get("sap_host")
        self.sap_port = config.get("sap_port", 8000)
        self.client = config.get("sap_client", "100")
        self.username = config.get("sap_username")
        self.password = config.get("sap_password")
        self.language = config.get("sap_language", "AR")  # Arabic
        
        # SAP-specific configuration
        self.encoding = "windows-1252"  # SAP legacy encoding  
        self.date_format = "%d.%m.%Y"   # DD.MM.YYYY format required by SAP
        self.time_format = "%H:%M:%S"
        self.decimal_separator = ","    # European decimal format
        
        # Arabic locale issues in SAP
        self.arabic_locale_issues = {
            "rtl_support": "Limited RTL support in SAP GUI",
            "font_rendering": "Arabic fonts may not render correctly",
            "number_formatting": "Arabic numerals converted to Western",
            "date_calendar": "Only Gregorian calendar supported"
        }
        
        # SAP module configurations
        self.modules = {
            "MM": "Materials Management",
            "FI": "Financial Accounting", 
            "CO": "Controlling",
            "SD": "Sales & Distribution"
        }
        
        # Known SAP issues in government environments
        self.known_issues = {
            "date_format_strict": "SAP rejects dates not in DD.MM.YYYY format",
            "encoding_legacy": "Arabic text requires special handling in Windows-1252",
            "decimal_format": "Amounts must use comma as decimal separator",
            "transaction_timeout": "Long-running transactions timeout after 30 minutes",
            "batch_processing": "Large datasets require RFC batch processing"
        }
        
        # Authentication token
        self._auth_token = None
        self._token_expires = None

    async def authenticate(self) -> bool:
        """
        Authenticate with SAP system
        
        Returns:
            True if authentication successful
        """
        
        try:
            auth_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/authenticate"
            
            auth_data = {
                "client": self.client,
                "username": self.username,
                "password": self.password,
                "language": self.language
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, json=auth_data) as response:
                    
                    if response.status == 200:
                        auth_result = await response.json()
                        self._auth_token = auth_result.get("token")
                        
                        # Token typically expires in 8 hours
                        self._token_expires = datetime.now().timestamp() + (8 * 3600)
                        
                        return True
                    else:
                        print(f"SAP authentication failed: {response.status}")
                        return False
        
        except Exception as e:
            print(f"SAP authentication error: {e}")
            return False

    async def submit_procurement_record(self, decision: ProcurementDecision) -> Dict[str, Any]:
        """
        Submit procurement decision to SAP system
        
        Args:
            decision: ProcurementDecision object
            
        Returns:
            SAP submission result
        """
        
        try:
            # Ensure authentication
            if not await self._ensure_authenticated():
                raise Exception("SAP authentication failed")
            
            # Convert decision to SAP format
            sap_record = await self._convert_to_sap_format(decision)
            
            # Submit to SAP MM module
            submission_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/mm/procurement"
            
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "Content-Type": "application/json; charset=windows-1252",
                "Accept": "application/json",
                "X-SAP-Client": self.client
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    submission_url,
                    json=sap_record,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        return {
                            "success": True,
                            "sap_document_number": result.get("document_number"),
                            "sap_fiscal_year": result.get("fiscal_year"),
                            "posting_date": result.get("posting_date"),
                            "status": "posted",
                            "submission_time": datetime.now().isoformat()
                        }
                    
                    elif response.status == 400:
                        error_detail = await response.json()
                        return {
                            "success": False,
                            "error": "SAP validation error",
                            "details": error_detail,
                            "suggestion": "Check date format and required fields"
                        }
                    
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"SAP submission failed: {response.status}",
                            "details": error_text
                        }
        
        except Exception as e:
            return SaudiGovernmentErrorHandler.handle_sap_integration_error(str(e))

    async def fetch_vendor_master_data(self, vendor_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch vendor master data from SAP
        
        Args:
            vendor_code: SAP vendor code
            
        Returns:
            Vendor master data or None
        """
        
        try:
            if not await self._ensure_authenticated():
                return None
            
            fetch_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/mm/vendor/{vendor_code}"
            
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "X-SAP-Client": self.client
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(fetch_url, headers=headers) as response:
                    
                    if response.status == 200:
                        vendor_data = await response.json()
                        return self._parse_sap_vendor_data(vendor_data)
                    
                    elif response.status == 404:
                        return None
                    
                    else:
                        print(f"SAP vendor fetch failed: {response.status}")
                        return None
        
        except Exception as e:
            print(f"Error fetching vendor {vendor_code}: {e}")
            return None

    async def export_financial_report(self, start_date: date, end_date: date, output_path: str) -> Dict[str, Any]:
        """
        Export financial report from SAP FI module
        
        Args:
            start_date: Report start date
            end_date: Report end date
            output_path: Output file path
            
        Returns:
            Export result
        """
        
        try:
            if not await self._ensure_authenticated():
                raise Exception("SAP authentication required")
            
            # Format dates for SAP
            start_sap = start_date.strftime(self.date_format)
            end_sap = end_date.strftime(self.date_format)
            
            report_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/fi/reports/procurement"
            
            params = {
                "start_date": start_sap,
                "end_date": end_sap,
                "report_type": "PROCUREMENT_SUMMARY",
                "format": "JSON"
            }
            
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "X-SAP-Client": self.client
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(report_url, params=params, headers=headers) as response:
                    
                    if response.status == 200:
                        report_data = await response.json()
                        
                        # Save report
                        output_file = Path(output_path)
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(report_data, f, ensure_ascii=False, indent=2)
                        
                        return {
                            "success": True,
                            "output_file": str(output_file),
                            "report_period": f"{start_sap} - {end_sap}",
                            "records_count": len(report_data.get("records", [])),
                            "total_amount": report_data.get("total_amount", 0),
                            "export_time": datetime.now().isoformat()
                        }
                    
                    else:
                        raise Exception(f"SAP report export failed: {response.status}")
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check date format and SAP connectivity"
            }

    async def sync_chart_of_accounts(self) -> Dict[str, Any]:
        """
        Synchronize chart of accounts from SAP
        
        Returns:
            Synchronization result
        """
        
        try:
            if not await self._ensure_authenticated():
                raise Exception("SAP authentication required")
            
            coa_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/fi/chart_of_accounts"
            
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "X-SAP-Client": self.client
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(coa_url, headers=headers) as response:
                    
                    if response.status == 200:
                        coa_data = await response.json()
                        
                        # Process accounts
                        accounts = []
                        for account in coa_data.get("accounts", []):
                            processed_account = {
                                "account_number": account.get("account_number"),
                                "account_name_ar": account.get("short_text_ar"),
                                "account_name_en": account.get("short_text_en"),
                                "account_group": account.get("account_group"),
                                "balance_sheet_item": account.get("balance_sheet_item"),
                                "profit_loss_item": account.get("profit_loss_item")
                            }
                            accounts.append(processed_account)
                        
                        return {
                            "success": True,
                            "accounts_synced": len(accounts),
                            "sync_time": datetime.now().isoformat(),
                            "chart_of_accounts": accounts[:20]  # Sample of first 20
                        }
                    
                    else:
                        raise Exception(f"Chart of accounts sync failed: {response.status}")
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check SAP FI module accessibility"
            }

    async def create_purchase_order(self, decision: ProcurementDecision) -> Dict[str, Any]:
        """
        Create purchase order in SAP based on procurement decision
        
        Args:
            decision: ProcurementDecision object
            
        Returns:
            Purchase order creation result
        """
        
        try:
            if not await self._ensure_authenticated():
                raise Exception("SAP authentication required")
            
            if not decision.winning_vendor or decision.decision_status != "منح":
                raise Exception("Cannot create PO for non-awarded decision")
            
            # Create PO data structure
            po_data = {
                "vendor_code": decision.winning_vendor.commercial_registration,
                "purchase_organization": "1000",  # Default gov org
                "purchasing_group": "001",
                "document_type": "NB",  # Standard PO
                "created_on": datetime.now().strftime(self.date_format),
                "currency": "SAR",
                "total_amount": str(decision.award_amount_sar).replace(".", self.decimal_separator),
                "payment_terms": "Z001",  # Government standard terms
                "reference_number": decision.decision_id,
                "header_text": convert_arabic_to_latin(decision.decision_reasoning_ar[:40])
            }
            
            po_url = f"http://{self.sap_host}:{self.sap_port}/sap/bc/rest/mm/purchase_order"
            
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "Content-Type": "application/json; charset=windows-1252",
                "X-SAP-Client": self.client
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(po_url, json=po_data, headers=headers) as response:
                    
                    if response.status == 201:
                        po_result = await response.json()
                        
                        return {
                            "success": True,
                            "po_number": po_result.get("po_number"),
                            "po_date": po_result.get("po_date"),
                            "vendor_code": po_result.get("vendor_code"),
                            "total_amount": po_result.get("total_amount"),
                            "status": "created",
                            "sap_message": po_result.get("message")
                        }
                    
                    else:
                        error_detail = await response.text()
                        return {
                            "success": False,
                            "error": f"PO creation failed: {response.status}",
                            "details": error_detail
                        }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check vendor master data and amounts"
            }

    # Private helper methods
    async def _ensure_authenticated(self) -> bool:
        """Ensure valid authentication token"""
        
        if not self._auth_token or not self._token_expires:
            return await self.authenticate()
        
        # Check if token is about to expire (refresh 30 minutes early)
        if datetime.now().timestamp() > (self._token_expires - 1800):
            return await self.authenticate()
        
        return True

    async def _convert_to_sap_format(self, decision: ProcurementDecision) -> Dict[str, Any]:
        """Convert ProcurementDecision to SAP-compatible format"""
        
        # SAP document structure
        sap_doc = {
            "document_header": {
                "document_type": "PROCUREMENT_DECISION",
                "document_date": decision.decision_date_gregorian.strftime(self.date_format),
                "posting_date": datetime.now().strftime(self.date_format),
                "reference": decision.decision_id,
                "header_text": convert_arabic_to_latin(decision.decision_reasoning_ar[:50]),
                "currency": "SAR",
                "company_code": "1000"  # Government company code
            },
            "tender_details": {
                "tender_number": decision.tender.tender_number,
                "tender_title": convert_arabic_to_latin(decision.tender.tender_title_ar),
                "procurement_type": decision.tender.procurement_type.value,
                "estimated_value": str(decision.tender.estimated_value_sar).replace(".", self.decimal_separator),
                "procuring_entity": convert_arabic_to_latin(decision.tender.procuring_entity_ar)
            }
        }
        
        # Add vendor information if available
        if decision.winning_vendor:
            sap_doc["vendor_details"] = {
                "vendor_code": decision.winning_vendor.commercial_registration,
                "vendor_name": convert_arabic_to_latin(decision.winning_vendor.name_ar),
                "region": decision.winning_vendor.region.value,
                "vendor_size": decision.winning_vendor.vendor_size
            }
        
        # Add financial information
        if decision.award_amount_sar:
            sap_doc["financial_details"] = {
                "award_amount": str(decision.award_amount_sar).replace(".", self.decimal_separator),
                "currency": "SAR",
                "payment_terms": "Z001",  # Government standard
                "gl_account": "2000000",  # Procurement expense account
                "cost_center": decision.tender.budget_code.replace("-", "")[:10]
            }
        
        return sap_doc

    def _parse_sap_vendor_data(self, sap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse SAP vendor master data"""
        
        return {
            "vendor_code": sap_data.get("vendor_code"),
            "name_ar": sap_data.get("name1"),
            "name_en": sap_data.get("name2"),
            "commercial_registration": sap_data.get("tax_number1"),
            "address": {
                "street": sap_data.get("street"),
                "city": sap_data.get("city1"),
                "postal_code": sap_data.get("postal_code"),
                "country": sap_data.get("country")
            },
            "contact": {
                "telephone": sap_data.get("telephone1"),
                "fax": sap_data.get("fax_number"),
                "email": sap_data.get("smtp_addr")
            },
            "payment_terms": sap_data.get("payment_terms"),
            "currency": sap_data.get("currency"),
            "created_on": sap_data.get("created_on"),
            "last_changed": sap_data.get("last_changed")
        }

    def format_sap_date(self, date_obj: Union[datetime, date]) -> str:
        """Format date for SAP (DD.MM.YYYY)"""
        
        if isinstance(date_obj, datetime):
            return date_obj.strftime(self.date_format)
        elif isinstance(date_obj, date):
            return date_obj.strftime(self.date_format)
        else:
            raise ValueError("Invalid date object")

    def format_sap_amount(self, amount: Union[Decimal, float, int]) -> str:
        """Format amount for SAP (comma as decimal separator)"""
        
        if isinstance(amount, Decimal):
            amount_str = str(amount)
        else:
            amount_str = f"{amount:.2f}"
        
        return amount_str.replace(".", self.decimal_separator)

    def get_known_issues_info(self) -> Dict[str, Any]:
        """Get information about known SAP integration issues"""
        
        return {
            "known_issues": {**self.known_issues, **self.arabic_locale_issues},
            "troubleshooting": {
                "date_format_strict": [
                    "Always use DD.MM.YYYY format for dates",
                    "Use format_sap_date() method for consistency",
                    "Example: 15.01.2024 (not 2024-01-15)"
                ],
                "encoding_legacy": [
                    "Convert Arabic text to Latin using convert_arabic_to_latin()",
                    "Limit text fields to ASCII characters where possible",
                    "Test with Arabic characters: ا ب ت"
                ],
                "decimal_format": [
                    "Use comma (,) as decimal separator",
                    "Use format_sap_amount() method",
                    "Example: 1000,50 (not 1000.50)"
                ],
                "transaction_timeout": [
                    "Break large operations into smaller batches",
                    "Use RFC calls for bulk operations",
                    "Monitor transaction time"
                ],
                "arabic_locale_issues": [
                    "Use convert_arabic_to_latin() for text fields",
                    "Test Arabic number formatting in amount fields",
                    "Verify date format with Gregorian calendar only",
                    "Check font rendering in SAP GUI"
                ]
            },
            "support_contacts": {
                "sap_basis": "sap-basis@mof.gov.sa",
                "functional_support": "sap-mm@mof.gov.sa",
                "emergency": "+966-11-401-2345"
            },
            "sap_modules": self.modules
        }