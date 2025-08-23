"""
Bot integration bridge
Handles communication between admin panel and Discord bot
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from app.core.database import db_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class TriggerType(str, Enum):
    """Bot trigger types"""
    CONFIG_RELOAD = "config_reload"
    FAME_REWARDS_UPDATE = "fame_rewards_update"
    TAXI_CONFIG_UPDATE = "taxi_config_update"
    BANKING_CONFIG_UPDATE = "banking_config_update"
    MECHANIC_CONFIG_UPDATE = "mechanic_config_update"
    USER_PERMISSION_UPDATE = "user_permission_update"
    SYSTEM_MAINTENANCE = "system_maintenance"

class BotBridge:
    """Bot integration bridge"""
    
    def __init__(self):
        self.db_path = settings.DATABASE_URL
        self._bot_status: Dict[str, Any] = {}
        
    async def trigger_bot_reload(self, trigger_type: TriggerType, guild_id: str, data: Dict[str, Any] = None) -> bool:
        """
        Trigger bot to reload configuration
        Uses database trigger mechanism for bot to detect changes
        """
        try:
            # Insert trigger record for bot to detect
            trigger_data = {
                "type": trigger_type.value,
                "guild_id": guild_id,
                "data": json.dumps(data or {}),
                "timestamp": datetime.utcnow().isoformat(),
                "processed": False
            }
            
            # Create admin_bot_triggers table if it doesn't exist
            await self._ensure_triggers_table()
            
            # Insert trigger
            insert_query = """
                INSERT INTO admin_bot_triggers 
                (id, trigger_type, guild_id, trigger_data, created_at, processed)
                VALUES (?, ?, ?, ?, ?, 0)
            """
            
            trigger_id = f"{guild_id}_{trigger_type.value}_{int(datetime.utcnow().timestamp())}"
            
            await db_manager.execute_command(
                insert_query,
                (trigger_id, trigger_type.value, guild_id, 
                 json.dumps(data or {}), datetime.utcnow().isoformat())
            )
            
            logger.info(f"Bot trigger created: {trigger_type.value} for guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create bot trigger: {e}")
            return False
    
    async def _ensure_triggers_table(self):
        """Ensure bot triggers table exists"""
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS admin_bot_triggers (
                    id TEXT PRIMARY KEY,
                    trigger_type TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    trigger_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    processed INTEGER DEFAULT 0,
                    processed_at TEXT NULL,
                    error_message TEXT NULL
                )
            """
            
            await db_manager.execute_command(create_table_query)
            
            # Create index for performance
            index_query = """
                CREATE INDEX IF NOT EXISTS idx_bot_triggers_guild_processed 
                ON admin_bot_triggers(guild_id, processed, created_at)
            """
            
            await db_manager.execute_command(index_query)
            
        except Exception as e:
            logger.error(f"Failed to create triggers table: {e}")
    
    async def get_bot_status(self, guild_id: Optional[str] = None) -> Dict[str, Any]:
        """Get bot status and health information"""
        try:
            # Check if bot is responding by checking recent activity
            status_query = """
                SELECT component, status, last_check, response_time_ms, error_message
                FROM admin_system_status
                WHERE component = 'bot'
            """
            
            if guild_id:
                status_query += " AND metadata LIKE ?"
                result = await db_manager.execute_query(status_query, (f'%{guild_id}%',))
            else:
                result = await db_manager.execute_query(status_query)
            
            if result:
                bot_status = result[0]
                return {
                    "status": bot_status['status'],
                    "last_check": bot_status['last_check'],
                    "response_time": bot_status['response_time_ms'],
                    "error": bot_status['error_message'],
                    "healthy": bot_status['status'] == 'online'
                }
            else:
                return {
                    "status": "unknown",
                    "last_check": None,
                    "response_time": None,
                    "error": "No status data available",
                    "healthy": False
                }
                
        except Exception as e:
            logger.error(f"Failed to get bot status: {e}")
            return {
                "status": "error",
                "last_check": None,
                "response_time": None,
                "error": str(e),
                "healthy": False
            }
    
    async def get_guild_bot_config(self, guild_id: str) -> Dict[str, Any]:
        """Get bot configuration for a specific guild"""
        try:
            query = """
                SELECT config_key, config_value, config_type
                FROM admin_bot_config
                WHERE guild_id = ?
            """
            
            result = await db_manager.execute_query(query, (guild_id,))
            
            config = {}
            for row in result:
                key = row['config_key']
                value = row['config_value']
                config_type = row['config_type']
                
                # Parse value based on type
                if config_type == 'json':
                    config[key] = json.loads(value)
                elif config_type == 'integer':
                    config[key] = int(value)
                elif config_type == 'boolean':
                    config[key] = value.lower() == 'true'
                else:
                    config[key] = value
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get guild bot config: {e}")
            return {}
    
    async def update_guild_bot_config(self, guild_id: str, config_key: str, config_value: Any, user_id: str) -> bool:
        """Update bot configuration for a guild"""
        try:
            # Determine config type
            config_type = "string"
            if isinstance(config_value, bool):
                config_type = "boolean"
                config_value = str(config_value).lower()
            elif isinstance(config_value, int):
                config_type = "integer"
                config_value = str(config_value)
            elif isinstance(config_value, (dict, list)):
                config_type = "json"
                config_value = json.dumps(config_value)
            else:
                config_value = str(config_value)
            
            # Upsert configuration
            upsert_query = """
                INSERT OR REPLACE INTO admin_bot_config
                (guild_id, config_key, config_value, config_type, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            await db_manager.execute_command(
                upsert_query,
                (guild_id, config_key, config_value, config_type, user_id)
            )
            
            # Trigger bot reload
            await self.trigger_bot_reload(
                TriggerType.CONFIG_RELOAD,
                guild_id,
                {"config_key": config_key, "config_value": config_value}
            )
            
            logger.info(f"Bot config updated: {config_key} for guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update bot config: {e}")
            return False
    
    async def get_processed_triggers(self, guild_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get processed triggers for monitoring"""
        try:
            query = """
                SELECT * FROM admin_bot_triggers
                WHERE guild_id = ? AND processed = 1
                ORDER BY processed_at DESC
                LIMIT ?
            """
            
            result = await db_manager.execute_query(query, (guild_id, limit))
            
            triggers = []
            for row in result:
                triggers.append({
                    "id": row['id'],
                    "type": row['trigger_type'],
                    "guild_id": row['guild_id'],
                    "data": json.loads(row['trigger_data']),
                    "created_at": row['created_at'],
                    "processed_at": row['processed_at'],
                    "error": row['error_message']
                })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Failed to get processed triggers: {e}")
            return []
    
    async def get_pending_triggers(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get pending triggers that haven't been processed by bot"""
        try:
            query = """
                SELECT * FROM admin_bot_triggers
                WHERE guild_id = ? AND processed = 0
                ORDER BY created_at ASC
            """
            
            result = await db_manager.execute_query(query, (guild_id,))
            
            triggers = []
            for row in result:
                triggers.append({
                    "id": row['id'],
                    "type": row['trigger_type'],
                    "guild_id": row['guild_id'],
                    "data": json.loads(row['trigger_data']),
                    "created_at": row['created_at'],
                    "age_seconds": int((datetime.utcnow() - datetime.fromisoformat(row['created_at'])).total_seconds())
                })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Failed to get pending triggers: {e}")
            return []
    
    async def cleanup_old_triggers(self, days_old: int = 7) -> int:
        """Clean up old processed triggers"""
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            delete_query = """
                DELETE FROM admin_bot_triggers
                WHERE processed = 1 AND processed_at < ?
            """
            
            result = await db_manager.execute_command(
                delete_query,
                (cutoff_date.isoformat(),)
            )
            
            logger.info(f"Cleaned up {result} old bot triggers")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup triggers: {e}")
            return 0

# Global bridge instance
bot_bridge = BotBridge()