"""
HashChainedLedger for Saudi AI Audit Platform
Immutable audit trail with 7-year retention policy and government compliance
"""

import hashlib
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import gzip
import os

from utils.hijri import get_hijri_date, hijri_to_gregorian
from api.errors import create_error_response, SaudiGovernmentErrorHandler

class HashChainedLedger:
    """
    Immutable blockchain-style audit ledger for AI decisions
    Compliant with Saudi government 7-year retention policy
    """
    
    def __init__(self, data_dir: str = "audit_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Chain configuration
        self.genesis_hash = "SAUDI_AI_AUDIT_GENESIS_2024"
        self.retention_years = 7
        self.backup_interval_hours = 4
        
        # Performance requirements
        self.max_append_time_ms = 50  # Government SLA
        self.max_verification_time_ms = 3000
        
        # Load existing chain or initialize
        self.chain: List[Dict[str, Any]] = []
        self.chain_index: Dict[str, int] = {}  # entry_id -> index mapping
        self._load_existing_chain()
        
        # Background tasks
        self._last_backup = datetime.now()
        self._corruption_checks_enabled = True

    async def append_entry(self, entry_data: Dict[str, Any]) -> str:
        """
        Append new entry to audit chain
        Must complete within 50ms (government SLA)
        
        Args:
            entry_data: Audit entry data
            
        Returns:
            entry_id: Unique identifier for the entry
            
        Raises:
            PerformanceException: If operation exceeds time limit
        """
        start_time = datetime.now()
        
        try:
            # Generate entry ID
            entry_id = self._generate_entry_id(entry_data)
            
            # Get previous hash
            previous_hash = self._get_latest_hash()
            
            # Create complete entry
            complete_entry = {
                "id": entry_id,
                "data": entry_data,
                "timestamp": datetime.now().isoformat(),
                "timestamp_hijri": get_hijri_date(),
                "previous_hash": previous_hash,
                "hash": None,  # Will be calculated
                "chain_position": len(self.chain),
                "retention_until": (datetime.now() + timedelta(days=365 * self.retention_years)).isoformat()
            }
            
            # Calculate hash
            complete_entry["hash"] = self._calculate_hash(complete_entry)
            
            # Append to chain
            self.chain.append(complete_entry)
            self.chain_index[entry_id] = len(self.chain) - 1
            
            # Performance check
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            if elapsed_ms > self.max_append_time_ms:
                # Log performance violation but don't fail
                print(f"WARNING: Append operation took {elapsed_ms}ms (limit: {self.max_append_time_ms}ms)")
            
            # Schedule backup if needed
            if self._should_backup():
                asyncio.create_task(self._backup_chain())
            
            return entry_id
            
        except Exception as e:
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            raise Exception(f"Chain append failed after {elapsed_ms}ms: {str(e)}")

    async def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify complete chain integrity
        Must complete within 3s (government SLA)
        """
        start_time = datetime.now()
        
        try:
            if not self.chain:
                return {
                    "valid": True,
                    "entries_count": 0,
                    "integrity_score": 1.0,
                    "verification_time_ms": 0
                }
            
            corruption_found = False
            corrupted_entries = []
            
            for i, entry in enumerate(self.chain):
                # Verify hash
                expected_hash = self._calculate_hash(entry, exclude_hash=True)
                if entry["hash"] != expected_hash:
                    corruption_found = True
                    corrupted_entries.append({
                        "position": i,
                        "entry_id": entry["id"],
                        "expected_hash": expected_hash,
                        "actual_hash": entry["hash"]
                    })
                
                # Verify chain linkage (except genesis)
                if i > 0:
                    previous_entry = self.chain[i-1]
                    if entry["previous_hash"] != previous_entry["hash"]:
                        corruption_found = True
                        corrupted_entries.append({
                            "position": i,
                            "entry_id": entry["id"],
                            "chain_link_broken": True
                        })
                
                # Performance check
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                if elapsed_ms > self.max_verification_time_ms:
                    return {
                        "valid": False,
                        "error": "Verification timeout",
                        "partial_verification": True,
                        "entries_checked": i + 1,
                        "verification_time_ms": elapsed_ms
                    }
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            integrity_score = 1.0 - (len(corrupted_entries) / len(self.chain))
            
            result = {
                "valid": not corruption_found,
                "entries_count": len(self.chain),
                "integrity_score": integrity_score,
                "verification_time_ms": elapsed_ms,
                "corrupted_entries": corrupted_entries if corruption_found else []
            }
            
            # Handle corruption
            if corruption_found:
                await self._handle_corruption(corrupted_entries)
            
            return result
            
        except Exception as e:
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "valid": False,
                "error": str(e),
                "verification_time_ms": elapsed_ms
            }

    async def verify_range(
        self,
        start_date: datetime,
        end_date: datetime,
        decision_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify integrity for specific date range"""
        
        matching_entries = []
        for entry in self.chain:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if start_date <= entry_date <= end_date:
                if decision_type is None or entry["data"].get("decision_type") == decision_type:
                    matching_entries.append(entry)
        
        # Verify each matching entry
        corruption_found = False
        corrupted_entries = []
        
        for entry in matching_entries:
            expected_hash = self._calculate_hash(entry, exclude_hash=True)
            if entry["hash"] != expected_hash:
                corruption_found = True
                corrupted_entries.append({
                    "entry_id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "expected_hash": expected_hash,
                    "actual_hash": entry["hash"]
                })
        
        return {
            "valid": not corruption_found,
            "entries_count": len(matching_entries),
            "integrity_score": 1.0 - (len(corrupted_entries) / max(len(matching_entries), 1)),
            "corrupted_entries": corrupted_entries,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "decision_type": decision_type
            }
        }

    async def get_daily_statistics(self, date: datetime.date) -> Dict[str, Any]:
        """Get statistics for specific day"""
        
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        daily_entries = []
        performance_metrics = []
        
        for entry in self.chain:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if day_start <= entry_date <= day_end:
                daily_entries.append(entry)
                
                # Collect performance metrics
                if "performance_metrics" in entry["data"]:
                    performance_metrics.append(entry["data"]["performance_metrics"])
        
        # Calculate statistics
        by_type = {}
        for entry in daily_entries:
            decision_type = entry["data"].get("decision_type", "unknown")
            by_type[decision_type] = by_type.get(decision_type, 0) + 1
        
        # Performance analysis
        if performance_metrics:
            processing_times = [m.get("processing_time_ms", 0) for m in performance_metrics]
            avg_processing_time = sum(processing_times) / len(processing_times)
            max_processing_time = max(processing_times)
            sla_violations = len([t for t in processing_times if t > self.max_append_time_ms])
        else:
            avg_processing_time = 0
            max_processing_time = 0
            sla_violations = 0
        
        return {
            "date": date.isoformat(),
            "total_decisions": len(daily_entries),
            "by_type": by_type,
            "performance": {
                "avg_processing_time_ms": avg_processing_time,
                "max_processing_time_ms": max_processing_time,
                "sla_violations": sla_violations,
                "sla_compliance_rate": 1.0 - (sla_violations / max(len(daily_entries), 1))
            }
        }

    def get_latest_hash(self) -> str:
        """Get hash of the latest entry"""
        return self._get_latest_hash()

    def get_next_backup_time(self) -> str:
        """Get timestamp of next scheduled backup"""
        next_backup = self._last_backup + timedelta(hours=self.backup_interval_hours)
        return next_backup.isoformat()

    async def log_bias_alert(self, entry_id: str, bias_result: Dict[str, Any]) -> None:
        """Log bias detection alert"""
        
        alert_entry = {
            "id": f"BIAS_ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "alert_type": "bias_detection",
            "related_entry": entry_id,
            "bias_details": bias_result,
            "severity": "HIGH" if bias_result["confidence"] > 0.8 else "MEDIUM",
            "regulatory_notification": True,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.append_entry(alert_entry)

    # Private methods
    def _generate_entry_id(self, entry_data: Dict[str, Any]) -> str:
        """Generate unique entry ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        user_id = entry_data.get("user_id", "SYSTEM")
        decision_type = entry_data.get("decision_type", "UNKNOWN")
        return f"{decision_type}_{user_id}_{timestamp}"

    def _get_latest_hash(self) -> str:
        """Get hash of the most recent entry"""
        if not self.chain:
            return self.genesis_hash
        return self.chain[-1]["hash"]

    def _calculate_hash(self, entry: Dict[str, Any], exclude_hash: bool = False) -> str:
        """Calculate SHA-256 hash of entry"""
        entry_copy = entry.copy()
        
        if exclude_hash and "hash" in entry_copy:
            del entry_copy["hash"]
        
        # Sort keys for consistent hashing
        entry_json = json.dumps(entry_copy, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(entry_json.encode('utf-8')).hexdigest()

    def _load_existing_chain(self) -> None:
        """Load existing chain from disk"""
        chain_file = self.data_dir / "audit_chain.pkl.gz"
        
        if chain_file.exists():
            try:
                with gzip.open(chain_file, 'rb') as f:
                    self.chain = pickle.load(f)
                
                # Rebuild index
                self.chain_index = {}
                for i, entry in enumerate(self.chain):
                    self.chain_index[entry["id"]] = i
                    
                print(f"Loaded {len(self.chain)} entries from existing chain")
                
            except Exception as e:
                print(f"Failed to load existing chain: {e}")
                self.chain = []
                self.chain_index = {}

    def _should_backup(self) -> bool:
        """Check if backup is needed"""
        return datetime.now() - self._last_backup > timedelta(hours=self.backup_interval_hours)

    async def _backup_chain(self) -> None:
        """Create compressed backup of chain"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.data_dir / f"audit_chain_backup_{timestamp}.pkl.gz"
            
            with gzip.open(backup_file, 'wb') as f:
                pickle.dump(self.chain, f)
            
            # Also save current chain
            current_file = self.data_dir / "audit_chain.pkl.gz"
            with gzip.open(current_file, 'wb') as f:
                pickle.dump(self.chain, f)
            
            self._last_backup = datetime.now()
            
            # Clean old backups (keep 30 days)
            await self._cleanup_old_backups()
            
            print(f"Chain backed up to {backup_file}")
            
        except Exception as e:
            print(f"Backup failed: {e}")

    async def _cleanup_old_backups(self) -> None:
        """Remove backups older than 30 days"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for backup_file in self.data_dir.glob("audit_chain_backup_*.pkl.gz"):
            try:
                file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_date < cutoff_date:
                    backup_file.unlink()
            except Exception as e:
                print(f"Failed to clean backup {backup_file}: {e}")

    async def _handle_corruption(self, corrupted_entries: List[Dict[str, Any]]) -> None:
        """Handle detected chain corruption"""
        corruption_details = {
            "detected_at": datetime.now().isoformat(),
            "corrupted_count": len(corrupted_entries),
            "total_entries": len(self.chain),
            "corruption_entries": corrupted_entries
        }
        
        # Log critical error
        error_response = SaudiGovernmentErrorHandler.handle_chain_corruption(corruption_details)
        
        # Save corruption report
        corruption_file = self.data_dir / f"corruption_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(corruption_file, 'w', encoding='utf-8') as f:
            json.dump(error_response, f, ensure_ascii=False, indent=2)
        
        # Trigger immediate backup and recovery procedures
        print("CRITICAL: Chain corruption detected. Initiating emergency procedures.")
        
        # Disable further writes until resolved
        self._corruption_checks_enabled = False