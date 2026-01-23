"""
Improved persistent storage system for bothost.ru
Handles automatic backups, cloud storage, and data recovery
"""
import os
import json
import time
import asyncio
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import aiosqlite
from config import STORAGE_DIR, DB_CONFIG

logger = logging.getLogger(__name__)

class BothostStorageManager:
    """
    Advanced storage manager for bothost.ru with automatic backups
    and data persistence across deployments
    """

    def __init__(self):
        self.storage_dir = STORAGE_DIR
        self.db_path = os.path.join(STORAGE_DIR, DB_CONFIG["name"])
        self.backup_dir = os.path.join(STORAGE_DIR, "backups")
        self.cloud_backup_dir = os.path.join(STORAGE_DIR, "cloud_backups")
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
        """Initialize storage system"""
        logger.info("🔧 Initializing persistent storage system")

        # Check if this is a fresh deployment
        is_fresh = not os.path.exists(self.db_path)

        if is_fresh:
            logger.info("🆕 Fresh deployment detected")
            await self._restore_from_backup()
        else:
            logger.info("✅ Existing database found")
            await self._create_backup("pre_init")

        # Start periodic backup task
        asyncio.create_task(self._periodic_backup())

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

    async def _periodic_backup(self):
        """Periodic backup task"""
        while True:
            try:
                await asyncio.sleep(3600)  # Backup every hour
                await self._create_backup("hourly")
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