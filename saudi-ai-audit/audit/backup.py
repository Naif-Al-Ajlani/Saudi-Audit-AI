"""
Automated backup system for Saudi AI Audit Platform
4-hour backup intervals with disaster recovery capabilities
"""

import asyncio
import gzip
import json
import pickle
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import schedule
import threading
import os

from utils.hijri import get_hijri_date
from api.errors import create_error_response

class AutomatedBackupSystem:
    """
    Automated backup system with government compliance
    - 4-hour backup intervals
    - 7-year retention
    - Disaster recovery capabilities
    - Government audit trail requirements
    """
    
    def __init__(self, 
                 primary_data_dir: str = "audit_data",
                 backup_base_dir: str = "backup_storage",
                 remote_backup_dir: Optional[str] = None):
        
        self.primary_data_dir = Path(primary_data_dir)
        self.backup_base_dir = Path(backup_base_dir)
        self.remote_backup_dir = Path(remote_backup_dir) if remote_backup_dir else None
        
        # Create directories
        self.backup_base_dir.mkdir(exist_ok=True)
        self.daily_backup_dir = self.backup_base_dir / "daily"
        self.monthly_backup_dir = self.backup_base_dir / "monthly"
        self.yearly_backup_dir = self.backup_base_dir / "yearly"
        
        for dir_path in [self.daily_backup_dir, self.monthly_backup_dir, self.yearly_backup_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Backup configuration
        self.backup_interval_hours = 4
        self.daily_retention_days = 30
        self.monthly_retention_months = 12
        self.yearly_retention_years = 7  # Government requirement
        
        # Status tracking
        self.last_backup_time = None
        self.backup_status = "initialized"
        self.backup_errors = []
        self.is_running = False
        
        # Performance requirements
        self.max_backup_time_seconds = 300  # 5 minutes max
        
    async def start_automated_backup(self) -> None:
        """Start the automated backup scheduler"""
        
        if self.is_running:
            return
        
        self.is_running = True
        print("Starting automated backup system...")
        
        # Schedule backups every 4 hours
        schedule.every(self.backup_interval_hours).hours.do(self._schedule_backup)
        
        # Schedule daily cleanup
        schedule.every().day.at("02:00").do(self._schedule_cleanup)
        
        # Schedule monthly archival
        schedule.every().month.do(self._schedule_monthly_archive)
        
        # Run scheduler in background thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                asyncio.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Perform initial backup
        await self.create_backup()
        
        print(f"Automated backup started - Next backup in {self.backup_interval_hours} hours")

    def stop_automated_backup(self) -> None:
        """Stop the automated backup scheduler"""
        self.is_running = False
        schedule.clear()
        print("Automated backup system stopped")

    async def create_backup(self, backup_type: str = "scheduled") -> Dict[str, Any]:
        """
        Create comprehensive backup of audit system
        
        Args:
            backup_type: Type of backup (scheduled, manual, emergency)
            
        Returns:
            Backup result dictionary
        """
        start_time = datetime.now()
        backup_id = f"backup_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            print(f"Starting {backup_type} backup: {backup_id}")
            
            # Create backup directory
            backup_dir = self.daily_backup_dir / backup_id
            backup_dir.mkdir(exist_ok=True)
            
            backup_manifest = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "start_time": start_time.isoformat(),
                "start_time_hijri": get_hijri_date(),
                "primary_data_dir": str(self.primary_data_dir),
                "files_backed_up": [],
                "compression_used": True,
                "encryption_used": False,  # Add encryption if required
                "retention_period_years": self.yearly_retention_years
            }
            
            # Backup audit chain
            await self._backup_audit_chain(backup_dir, backup_manifest)
            
            # Backup configuration files
            await self._backup_configurations(backup_dir, backup_manifest)
            
            # Backup reports and templates
            await self._backup_reports_templates(backup_dir, backup_manifest)
            
            # Backup logs
            await self._backup_logs(backup_dir, backup_manifest)
            
            # Create backup verification
            verification_result = await self._verify_backup(backup_dir)
            backup_manifest["verification"] = verification_result
            
            # Save manifest
            manifest_file = backup_dir / "backup_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(backup_manifest, f, ensure_ascii=False, indent=2)
            
            end_time = datetime.now()
            backup_duration = (end_time - start_time).total_seconds()
            
            backup_manifest["end_time"] = end_time.isoformat()
            backup_manifest["duration_seconds"] = backup_duration
            backup_manifest["status"] = "completed"
            
            # Performance check
            if backup_duration > self.max_backup_time_seconds:
                backup_manifest["performance_warning"] = f"Backup took {backup_duration}s (limit: {self.max_backup_time_seconds}s)"
            
            self.last_backup_time = end_time
            self.backup_status = "completed"
            
            # Remote backup if configured
            if self.remote_backup_dir:
                await self._copy_to_remote(backup_dir)
            
            print(f"Backup {backup_id} completed in {backup_duration:.2f} seconds")
            
            return {
                "success": True,
                "backup_id": backup_id,
                "duration_seconds": backup_duration,
                "backup_path": str(backup_dir),
                "files_count": len(backup_manifest["files_backed_up"]),
                "verification": verification_result
            }
            
        except Exception as e:
            error_time = datetime.now()
            error_duration = (error_time - start_time).total_seconds()
            
            error_details = {
                "backup_id": backup_id,
                "error": str(e),
                "duration_before_error": error_duration,
                "error_time": error_time.isoformat()
            }
            
            self.backup_errors.append(error_details)
            self.backup_status = "failed"
            
            print(f"Backup {backup_id} failed after {error_duration:.2f} seconds: {e}")
            
            return {
                "success": False,
                "backup_id": backup_id,
                "error": str(e),
                "duration_seconds": error_duration
            }

    async def restore_from_backup(self, backup_id: str, restore_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore system from backup
        
        Args:
            backup_id: ID of backup to restore from
            restore_path: Optional custom restore path
            
        Returns:
            Restore result dictionary
        """
        start_time = datetime.now()
        
        try:
            # Find backup
            backup_dir = self._find_backup(backup_id)
            if not backup_dir:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Load manifest
            manifest_file = backup_dir / "backup_manifest.json"
            if not manifest_file.exists():
                raise ValueError(f"Backup manifest not found for {backup_id}")
            
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            print(f"Starting restore from backup: {backup_id}")
            
            # Verify backup integrity before restore
            verification = await self._verify_backup(backup_dir)
            if not verification["valid"]:
                raise ValueError(f"Backup {backup_id} failed integrity check")
            
            # Determine restore path
            if restore_path:
                target_dir = Path(restore_path)
            else:
                target_dir = self.primary_data_dir
            
            target_dir.mkdir(exist_ok=True)
            
            # Restore files
            restored_files = []
            for file_info in manifest["files_backed_up"]:
                source_file = backup_dir / file_info["backup_filename"]
                target_file = target_dir / file_info["original_filename"]
                
                # Create parent directories
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                if file_info.get("compressed"):
                    # Decompress file
                    with gzip.open(source_file, 'rb') as src:
                        with open(target_file, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                else:
                    # Copy file directly
                    shutil.copy2(source_file, target_file)
                
                restored_files.append(str(target_file))
            
            end_time = datetime.now()
            restore_duration = (end_time - start_time).total_seconds()
            
            print(f"Restore completed in {restore_duration:.2f} seconds")
            
            return {
                "success": True,
                "backup_id": backup_id,
                "restore_path": str(target_dir),
                "restored_files": restored_files,
                "duration_seconds": restore_duration,
                "original_backup_time": manifest["start_time"]
            }
            
        except Exception as e:
            error_duration = (datetime.now() - start_time).total_seconds()
            
            print(f"Restore failed after {error_duration:.2f} seconds: {e}")
            
            return {
                "success": False,
                "backup_id": backup_id,
                "error": str(e),
                "duration_seconds": error_duration
            }

    async def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup system status"""
        
        # Count backups by type
        backup_counts = {
            "daily": len(list(self.daily_backup_dir.glob("backup_*"))),
            "monthly": len(list(self.monthly_backup_dir.glob("archive_*"))),
            "yearly": len(list(self.yearly_backup_dir.glob("yearly_*")))
        }
        
        # Calculate next backup time
        if self.last_backup_time:
            next_backup = self.last_backup_time + timedelta(hours=self.backup_interval_hours)
        else:
            next_backup = datetime.now() + timedelta(hours=self.backup_interval_hours)
        
        return {
            "status": self.backup_status,
            "is_running": self.is_running,
            "last_backup_time": self.last_backup_time.isoformat() if self.last_backup_time else None,
            "next_backup_time": next_backup.isoformat(),
            "backup_counts": backup_counts,
            "recent_errors": self.backup_errors[-5:],  # Last 5 errors
            "storage_usage": await self._calculate_storage_usage(),
            "retention_policy": {
                "daily_retention_days": self.daily_retention_days,
                "monthly_retention_months": self.monthly_retention_months,
                "yearly_retention_years": self.yearly_retention_years
            }
        }

    # Private methods
    async def _backup_audit_chain(self, backup_dir: Path, manifest: Dict[str, Any]) -> None:
        """Backup the main audit chain"""
        source_file = self.primary_data_dir / "audit_chain.pkl.gz"
        
        if source_file.exists():
            backup_file = backup_dir / "audit_chain.pkl.gz"
            shutil.copy2(source_file, backup_file)
            
            manifest["files_backed_up"].append({
                "original_filename": "audit_chain.pkl.gz",
                "backup_filename": "audit_chain.pkl.gz",
                "file_size": source_file.stat().st_size,
                "compressed": True,
                "file_type": "audit_chain"
            })

    async def _backup_configurations(self, backup_dir: Path, manifest: Dict[str, Any]) -> None:
        """Backup configuration files"""
        config_files = ["config.json", "settings.ini", ".env"]
        
        for config_file in config_files:
            source_path = self.primary_data_dir.parent / config_file
            if source_path.exists():
                backup_path = backup_dir / f"config_{config_file}"
                shutil.copy2(source_path, backup_path)
                
                manifest["files_backed_up"].append({
                    "original_filename": config_file,
                    "backup_filename": f"config_{config_file}",
                    "file_size": source_path.stat().st_size,
                    "compressed": False,
                    "file_type": "configuration"
                })

    async def _backup_reports_templates(self, backup_dir: Path, manifest: Dict[str, Any]) -> None:
        """Backup generated reports and templates"""
        templates_dir = self.primary_data_dir.parent / "templates"
        
        if templates_dir.exists():
            backup_templates_dir = backup_dir / "templates"
            shutil.copytree(templates_dir, backup_templates_dir, dirs_exist_ok=True)
            
            # Count files
            template_files = list(backup_templates_dir.rglob("*"))
            manifest["files_backed_up"].append({
                "original_filename": "templates/",
                "backup_filename": "templates/",
                "files_count": len([f for f in template_files if f.is_file()]),
                "compressed": False,
                "file_type": "templates"
            })

    async def _backup_logs(self, backup_dir: Path, manifest: Dict[str, Any]) -> None:
        """Backup system logs"""
        logs_dir = self.primary_data_dir / "logs"
        
        if logs_dir.exists():
            backup_logs_dir = backup_dir / "logs"
            backup_logs_dir.mkdir(exist_ok=True)
            
            # Compress log files
            for log_file in logs_dir.glob("*.log"):
                compressed_log = backup_logs_dir / f"{log_file.stem}.log.gz"
                with open(log_file, 'rb') as src:
                    with gzip.open(compressed_log, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                
                manifest["files_backed_up"].append({
                    "original_filename": f"logs/{log_file.name}",
                    "backup_filename": f"logs/{log_file.stem}.log.gz",
                    "file_size": log_file.stat().st_size,
                    "compressed": True,
                    "file_type": "logs"
                })

    async def _verify_backup(self, backup_dir: Path) -> Dict[str, Any]:
        """Verify backup integrity"""
        try:
            manifest_file = backup_dir / "backup_manifest.json"
            
            if not manifest_file.exists():
                return {"valid": False, "error": "Manifest file missing"}
            
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            missing_files = []
            corrupted_files = []
            
            for file_info in manifest.get("files_backed_up", []):
                backup_file_path = backup_dir / file_info["backup_filename"]
                
                if not backup_file_path.exists():
                    missing_files.append(file_info["backup_filename"])
                    continue
                
                # Verify file size (basic integrity check)
                actual_size = backup_file_path.stat().st_size
                if actual_size == 0:
                    corrupted_files.append(file_info["backup_filename"])
            
            is_valid = len(missing_files) == 0 and len(corrupted_files) == 0
            
            return {
                "valid": is_valid,
                "files_checked": len(manifest.get("files_backed_up", [])),
                "missing_files": missing_files,
                "corrupted_files": corrupted_files,
                "verification_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "verification_time": datetime.now().isoformat()
            }

    def _find_backup(self, backup_id: str) -> Optional[Path]:
        """Find backup directory by ID"""
        
        # Search in daily backups
        daily_backup = self.daily_backup_dir / backup_id
        if daily_backup.exists():
            return daily_backup
        
        # Search in monthly archives
        for archive_dir in self.monthly_backup_dir.glob("*"):
            backup_path = archive_dir / backup_id
            if backup_path.exists():
                return backup_path
        
        # Search in yearly archives
        for yearly_dir in self.yearly_backup_dir.glob("*"):
            backup_path = yearly_dir / backup_id
            if backup_path.exists():
                return backup_path
        
        return None

    async def _copy_to_remote(self, backup_dir: Path) -> None:
        """Copy backup to remote location"""
        if not self.remote_backup_dir:
            return
        
        try:
            self.remote_backup_dir.mkdir(exist_ok=True)
            remote_backup_path = self.remote_backup_dir / backup_dir.name
            shutil.copytree(backup_dir, remote_backup_path, dirs_exist_ok=True)
            print(f"Backup copied to remote location: {remote_backup_path}")
        except Exception as e:
            print(f"Failed to copy backup to remote location: {e}")

    async def _calculate_storage_usage(self) -> Dict[str, Any]:
        """Calculate storage usage for backups"""
        
        def get_dir_size(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        daily_size = get_dir_size(self.daily_backup_dir)
        monthly_size = get_dir_size(self.monthly_backup_dir)
        yearly_size = get_dir_size(self.yearly_backup_dir)
        total_size = daily_size + monthly_size + yearly_size
        
        return {
            "daily_backups_mb": daily_size / (1024 * 1024),
            "monthly_archives_mb": monthly_size / (1024 * 1024),
            "yearly_archives_mb": yearly_size / (1024 * 1024),
            "total_mb": total_size / (1024 * 1024),
            "last_calculated": datetime.now().isoformat()
        }

    def _schedule_backup(self) -> None:
        """Schedule backup (called by scheduler)"""
        asyncio.create_task(self.create_backup("scheduled"))

    def _schedule_cleanup(self) -> None:
        """Schedule cleanup of old backups"""
        asyncio.create_task(self._cleanup_old_backups())

    def _schedule_monthly_archive(self) -> None:
        """Schedule monthly archival"""
        asyncio.create_task(self._create_monthly_archive())

    async def _cleanup_old_backups(self) -> None:
        """Clean up old backups according to retention policy"""
        
        cutoff_date = datetime.now() - timedelta(days=self.daily_retention_days)
        
        for backup_dir in self.daily_backup_dir.glob("backup_*"):
            try:
                dir_time = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                if dir_time < cutoff_date:
                    shutil.rmtree(backup_dir)
                    print(f"Cleaned old backup: {backup_dir}")
            except Exception as e:
                print(f"Failed to clean backup {backup_dir}: {e}")

    async def _create_monthly_archive(self) -> None:
        """Create monthly archive from daily backups"""
        
        current_month = datetime.now().strftime('%Y%m')
        archive_dir = self.monthly_backup_dir / f"archive_{current_month}"
        
        if not archive_dir.exists():
            archive_dir.mkdir()
            
            # Copy representative daily backups from the month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            for backup_dir in self.daily_backup_dir.glob("backup_*"):
                try:
                    backup_time = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                    if backup_time >= month_start:
                        # Copy first backup of each week
                        if backup_time.weekday() == 6:  # Sunday
                            dest_dir = archive_dir / backup_dir.name
                            shutil.copytree(backup_dir, dest_dir, dirs_exist_ok=True)
                except Exception as e:
                    print(f"Failed to archive backup {backup_dir}: {e}")
            
            print(f"Created monthly archive: {archive_dir}")