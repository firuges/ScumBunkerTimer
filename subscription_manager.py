"""
Sistema de suscripciones para el bot SCUM
Gestiona planes gratuitos y premium por Discord Guild
"""

import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self, db_path="subscriptions.db"):
        self.db_path = db_path
    
    async def initialize(self):
        """Inicializar base de datos de suscripciones"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tabla de suscripciones
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_guild_id TEXT UNIQUE NOT NULL,
                    plan_type TEXT DEFAULT 'free',
                    status TEXT DEFAULT 'active',
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de límites por plan
            await db.execute("""
                CREATE TABLE IF NOT EXISTS plan_limits (
                    plan_type TEXT PRIMARY KEY,
                    max_bunkers INTEGER,
                    max_servers INTEGER,
                    advanced_notifications BOOLEAN,
                    api_access BOOLEAN,
                    priority_support BOOLEAN,
                    monthly_price_usd DECIMAL(10,2)
                )
            """)
            
            # Insertar planes por defecto
            plans = [
                ('free', 1, 1, False, False, False, 0.00),  # 1 bunker cada 72 horas
                ('premium', -1, -1, True, True, True, 5.99),
                ('enterprise', -1, -1, True, True, True, 15.99)
            ]
            
            for plan in plans:
                await db.execute("""
                    INSERT OR REPLACE INTO plan_limits 
                    (plan_type, max_bunkers, max_servers, advanced_notifications, 
                     api_access, priority_support, monthly_price_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, plan)
            
            await db.commit()
            logger.info("Base de datos de suscripciones inicializada")
    
    async def get_subscription(self, guild_id: str) -> Dict:
        """Obtener suscripción de un guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT s.*, p.* FROM subscriptions s
                LEFT JOIN plan_limits p ON s.plan_type = p.plan_type
                WHERE s.discord_guild_id = ?
            """, (guild_id,))
            
            row = await cursor.fetchone()
            if not row:
                # Crear suscripción gratuita por defecto
                await self.create_free_subscription(guild_id)
                return await self.get_subscription(guild_id)
            
            return {
                'guild_id': row[1],
                'plan_type': row[2],
                'status': row[3],
                'current_period_end': row[7],
                'max_bunkers': int(row[11]) if row[11] is not None else 2,
                'max_servers': int(row[12]) if row[12] is not None else 1,
                'advanced_notifications': bool(row[13]),
                'api_access': bool(row[14]),
                'priority_support': bool(row[15]),
                'monthly_price': row[16]
            }
    
    async def create_free_subscription(self, guild_id: str):
        """Crear suscripción gratuita"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (discord_guild_id, plan_type, status)
                VALUES (?, 'free', 'active')
            """, (guild_id,))
            await db.commit()
    
    async def upgrade_subscription(self, guild_id: str, plan_type: str, 
                                 stripe_customer_id: str = None,
                                 stripe_subscription_id: str = None):
        """Actualizar a plan premium"""
        end_date = datetime.now() + timedelta(days=30)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE subscriptions 
                SET plan_type = ?, status = 'active',
                    stripe_customer_id = ?, stripe_subscription_id = ?,
                    current_period_start = ?, current_period_end = ?,
                    updated_at = ?
                WHERE discord_guild_id = ?
            """, (plan_type, stripe_customer_id, stripe_subscription_id,
                  datetime.now(), end_date, datetime.now(), guild_id))
            await db.commit()
    
    async def cancel_subscription(self, guild_id: str):
        """Cancelar suscripción (volver a free)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE subscriptions 
                SET plan_type = 'free', status = 'cancelled',
                    stripe_customer_id = NULL, stripe_subscription_id = NULL,
                    updated_at = ?
                WHERE discord_guild_id = ?
            """, (datetime.now(), guild_id))
            await db.commit()
    
    async def check_limits(self, guild_id: str, bunkers_count: int, servers_count: int) -> Dict:
        """Verificar si el guild está dentro de los límites"""
        subscription = await self.get_subscription(guild_id)
        
        # Convertir a enteros y -1 significa ilimitado
        max_bunkers = int(subscription['max_bunkers'])
        max_servers = int(subscription['max_servers'])
        
        bunkers_ok = max_bunkers == -1 or bunkers_count <= max_bunkers
        servers_ok = max_servers == -1 or servers_count <= max_servers
        
        return {
            'within_limits': bunkers_ok and servers_ok,
            'bunkers_ok': bunkers_ok,
            'servers_ok': servers_ok,
            'max_bunkers': max_bunkers,
            'max_servers': max_servers,
            'current_bunkers': bunkers_count,
            'current_servers': servers_count,
            'plan_type': subscription['plan_type']
        }
    
    async def get_all_subscriptions(self) -> List[Dict]:
        """Obtener todas las suscripciones activas"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT s.*, p.monthly_price_usd FROM subscriptions s
                LEFT JOIN plan_limits p ON s.plan_type = p.plan_type
                WHERE s.status = 'active'
                ORDER BY s.plan_type DESC, s.created_at DESC
            """)
            
            subscriptions = []
            async for row in cursor:
                subscriptions.append({
                    'guild_id': row[1],
                    'plan_type': row[2],
                    'status': row[3],
                    'current_period_end': row[6],
                    'monthly_price': row[15] or 0,
                    'created_at': row[7]
                })
            
            return subscriptions

# Instancia global
subscription_manager = SubscriptionManager()
