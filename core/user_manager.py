#!/usr/bin/env python3
"""
Gestor Centralizado de Usuarios
Maneja todas las operaciones relacionadas con usuarios de forma unificada.
Extrae la funcionalidad de usuario de taxi_database.py para ser reutilizada por todos los módulos.
"""

import aiosqlite
import logging
from datetime import datetime, date
from typing import Optional, Dict, Tuple, List
import asyncio

logger = logging.getLogger(__name__)

class UserManager:
    """Gestor centralizado de usuarios del sistema"""
    
    def __init__(self, db_path: str = None):
        # Auto-detectar qué base usar (compatibilidad durante migración)
        if db_path is None:
            import os
            if os.path.exists("scum_main.db"):
                self.db_path = "scum_main.db"
            elif os.path.exists("taxi_system.db"):
                self.db_path = "taxi_system.db"
            else:
                self.db_path = "scum_main.db"  # Default
        else:
            self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """Inicializar tablas de usuarios preservando estructura existente"""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            # Verificar si tabla taxi_users existe
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='taxi_users'
            """)
            table_exists = await cursor.fetchone()
            
            if not table_exists:
                # Crear tabla nueva con estructura completa
                await db.execute("""
                    CREATE TABLE taxi_users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT NOT NULL,
                        discord_guild_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        display_name TEXT,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        welcome_pack_claimed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        timezone TEXT DEFAULT 'UTC',
                        ingame_name TEXT,
                        language TEXT DEFAULT 'es',
                        balance REAL DEFAULT 0.0,
                        UNIQUE(discord_id, discord_guild_id)
                    )
                """)
            else:
                # Verificar y agregar columna balance si no existe
                cursor = await db.execute("PRAGMA table_info(taxi_users)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'balance' not in column_names:
                    await db.execute("ALTER TABLE taxi_users ADD COLUMN balance REAL DEFAULT 0.0")
                    logger.info("Agregada columna 'balance' a tabla taxi_users")
            
            # Tabla de transacciones (movida de taxi_database para centralizar)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_account TEXT NOT NULL,
                    to_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT DEFAULT 'transfer',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    guild_id TEXT
                )
            """)
            
            # Tabla de recompensas diarias
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES taxi_users(user_id)
                )
            """)
            
            await db.commit()
            self._initialized = True
            logger.info("UserManager inicializado correctamente")
    
    # === GESTIÓN BÁSICA DE USUARIOS ===
    
    async def register_user(self, discord_id: str, guild_id: str, username: str, 
                           display_name: str = None, timezone: str = None, 
                           ingame_name: str = None) -> Tuple[bool, Dict]:
        """
        Registrar nuevo usuario en el sistema.
        Mantiene compatibilidad total con taxi_database.register_user()
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Verificar si ya existe
                cursor = await db.execute(
                    "SELECT user_id FROM taxi_users WHERE discord_id = ? AND discord_guild_id = ?",
                    (discord_id, guild_id)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    logger.warning(f"Usuario {discord_id} ya existe en guild {guild_id}")
                    return False, {}
                
                # Detectar timezone si no se proporciona
                if not timezone:
                    timezone = 'UTC'  # Default seguro
                
                # Registrar usuario con estructura existente
                cursor = await db.execute("""
                    INSERT INTO taxi_users (discord_id, discord_guild_id, username, display_name, 
                                          welcome_pack_claimed, timezone, ingame_name, balance, language)
                    VALUES (?, ?, ?, ?, TRUE, ?, ?, 1000.0, 'es')
                """, (discord_id, guild_id, username, display_name, timezone, ingame_name))
                
                user_id = cursor.lastrowid
                await db.commit()
                
                # Generar número de cuenta (mantiene compatibilidad)
                account_number = f"ACC-{user_id:06d}"
                
                user_data = {
                    'user_id': user_id,
                    'discord_id': discord_id,
                    'discord_guild_id': guild_id,
                    'username': username,
                    'display_name': display_name,
                    'balance': 1000.0,
                    'account_number': account_number,
                    'timezone': timezone,
                    'ingame_name': ingame_name,
                    'language': 'es'
                }
                
                logger.info(f"Usuario {username} registrado exitosamente con ID {user_id}")
                return True, user_data
                
            except Exception as e:
                logger.error(f"Error registrando usuario {username}: {e}")
                return False, {}
    
    async def get_user_by_discord_id(self, discord_id: str, guild_id: str) -> Optional[Dict]:
        """
        Obtener usuario por Discord ID.
        Mantiene compatibilidad total con taxi_database.get_user_by_discord_id()
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Usar tabla users (unificada) y obtener cuenta real de bank_accounts
            cursor = await db.execute("""
                SELECT u.user_id, u.discord_id, u.discord_guild_id, u.username, u.display_name, 
                       u.timezone, u.language, u.ingame_name, u.last_active, u.created_at, 
                       u.welcome_pack_claimed, u.status, b.account_number, b.balance
                FROM users u
                LEFT JOIN bank_accounts b ON u.user_id = b.user_id
                WHERE u.discord_id = ? AND u.discord_guild_id = ?
            """, (discord_id, guild_id))
            
            row = await cursor.fetchone()
            if row:
                user_data = {
                    'user_id': row[0],
                    'discord_id': row[1],
                    'discord_guild_id': row[2],
                    'username': row[3],
                    'display_name': row[4],
                    'timezone': row[5] or 'UTC',
                    'language': row[6] or 'es',
                    'ingame_name': row[7],
                    'last_active': row[8],
                    'created_at': row[9],
                    'welcome_pack_claimed': row[10] or False,
                    'status': row[11] or 'active',
                    'account_number': row[12] or f"ACC-{row[0]:06d}",  # Número real o fallback
                    'balance': float(row[13]) if row[13] is not None else 0.0  # Balance real de bank_accounts
                }
                return user_data
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Obtener usuario por ID interno.
        Mantiene compatibilidad total con taxi_database.get_user_by_id()
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Usar tabla users (unificada) y obtener cuenta real de bank_accounts
            cursor = await db.execute("""
                SELECT u.user_id, u.discord_id, u.discord_guild_id, u.username, u.display_name, 
                       u.timezone, u.language, u.ingame_name, u.last_active, u.created_at, 
                       u.welcome_pack_claimed, u.status, b.account_number, b.balance
                FROM users u
                LEFT JOIN bank_accounts b ON u.user_id = b.user_id
                WHERE u.user_id = ?
            """, (user_id,))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'discord_id': row[1],
                    'discord_guild_id': row[2],
                    'username': row[3],
                    'display_name': row[4],
                    'timezone': row[5] or 'UTC',
                    'language': row[6] or 'es',
                    'ingame_name': row[7],
                    'last_active': row[8],
                    'created_at': row[9],
                    'welcome_pack_claimed': row[10] or False,
                    'status': row[11] or 'active',
                    'account_number': row[12] or f"ACC-{row[0]:06d}",  # Número real o fallback
                    'balance': float(row[13]) if row[13] is not None else 0.0  # Balance real de bank_accounts
                }
            return None
    
    async def update_user_last_active(self, user_id: int):
        """Actualizar última actividad del usuario"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE taxi_users 
                SET last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    # === GESTIÓN DE IDIOMAS ===
    
    async def update_user_language(self, user_id: int, language: str) -> bool:
        """
        Actualizar idioma preferido del usuario.
        Mantiene compatibilidad total con taxi_database.update_user_language()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE taxi_users SET language = ? WHERE user_id = ?",
                    (language, user_id)
                )
                await db.commit()
                logger.info(f"Idioma de usuario {user_id} actualizado a: {language}")
                return True
        except Exception as e:
            logger.error(f"Error actualizando idioma: {e}")
            return False
    
    async def get_user_language(self, user_id: int) -> str:
        """
        Obtener idioma preferido del usuario por ID interno.
        Mantiene compatibilidad total con taxi_database.get_user_language()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT language FROM taxi_users WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                if result and result[0]:
                    return result[0]
                return 'es'  # Default
        except Exception as e:
            logger.error(f"Error obteniendo idioma: {e}")
            return 'es'
    
    async def get_user_language_by_discord_id(self, discord_id: str, guild_id: str = None) -> str:
        """
        Obtener idioma preferido del usuario por Discord ID.
        Mantiene compatibilidad total con taxi_database.get_user_language_by_discord_id()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if guild_id:
                    cursor = await db.execute(
                        "SELECT language FROM taxi_users WHERE discord_id = ? AND discord_guild_id = ?",
                        (discord_id, guild_id)
                    )
                else:
                    cursor = await db.execute(
                        "SELECT language FROM taxi_users WHERE discord_id = ?",
                        (discord_id,)
                    )
                
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 'es'
        except Exception as e:
            logger.error(f"Error obteniendo idioma por Discord ID: {e}")
            return 'es'
    
    # === GESTIÓN DE TIMEZONE ===
    
    async def update_user_timezone(self, discord_id: str, guild_id: str, timezone: str) -> bool:
        """
        Actualizar timezone del usuario.
        Mantiene compatibilidad total con taxi_database.update_user_timezone()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    UPDATE taxi_users 
                    SET timezone = ? 
                    WHERE discord_id = ? AND discord_guild_id = ?
                """, (timezone, discord_id, guild_id))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Timezone de {discord_id} actualizado a {timezone}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error actualizando timezone: {e}")
            return False
    
    # === GESTIÓN FINANCIERA ===
    
    async def get_user_balance(self, user_id: int) -> float:
        """
        Obtener balance del usuario.
        Mantiene compatibilidad total con taxi_database.get_user_balance()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Usar bank_accounts como fuente única de verdad
                cursor = await db.execute(
                    "SELECT balance FROM bank_accounts WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                return float(result[0]) if result else 0.0
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return 0.0
    
    async def add_money(self, user_id: int, amount: float, description: str = "System credit") -> bool:
        """Agregar dinero a un usuario"""
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Usar bank_accounts como fuente única de verdad
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance + ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        last_transaction = CURRENT_TIMESTAMP,
                        total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (amount, amount, user_id))
                
                # Registrar transacción
                user = await self.get_user_by_id(user_id)
                if user:
                    await db.execute("""
                        INSERT INTO user_transactions (from_account, to_account, amount, transaction_type, description, guild_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("SYSTEM", user['account_number'], amount, "credit", description, user['discord_guild_id']))
                
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error agregando dinero: {e}")
            return False
    
    async def subtract_money(self, user_id: int, amount: float, description: str = "System debit") -> bool:
        """
        Restar dinero a un usuario.
        Mantiene compatibilidad total con taxi_database.subtract_money()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar balance suficiente
                current_balance = await self.get_user_balance(user_id)
                if current_balance < amount:
                    return False
                
                # Usar bank_accounts como fuente única de verdad
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance - ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        last_transaction = CURRENT_TIMESTAMP,
                        total_spent = total_spent + ?
                    WHERE user_id = ?
                """, (amount, amount, user_id))
                
                # Registrar transacción
                user = await self.get_user_by_id(user_id)
                if user:
                    await db.execute("""
                        INSERT INTO user_transactions (from_account, to_account, amount, transaction_type, description, guild_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user['account_number'], "SYSTEM", amount, "debit", description, user['discord_guild_id']))
                
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error restando dinero: {e}")
            return False
    
    async def transfer_money(self, from_user_id: int, to_user_id: int, amount: float, 
                           description: str = "Transfer") -> Tuple[bool, str]:
        """
        Transferir dinero entre usuarios.
        Mantiene compatibilidad con taxi_database.transfer_money() pero usando IDs de usuario
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar balances y usuarios
                from_user = await self.get_user_by_id(from_user_id)
                to_user = await self.get_user_by_id(to_user_id)
                
                if not from_user or not to_user:
                    return False, "Usuario no encontrado"
                
                if from_user['balance'] < amount:
                    return False, "Balance insuficiente"
                
                # Realizar transferencia usando bank_accounts
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance - ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        last_transaction = CURRENT_TIMESTAMP,
                        total_spent = total_spent + ?
                    WHERE user_id = ?
                """, (amount, amount, from_user_id))
                
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance + ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        last_transaction = CURRENT_TIMESTAMP,
                        total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (amount, amount, to_user_id))
                
                # Registrar transacción
                await db.execute("""
                    INSERT INTO user_transactions (from_account, to_account, amount, transaction_type, description, guild_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (from_user['account_number'], to_user['account_number'], amount, "transfer", description, from_user['discord_guild_id']))
                
                await db.commit()
                return True, "Transferencia exitosa"
                
        except Exception as e:
            logger.error(f"Error en transferencia: {e}")
            return False, f"Error: {e}"
    
    # === SISTEMA DE RECOMPENSAS DIARIAS ===
    
    async def get_last_daily_claim(self, user_id: int) -> str:
        """
        Obtener la fecha del último canje diario del usuario.
        Mantiene compatibilidad con taxi_database.get_last_daily_claim()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT claimed_at FROM daily_rewards 
                    WHERE user_id = ? 
                    ORDER BY claimed_at DESC 
                    LIMIT 1
                """, (user_id,))
                
                result = await cursor.fetchone()
                if result:
                    return result[0]
                return ""  # No ha canjeado nunca
        except Exception as e:
            logger.error(f"Error obteniendo último canje diario: {e}")
            return ""
    
    async def add_daily_reward(self, user_id: int, amount: float = 500.0) -> bool:
        """
        Agregar recompensa diaria al usuario.
        Mantiene compatibilidad con taxi_database.add_daily_reward()
        """
        await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Registrar la recompensa
                await db.execute("""
                    INSERT INTO daily_rewards (user_id, amount)
                    VALUES (?, ?)
                """, (user_id, amount))
                
                # Agregar dinero al balance usando bank_accounts
                await db.execute("""
                    UPDATE bank_accounts 
                    SET balance = balance + ?, 
                        updated_at = CURRENT_TIMESTAMP,
                        last_transaction = CURRENT_TIMESTAMP,
                        total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (amount, amount, user_id))
                
                # Registrar transacción
                user = await self.get_user_by_id(user_id)
                if user:
                    await db.execute("""
                        INSERT INTO user_transactions (from_account, to_account, amount, transaction_type, description, guild_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("SYSTEM", user['account_number'], amount, "daily_reward", "Daily reward", user['discord_guild_id']))
                
                await db.commit()
                logger.info(f"Recompensa diaria de ${amount:,.0f} agregada al usuario {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error agregando recompensa diaria: {e}")
            return False
    
    # === ESTADÍSTICAS ===
    
    async def get_user_count(self, guild_id: str = None) -> int:
        """Obtener número total de usuarios registrados"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            if guild_id:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM taxi_users WHERE discord_guild_id = ?", 
                    (guild_id,)
                )
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM taxi_users")
            
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Obtener transacciones recientes del usuario.
        Mantiene compatibilidad con taxi_database.get_user_transactions()
        """
        await self.initialize()
        
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return []
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT from_account, to_account, amount, transaction_type, description, created_at
                    FROM user_transactions 
                    WHERE from_account = ? OR to_account = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user['account_number'], user['account_number'], limit))
                
                transactions = []
                async for row in cursor:
                    transactions.append({
                        'from_account': row[0],
                        'to_account': row[1],
                        'amount': row[2],
                        'transaction_type': row[3],
                        'description': row[4],
                        'created_at': row[5]
                    })
                
                return transactions
        except Exception as e:
            logger.error(f"Error obteniendo transacciones: {e}")
            return []

# Instancia global para mantener compatibilidad
user_manager = UserManager()

# === FUNCIONES DE COMPATIBILIDAD ===
# Estas funciones mantienen la API existente para evitar romper código existente

async def register_user(discord_id: str, guild_id: str, username: str, 
                       display_name: str = None, timezone: str = None, 
                       ingame_name: str = None) -> Tuple[bool, Dict]:
    """Función de compatibilidad con taxi_database.register_user()"""
    return await user_manager.register_user(discord_id, guild_id, username, display_name, timezone, ingame_name)

async def get_user_by_discord_id(discord_id: str, guild_id: str) -> Optional[Dict]:
    """Función de compatibilidad con taxi_database.get_user_by_discord_id()"""
    return await user_manager.get_user_by_discord_id(discord_id, guild_id)

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Función de compatibilidad con taxi_database.get_user_by_id()"""
    return await user_manager.get_user_by_id(user_id)

async def get_user_balance(user_id: int) -> float:
    """Función de compatibilidad con taxi_database.get_user_balance()"""
    return await user_manager.get_user_balance(user_id)

async def subtract_money(user_id: int, amount: float, description: str = "System debit") -> bool:
    """Función de compatibilidad con taxi_database.subtract_money()"""
    return await user_manager.subtract_money(user_id, amount, description)

async def update_user_language(user_id: int, language: str) -> bool:
    """Función de compatibilidad con taxi_database.update_user_language()"""
    return await user_manager.update_user_language(user_id, language)

async def get_user_language_by_discord_id(discord_id: str, guild_id: str = None) -> str:
    """Función de compatibilidad con taxi_database.get_user_language_by_discord_id()"""
    return await user_manager.get_user_language_by_discord_id(discord_id, guild_id)

async def update_user_timezone(discord_id: str, guild_id: str, timezone: str) -> bool:
    """Función de compatibilidad con taxi_database.update_user_timezone()"""
    return await user_manager.update_user_timezone(discord_id, guild_id, timezone)

async def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict]:
    """Función de compatibilidad con taxi_database.get_user_transactions()"""
    return await user_manager.get_user_transactions(user_id, limit)

async def add_money(user_id: int, amount: float, description: str = "System credit") -> bool:
    """Función de compatibilidad con taxi_database.add_money()"""
    return await user_manager.add_money(user_id, amount, description)

async def user_exists(user_id: int) -> bool:
    """Función de compatibilidad: verificar si usuario existe por Discord ID"""
    # Buscar en todas las guilds ya que solo tenemos Discord ID
    await user_manager.initialize()
    
    try:
        async with aiosqlite.connect(user_manager.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM taxi_users WHERE discord_id = ? LIMIT 1",
                (str(user_id),)
            )
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Error verificando existencia de usuario: {e}")
        return False

async def get_user(user_id: int) -> Optional[Dict]:
    """Función de compatibilidad: obtener usuario por Discord ID (primera coincidencia)"""
    await user_manager.initialize()
    
    try:
        async with aiosqlite.connect(user_manager.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id, discord_id, discord_guild_id, username, display_name, 
                       COALESCE(balance, 0.0) as balance, timezone, language, ingame_name, 
                       last_active, created_at, welcome_pack_claimed, status
                FROM taxi_users 
                WHERE discord_id = ?
                LIMIT 1
            """, (str(user_id),))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'discord_id': row[1],
                    'discord_guild_id': row[2],
                    'username': row[3],
                    'display_name': row[4],
                    'balance': row[5] or 0.0,
                    'timezone': row[6] or 'UTC',
                    'language': row[7] or 'es',
                    'ingame_name': row[8],
                    'last_active': row[9],
                    'created_at': row[10],
                    'welcome_pack_claimed': row[11] or False,
                    'status': row[12] or 'active',
                    'account_number': f"ACC-{row[0]:06d}",
                    'user_type': 'player',  # Valor por defecto para compatibilidad
                    'joined_at': row[10]  # Alias para created_at
                }
            return None
    except Exception as e:
        logger.error(f"Error obteniendo usuario: {e}")
        return None

async def get_last_daily_claim(user_id: int) -> str:
    """Función de compatibilidad con taxi_database.get_last_daily_claim()"""
    return await user_manager.get_last_daily_claim(user_id)

async def add_daily_reward(user_id: int, amount: float = 500.0) -> bool:
    """Función de compatibilidad con taxi_database.add_daily_reward()"""
    return await user_manager.add_daily_reward(user_id, amount)

async def transfer_money_by_discord_id(sender_id: int, receiver_id: int, amount: float, description: str = "Transfer") -> Tuple[bool, str]:
    """Función de compatibilidad para transfer_money usando Discord IDs en lugar de user IDs"""
    try:
        # Obtener usuarios por Discord ID
        sender = await get_user(sender_id)
        receiver = await get_user(receiver_id)
        
        if not sender:
            return False, "Remitente no encontrado"
        if not receiver:
            return False, "Destinatario no encontrado"
        
        # Usar transfer_money del user_manager con user IDs internos
        return await user_manager.transfer_money(
            sender['user_id'], 
            receiver['user_id'], 
            amount, 
            description
        )
    except Exception as e:
        logger.error(f"Error en transfer_money_by_discord_id: {e}")
        return False, f"Error: {e}"