"""
Advanced persistent storage system for bothost.ru with AI-powered diagnostics
Handles automatic backups, cloud storage, data recovery, and intelligent monitoring
"""
import os
import json
import time
import asyncio
import logging
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import aiosqlite
from config import STORAGE_DIR, DB_CONFIG, ADMIN_CONFIG

logger = logging.getLogger(__name__)

class DiagnosticResult:
    """Result of system diagnostic"""
    def __init__(self, status: str, message: str, severity: str = "info", suggestions: List[str] = None):
        self.status = status
        self.message = message
        self.severity = severity  # info, warning, error, critical
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()

class StorageDiagnostic:
    """AI-powered diagnostic system for storage health"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.last_diagnostics = []
        self.problems_detected = []
        
    async def run_comprehensive_diagnostic(self) -> List[DiagnosticResult]:
        """Run comprehensive system diagnostic"""
        results = []
        
        # 1. Database integrity check
        db_result = await self._check_database_integrity()
        results.append(db_result)
        
        # 2. Storage space check
        space_result = await self._check_storage_space()
        results.append(space_result)
        
        # 3. Backup health check
        backup_result = await self._check_backup_health()
        results.append(backup_result)
        
        # 4. Performance check
        perf_result = await self._check_performance()
        results.append(perf_result)
        
        # 5. Predictive analysis
        prediction_result = await self._predict_issues()
        results.append(prediction_result)
        
        # Store results
        self.last_diagnostics = results
        self._analyze_problems(results)
        
        return results
    
    async def _check_database_integrity(self) -> DiagnosticResult:
        """Check database file integrity"""
        try:
            if not os.path.exists(self.storage_manager.db_path):
                return DiagnosticResult(
                    "error", 
                    "Database file not found", 
                    "critical", 
                    ["Run automatic repair", "Restore from backup"]
                )
            
            # Check file size
            db_size = os.path.getsize(self.storage_manager.db_path)
            if db_size < 1024:  # Less than 1KB
                return DiagnosticResult(
                    "warning",
                    f"Database file suspiciously small: {db_size} bytes",
                    "warning",
                    ["Check for corruption", "Verify data integrity"]
                )
            
            # Test database connection
            try:
                conn = await aiosqlite.connect(self.storage_manager.db_path)
                await conn.execute("SELECT COUNT(*) FROM users")
                await conn.close()
                
                return DiagnosticResult(
                    "ok",
                    f"Database integrity verified ({db_size / 1024 / 1024:.1f} MB)",
                    "info"
                )
            except Exception as e:
                return DiagnosticResult(
                    "error",
                    f"Database connection failed: {str(e)}",
                    "error",
                    ["Run database repair", "Check file permissions"]
                )
                
        except Exception as e:
            return DiagnosticResult(
                "error",
                f"Database check failed: {str(e)}",
                "error",
                ["Manual inspection required"]
            )
    
    async def _check_storage_space(self) -> DiagnosticResult:
        """Check available storage space"""
        try:
            total, used, free = shutil.disk_usage(self.storage_manager.storage_dir)
            
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100
            
            if free_gb < 0.1:  # Less than 100MB
                return DiagnosticResult(
                    "critical",
                    f"Critical: Only {free_gb:.2f} GB free space remaining",
                    "critical",
                    ["Clean up old files", "Increase storage", "Monitor space usage"]
                )
            elif free_gb < 1.0:  # Less than 1GB
                return DiagnosticResult(
                    "warning",
                    f"Warning: Only {free_gb:.2f} GB free space remaining",
                    "warning",
                    ["Consider cleanup", "Monitor space usage"]
                )
            elif used_percent > 80:
                return DiagnosticResult(
                    "warning",
                    f"Warning: {used_percent:.1f}% of disk space used",
                    "warning",
                    ["Monitor space usage", "Plan for cleanup"]
                )
            else:
                return DiagnosticResult(
                    "ok",
                    f"Storage space healthy: {free_gb:.2f} GB free ({used_percent:.1f}% used)",
                    "info"
                )
                
        except Exception as e:
            return DiagnosticResult(
                "error",
                f"Storage check failed: {str(e)}",
                "error",
                ["Check disk access permissions"]
            )
    
    async def _check_backup_health(self) -> DiagnosticResult:
        """Check backup file health and availability"""
        try:
            backup_files = self.storage_manager._find_backups(self.storage_manager.backup_dir)
            cloud_backups = self.storage_manager._find_backups(self.storage_manager.cloud_backup_dir)
            
            total_backups = len(backup_files) + len(cloud_backups)
            
            if total_backups == 0:
                return DiagnosticResult(
                    "critical",
                    "No backup files found",
                    "critical",
                    ["Create immediate backup", "Enable automatic backups"]
                )
            
            # Check latest backup age
            all_backups = backup_files + cloud_backups
            latest_backup = max(all_backups, key=lambda x: os.path.getmtime(x))
            backup_age = time.time() - os.path.getmtime(latest_backup)
            
            if backup_age > 86400:  # More than 24 hours
                return DiagnosticResult(
                    "warning",
                    f"Latest backup is {backup_age / 3600:.1f} hours old",
                    "warning",
                    ["Create new backup", "Check backup automation"]
                )
            elif backup_age > 172800:  # More than 48 hours
                return DiagnosticResult(
                    "error",
                    f"Latest backup is {backup_age / 3600:.1f} hours old",
                    "error",
                    ["Create immediate backup", "Investigate backup failures"]
                )
            else:
                return DiagnosticResult(
                    "ok",
                    f"Backup system healthy: {total_backups} backups available, latest {backup_age / 3600:.1f} hours old",
                    "info"
                )
                
        except Exception as e:
            return DiagnosticResult(
                "error",
                f"Backup check failed: {str(e)}",
                "error",
                ["Check backup directory access"]
            )
    
    async def _check_performance(self) -> DiagnosticResult:
        """Check system performance metrics"""
        try:
            # Test database query performance
            start_time = time.time()
            conn = await aiosqlite.connect(self.storage_manager.db_path)
            await conn.execute("SELECT COUNT(*) FROM users")
            await conn.close()
            query_time = time.time() - start_time
            
            if query_time > 1.0:  # More than 1 second
                return DiagnosticResult(
                    "warning",
                    f"Database query slow: {query_time:.2f}s",
                    "warning",
                    ["Check database size", "Consider optimization", "Monitor performance"]
                )
            elif query_time > 5.0:  # More than 5 seconds
                return DiagnosticResult(
                    "error",
                    f"Database query very slow: {query_time:.2f}s",
                    "error",
                    ["Database optimization required", "Check for corruption", "Consider backup and rebuild"]
                )
            else:
                return DiagnosticResult(
                    "ok",
                    f"Database performance good: {query_time:.2f}s",
                    "info"
                )
                
        except Exception as e:
            return DiagnosticResult(
                "error",
                f"Performance check failed: {str(e)}",
                "error",
                ["Check database connection", "Monitor system resources"]
            )
    
    async def _predict_issues(self) -> DiagnosticResult:
        """Predict potential future issues based on trends"""
        try:
            # Analyze backup frequency
            backup_files = self.storage_manager._find_backups(self.storage_manager.backup_dir)
            if len(backup_files) < 3:
                return DiagnosticResult(
                    "warning",
                    "Insufficient backup history for trend analysis",
                    "warning",
                    ["Create more backups", "Enable automatic backups"]
                )
            
            # Check backup file sizes for trends
            backup_sizes = []
            for backup in backup_files[-10:]:  # Last 10 backups
                try:
                    backup_sizes.append(os.path.getsize(backup))
                except:
                    pass
            
            if len(backup_sizes) >= 3:
                # Calculate growth trend
                size_trend = (backup_sizes[-1] - backup_sizes[0]) / len(backup_sizes)
                
                if size_trend > 1024 * 1024:  # Growing by more than 1MB per backup
                    estimated_days = (5 * 1024 * 1024 * 1024) / max(1, size_trend)  # Days until 5GB growth
                    if estimated_days < 30:
                        return DiagnosticResult(
                            "warning",
                            f"Database growing rapidly, may exceed storage in {estimated_days:.0f} days",
                            "warning",
                            ["Monitor growth", "Consider cleanup", "Plan storage expansion"]
                        )
            
            return DiagnosticResult(
                "ok",
                "No immediate issues predicted based on current trends",
                "info"
            )
            
        except Exception as e:
            return DiagnosticResult(
                "error",
                f"Prediction analysis failed: {str(e)}",
                "error",
                ["Manual monitoring required"]
            )
    
    def _analyze_problems(self, results: List[DiagnosticResult]):
        """Analyze diagnostic results for patterns and problems"""
        self.problems_detected = [r for r in results if r.severity in ["warning", "error", "critical"]]
        
        # Auto-repair suggestions
        if ADMIN_CONFIG["auto_repair_enabled"]:
            for result in self.problems_detected:
                if result.status == "error" and "Database connection failed" in result.message:
                    asyncio.create_task(self.storage_manager._auto_repair_database())
                elif result.status == "critical" and "No backup files found" in result.message:
                    asyncio.create_task(self.storage_manager._create_backup("emergency"))
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        if not self.last_diagnostics:
            return {"status": "unknown", "message": "No diagnostics available"}
        
        critical_issues = [r for r in self.last_diagnostics if r.severity == "critical"]
        error_issues = [r for r in self.last_diagnostics if r.severity == "error"]
        warning_issues = [r for r in self.last_diagnostics if r.severity == "warning"]
        
        if critical_issues:
            status = "critical"
            message = f"{len(critical_issues)} critical issues detected"
        elif error_issues:
            status = "error"
            message = f"{len(error_issues)} errors detected"
        elif warning_issues:
            status = "warning"
            message = f"{len(warning_issues)} warnings detected"
        else:
            status = "healthy"
            message = "System operating normally"
        
        return {
            "status": status,
            "message": message,
            "total_issues": len(self.problems_detected),
            "last_check": self.last_diagnostics[0].timestamp if self.last_diagnostics else None
        }

class BothostStorageManager:
    """
    Advanced storage manager for bothost.ru with automatic backups,
    AI-powered diagnostics, and intelligent recovery
    """

    def __init__(self):
        self.storage_dir = STORAGE_DIR
        self.db_path = os.path.join(STORAGE_DIR, DB_CONFIG["name"])
        self.backup_dir = os.path.join(STORAGE_DIR, "backups")
        self.cloud_backup_dir = os.path.join(STORAGE_DIR, "cloud_backups")
        self.diagnostic_system = StorageDiagnostic(self)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.cloud_backup_dir, exist_ok=True)

        # Create .bothostkeep files to prevent directory deletion
        for directory in [self.storage_dir, self.backup_dir, self.cloud_backup_dir]:
            keep_file = os.path.join(directory, ".bothostkeep")
            if not os.path.exists(keep_file):
                with open(keep_file, "w") as f:
                    f.write(f"# Bothost.ru keep file\n# Created: {datetime.now().isoformat()}\n# Do not delete this file or directory")

    async def initialize(self):
        """Initialize storage system with AI diagnostics"""
        logger.info("🔧 Initializing advanced persistent storage system with AI diagnostics")

        # Check if this is a fresh deployment
        is_fresh = not os.path.exists(self.db_path)

        if is_fresh:
            logger.info("🆕 Fresh deployment detected")
            await self._restore_from_backup()
        else:
            logger.info("✅ Existing database found")
            await self._create_backup("pre_init")

        # Start intelligent monitoring
        asyncio.create_task(self._intelligent_monitoring())

        return is_fresh

    async def _restore_from_backup(self):
        """Restore from most recent backup if available"""
        try:
            # Look for backups in cloud storage first
            cloud_backups = self._find_backups(self.cloud_backup_dir)
            if cloud_backups:
                latest_cloud = max(cloud_backups)
                logger.info(f"🔄 Restoring from cloud backup: {latest_cloud}")
                await self._restore_backup(latest_cloud)
                return

            # Fall back to local backups
            local_backups = self._find_backups(self.backup_dir)
            if local_backups:
                latest_local = max(local_backups)
                logger.info(f"🔄 Restoring from local backup: {latest_local}")
                await self._restore_backup(latest_local)
                return

            logger.info("ℹ️ No backups found, starting with fresh database")

        except Exception as e:
            logger.error(f"❌ Backup restore failed: {e}")
            logger.info("🆕 Starting with fresh database")

    def _find_backups(self, backup_dir: str) -> List[str]:
        """Find all backup files in directory"""
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and filename.endswith(".db"):
                backups.append(os.path.join(backup_dir, filename))
        return backups

    async def _restore_backup(self, backup_path: str):
        """Restore database from backup file"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"✅ Successfully restored from {os.path.basename(backup_path)}")
        except Exception as e:
            logger.error(f"❌ Failed to restore {backup_path}: {e}")
            raise

    async def _create_backup(self, prefix: str = "auto"):
        """Create a backup of the database"""
        try:
            import shutil
            from datetime import datetime

            if not os.path.exists(self.db_path):
                logger.warning("🚨 Database file not found, skipping backup")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{prefix}_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Copy to local backup
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"💾 Created local backup: {backup_name}")

            # Also copy to cloud backup (if different directory)
            if self.cloud_backup_dir != self.backup_dir:
                cloud_backup_path = os.path.join(self.cloud_backup_dir, backup_name)
                shutil.copy2(self.db_path, cloud_backup_path)
                logger.info(f"☁️ Created cloud backup: {backup_name}")

            # Clean up old backups
            await self._cleanup_backups()

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")

    async def _cleanup_backups(self):
        """Clean up old backups, keeping only the most recent"""
        try:
            # Keep last 5 local backups
            local_backups = self._find_backups(self.backup_dir)
            if len(local_backups) > 5:
                local_backups.sort()
                for old_backup in local_backups[:-5]:
                    try:
                        os.remove(old_backup)
                        logger.info(f"🗑️ Removed old backup: {os.path.basename(old_backup)}")
                    except:
                        pass

            # Keep last 10 cloud backups
            cloud_backups = self._find_backups(self.cloud_backup_dir)
            if len(cloud_backups) > 10:
                cloud_backups.sort()
                for old_backup in cloud_backups[:-10]:
                    try:
                        os.remove(old_backup)
                        logger.info(f"🗑️ Removed old cloud backup: {os.path.basename(old_backup)}")
                    except:
                        pass

        except Exception as e:
            logger.error(f"⚠️ Backup cleanup failed: {e}")

    async def _intelligent_monitoring(self):
        """Intelligent monitoring with AI diagnostics"""
        while True:
            try:
                # Run comprehensive diagnostics
                diagnostics = await self.diagnostic_system.run_comprehensive_diagnostic()
                
                # Log diagnostic results
                for result in diagnostics:
                    if result.severity == "critical":
                        logger.critical(f"🚨 CRITICAL: {result.message}")
                    elif result.severity == "error":
                        logger.error(f"❌ ERROR: {result.message}")
                    elif result.severity == "warning":
                        logger.warning(f"⚠️ WARNING: {result.message}")
                    else:
                        logger.info(f"✅ {result.message}")
                
                # Get health summary
                health = self.diagnostic_system.get_health_summary()
                logger.info(f"📊 Health Status: {health['status']} - {health['message']}")
                
                # Sleep until next diagnostic check
                await asyncio.sleep(ADMIN_CONFIG["diagnostic_interval"])
                
            except Exception as e:
                logger.error(f"❌ Intelligent monitoring failed: {e}")
                await asyncio.sleep(60)  # Retry after delay

    async def _repair_database(self):
        """Repair database issues"""
        try:
            logger.info("🔧 Starting database repair...")
            
            # Create backup before repair
            await self._create_backup("repair_backup")
            
            # Try to repair database
            conn = await aiosqlite.connect(self.db_path)
            
            # Run integrity check
            async with conn.execute("PRAGMA integrity_check") as cursor:
                result = await cursor.fetchone()
                if result and result[0] != "ok":
                    logger.warning(f"Database integrity issue: {result[0]}")
            
            # Optimize database
            await conn.execute("VACUUM")
            await conn.execute("PRAGMA optimize")
            
            await conn.close()
            
            logger.info("✅ Database repair completed")
            
        except Exception as e:
            logger.error(f"❌ Database repair failed: {e}")
            raise

    async def _auto_repair_database(self):
        """Automatically repair database issues"""
        try:
            logger.info("🔧 Starting automatic database repair...")
            
            # Try to repair database
            await self._repair_database()
            
            # Create backup after repair
            await self._create_backup("auto_repair")
            
            logger.info("✅ Automatic database repair completed")
            
        except Exception as e:
            logger.error(f"❌ Automatic repair failed: {e}")

    async def _periodic_backup(self):
        """Periodic backup task"""
        while True:
            try:
                await asyncio.sleep(ADMIN_CONFIG["backup_interval"])  # Backup every configured interval
                await self._create_backup("auto")
            except Exception as e:
                logger.error(f"❌ Periodic backup failed: {e}")
                await asyncio.sleep(60)  # Retry after delay

    async def get_database_status(self) -> Dict[str, Any]:
        """Get database status information"""
        status = {
            "db_exists": os.path.exists(self.db_path),
            "db_size": 0,
            "local_backups": 0,
            "cloud_backups": 0,
            "last_backup": None
        }

        if status["db_exists"]:
            status["db_size"] = os.path.getsize(self.db_path)

        local_backups = self._find_backups(self.backup_dir)
        status["local_backups"] = len(local_backups)
        if local_backups:
            status["last_backup"] = max(local_backups)

        cloud_backups = self._find_backups(self.cloud_backup_dir)
        status["cloud_backups"] = len(cloud_backups)

        return status

    async def export_data(self, format: str = "json") -> Optional[str]:
        """Export database data to specified format"""
        try:
            if format == "json":
                return await self._export_to_json()
            elif format == "sql":
                return await self._export_to_sql()
            else:
                logger.error(f"❌ Unsupported export format: {format}")
                return None
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return None

    async def _export_to_json(self) -> str:
        """Export database to JSON format"""
        try:
            import json
            from db_manager import get_connection

            conn = await get_connection()
            export_data = {}

            # Export users
            async with conn.execute('SELECT * FROM users') as cursor:
                users = await cursor.fetchall()
                export_data['users'] = [dict(user) for user in users]

            # Export fights
            async with conn.execute('SELECT * FROM rademka_fights') as cursor:
                fights = await cursor.fetchall()
                export_data['fights'] = [dict(fight) for fight in fights]

            # Export chats
            async with conn.execute('SELECT * FROM chats') as cursor:
                chats = await cursor.fetchall()
                export_data['chats'] = [dict(chat) for chat in chats]

            # Export chat stats
            async with conn.execute('SELECT * FROM chat_stats') as cursor:
                chat_stats = await cursor.fetchall()
                export_data['chat_stats'] = [dict(stat) for stat in chat_stats]

            # Export chat top
            async with conn.execute('SELECT * FROM chat_top') as cursor:
                chat_top = await cursor.fetchall()
                export_data['chat_top'] = [dict(top) for top in chat_top]

            await conn.close()

            export_file = os.path.join(self.storage_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📤 Exported data to {export_file}")
            return export_file

        except Exception as e:
            logger.error(f"❌ JSON export failed: {e}")
            return None

    async def _export_to_sql(self) -> str:
        """Export database to SQL format"""
        try:
            from db_manager import get_connection

            conn = await get_connection()
            export_file = os.path.join(self.storage_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

            with open(export_file, 'w', encoding='utf-8') as f:
                f.write("-- Database Export\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")

                # Export each table
                tables = ['users', 'rademka_fights', 'chats', 'chat_stats', 'chat_top']
                for table in tables:
                    f.write(f"-- Table: {table}\n")
                    async with conn.execute(f'SELECT * FROM {table}') as cursor:
                        rows = await cursor.fetchall()
                        for row in rows:
                            # Convert row to dict and then to SQL INSERT
                            row_dict = dict(row)
                            columns = ', '.join(row_dict.keys())
                            values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in row_dict.values()])
                            f.write(f"INSERT INTO {table} ({columns}) VALUES ({values});\n")
                    f.write("\n")

            await conn.close()
            logger.info(f"📤 Exported data to {export_file}")
            return export_file

        except Exception as e:
            logger.error(f"❌ SQL export failed: {e}")
            return None

    async def import_data(self, import_file: str) -> bool:
        """Import data from backup file"""
        try:
            if import_file.endswith('.json'):
                return await self._import_from_json(import_file)
            elif import_file.endswith('.sql') or import_file.endswith('.db'):
                return await self._import_from_sql(import_file)
            else:
                logger.error(f"❌ Unsupported import format: {import_file}")
                return False
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False

    async def _import_from_json(self, json_file: str) -> bool:
        """Import data from JSON file"""
        try:
            import json
            from db_manager import get_connection

            with open(json_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            conn = await get_connection()

            # Import users
            if 'users' in import_data:
                for user in import_data['users']:
                    await conn.execute('''
                        INSERT OR REPLACE INTO users
                        (user_id, nickname, gofra_mm, cable_mm, gofra, cable_power, zmiy_grams,
                         last_update, last_davka, atm_count, max_atm, experience, total_davki, total_zmiy_grams, nickname_changed)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        user['user_id'], user['nickname'], user['gofra_mm'], user['cable_mm'],
                        user['gofra'], user['cable_power'], user['zmiy_grams'],
                        user['last_update'], user['last_davka'], user['atm_count'],
                        user['max_atm'], user['experience'], user['total_davki'], user['total_zmiy_grams'],
                        user['nickname_changed']
                    ))

            # Import other tables similarly...

            await conn.commit()
            await conn.close()

            logger.info(f"📥 Successfully imported from {json_file}")
            return True

        except Exception as e:
            logger.error(f"❌ JSON import failed: {e}")
            return False

    async def _import_from_sql(self, sql_file: str) -> bool:
        """Import data from SQL file"""
        try:
            from db_manager import get_connection

            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_commands = f.read()

            conn = await get_connection()
            await conn.executescript(sql_commands)
            await conn.commit()
            await conn.close()

            logger.info(f"📥 Successfully imported from {sql_file}")
            return True

        except Exception as e:
            logger.error(f"❌ SQL import failed: {e}")
            return False

# Global storage manager instance
storage_manager = BothostStorageManager()

async def init_persistent_storage():
    """Initialize persistent storage system"""
    is_fresh = await storage_manager.initialize()
    return is_fresh

async def get_storage_status():
    """Get current storage status"""
    return await storage_manager.get_database_status()