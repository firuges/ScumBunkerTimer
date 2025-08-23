#!/usr/bin/env python3
"""
MIGRACIÓN BANCARIA UNIFICADA SEGURA
Consolida users, users y bank_accounts en bank_accounts como fuente única
Preserva el balance más alto y todos los datos críticos
"""

import asyncio
import aiosqlite
import logging
from datetime import datetime
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeBankingMigration:
    def __init__(self, db_path='scum_main.db'):
        self.db_path = db_path
        self.migration_log = []
        
    async def analyze_current_state(self):
        """Analizar estado actual de las tablas bancarias"""
        logger.info("🔍 Analizando estado actual...")
        
        async with aiosqlite.connect(self.db_path) as db:
            # Contar registros en cada tabla
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            users_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM users") 
            users_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM bank_accounts")
            bank_accounts_count = (await cursor.fetchone())[0]
            
            logger.info(f"📊 Estado actual:")
            logger.info(f"   - users: {users_count} registros")
            logger.info(f"   - users: {users_count} registros") 
            logger.info(f"   - bank_accounts: {bank_accounts_count} registros")
            
            # Verificar usuarios con dinero
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE balance > 0")
            users_with_money = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE balance > 0")
            taxi_with_money = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM bank_accounts WHERE balance > 0")
            bank_with_money = (await cursor.fetchone())[0]
            
            logger.info(f"💰 Usuarios con dinero:")
            logger.info(f"   - users: {users_with_money}")
            logger.info(f"   - users: {taxi_with_money}")
            logger.info(f"   - bank_accounts: {bank_with_money}")
            
            return {
                'users_count': users_count,
                'users_count': users_count,
                'bank_accounts_count': bank_accounts_count,
                'users_with_money': users_with_money,
                'taxi_with_money': taxi_with_money,
                'bank_with_money': bank_with_money
            }
    
    async def find_user_conflicts(self):
        """Encontrar usuarios que existen en múltiples tablas"""
        logger.info("🔍 Buscando conflictos entre tablas...")
        
        conflicts = []
        async with aiosqlite.connect(self.db_path) as db:
            # Buscar usuarios que están en users y users
            cursor = await db.execute("""
                SELECT u.user_id, u.discord_id, u.username, u.balance as users_balance,
                       t.balance as taxi_balance, u.ingame_name, t.ingame_name as taxi_ingame
                FROM users u
                users t ON u.discord_id = t.discord_id AND u.discord_guild_id = t.discord_guild_id
            """)
            
            user_taxi_conflicts = await cursor.fetchall()
            for conflict in user_taxi_conflicts:
                conflicts.append({
                    'type': 'users_vs_users',
                    'user_id': conflict[0],
                    'discord_id': conflict[1],
                    'username': conflict[2],
                    'users_balance': conflict[3],
                    'taxi_balance': conflict[4],
                    'users_ingame': conflict[5],
                    'taxi_ingame': conflict[6]
                })
                logger.warning(f"⚠️ Conflicto encontrado - Usuario: {conflict[2]}")
                logger.warning(f"   Balance users: ${conflict[3]} vs users: ${conflict[4]}")
                
            # Buscar usuarios que están en users y bank_accounts
            cursor = await db.execute("""
                SELECT u.user_id, u.discord_id, u.username, u.balance as users_balance,
                       b.balance as bank_balance, b.account_number
                FROM users u
                JOIN bank_accounts b ON u.user_id = b.user_id
            """)
            
            user_bank_conflicts = await cursor.fetchall()
            for conflict in user_bank_conflicts:
                conflicts.append({
                    'type': 'users_vs_bank_accounts',
                    'user_id': conflict[0],
                    'discord_id': conflict[1], 
                    'username': conflict[2],
                    'users_balance': conflict[3],
                    'bank_balance': conflict[4],
                    'account_number': conflict[5]
                })
                logger.warning(f"⚠️ Conflicto encontrado - Usuario: {conflict[2]}")
                logger.warning(f"   Balance users: ${conflict[3]} vs bank_accounts: ${conflict[4]}")
                
        logger.info(f"🔍 Total conflictos encontrados: {len(conflicts)}")
        return conflicts
    
    async def create_unified_migration_plan(self, conflicts):
        """Crear plan de migración unificada"""
        logger.info("📋 Creando plan de migración...")
        
        migration_plan = []
        
        async with aiosqlite.connect(self.db_path) as db:
            # Para cada usuario en users, crear/actualizar cuenta en bank_accounts
            cursor = await db.execute("""
                SELECT user_id, discord_id, discord_guild_id, username, display_name,
                       balance, timezone, ingame_name, language, welcome_pack_claimed,
                       created_at, last_active
                FROM users
            """)
            
            users_data = await cursor.fetchall()
            
            for user in users_data:
                user_id = user[0]
                discord_id = user[1]
                guild_id = user[2]
                username = user[3]
                balance_users = user[5] or 0.0
                
                # Buscar balance en users para este usuario
                cursor = await db.execute("""
                    SELECT balance, ingame_name, timezone 
                    FROM users 
                    WHERE discord_id = ? AND discord_guild_id = ?
                """, (discord_id, guild_id))
                
                taxi_data = await cursor.fetchone()
                balance_taxi = taxi_data[0] if taxi_data else 0.0
                ingame_taxi = taxi_data[1] if taxi_data else None
                timezone_taxi = taxi_data[2] if taxi_data else None
                
                # Buscar si ya tiene cuenta en bank_accounts
                cursor = await db.execute("""
                    SELECT account_id, balance, account_number
                    FROM bank_accounts
                    WHERE user_id = ?
                """, (user_id,))
                
                bank_data = await cursor.fetchone()
                balance_bank = float(bank_data[1]) if bank_data else 0.0
                
                # Determinar el balance final (el más alto)
                final_balance = max(balance_users, balance_taxi, balance_bank)
                
                # Determinar mejor ingame_name (el no nulo más reciente)
                best_ingame = user[7] or ingame_taxi  # users.ingame_name or taxi.ingame_name
                
                # Determinar mejor timezone  
                best_timezone = user[6] if user[6] != 'UTC' else timezone_taxi
                
                migration_plan.append({
                    'user_id': user_id,
                    'discord_id': discord_id,
                    'guild_id': guild_id,
                    'username': username,
                    'display_name': user[4],
                    'balance_users': balance_users,
                    'balance_taxi': balance_taxi, 
                    'balance_bank': balance_bank,
                    'final_balance': final_balance,
                    'best_ingame': best_ingame,
                    'best_timezone': best_timezone,
                    'has_bank_account': bank_data is not None,
                    'account_number': bank_data[2] if bank_data else None,
                    'welcome_pack_claimed': user[9],
                    'created_at': user[10],
                    'last_active': user[11]
                })
                
                logger.info(f"📝 Plan para {username}:")
                logger.info(f"   Balances: users=${balance_users}, taxi=${balance_taxi}, bank=${balance_bank}")
                logger.info(f"   Final: ${final_balance}")
                logger.info(f"   Ingame: {best_ingame}")
                
        return migration_plan
    
    async def execute_migration(self, migration_plan, dry_run=True):
        """Ejecutar migración según el plan"""
        if dry_run:
            logger.info("🧪 MODO DRY RUN - Solo simulación")
        else:
            logger.info("🚀 EJECUTANDO MIGRACIÓN REAL")
            
        async with aiosqlite.connect(self.db_path) as db:
            if not dry_run:
                await db.execute("BEGIN TRANSACTION")
                
            try:
                for plan in migration_plan:
                    user_id = plan['user_id']
                    username = plan['username']
                    final_balance = plan['final_balance']
                    
                    if plan['has_bank_account']:
                        # Actualizar cuenta existente
                        if not dry_run:
                            await db.execute("""
                                UPDATE bank_accounts 
                                SET balance = ?, 
                                    updated_at = CURRENT_TIMESTAMP,
                                    last_transaction = CURRENT_TIMESTAMP
                                WHERE user_id = ?
                            """, (final_balance, user_id))
                        
                        logger.info(f"✅ {username}: Actualizando cuenta existente -> ${final_balance}")
                        
                    else:
                        # Crear nueva cuenta bancaria
                        account_number = f"TAX{user_id:06d}"
                        
                        if not dry_run:
                            await db.execute("""
                                INSERT INTO bank_accounts 
                                (user_id, guild_id, account_number, balance, account_type,
                                 welcome_pack_received, created_at, updated_at, last_transaction, status)
                                VALUES (?, ?, ?, ?, 'personal', ?, CURRENT_TIMESTAMP, 
                                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'active')
                            """, (user_id, int(plan['guild_id']), account_number, final_balance,
                                  plan['welcome_pack_claimed']))
                        
                        logger.info(f"✅ {username}: Creando nueva cuenta {account_number} -> ${final_balance}")
                
                # Eliminar balance de users (mantener solo datos de perfil)
                if not dry_run:
                    await db.execute("UPDATE users SET balance = 0.0")
                    logger.info("🧹 Limpiando balances de tabla users")
                
                if not dry_run:
                    await db.execute("COMMIT")
                    logger.info("✅ Migración completada exitosamente")
                else:
                    logger.info("🧪 Simulación completada")
                    
            except Exception as e:
                if not dry_run:
                    await db.execute("ROLLBACK")
                logger.error(f"❌ Error en migración: {e}")
                raise
                
    async def validate_migration(self):
        """Validar que la migración fue exitosa"""
        logger.info("🔍 Validando migración...")
        
        async with aiosqlite.connect(self.db_path) as db:
            # Verificar que todos los usuarios de users tienen cuenta bancaria
            cursor = await db.execute("""
                SELECT COUNT(*) FROM users u
                LEFT JOIN bank_accounts b ON u.user_id = b.user_id
                WHERE b.user_id IS NULL
            """)
            orphaned_users = (await cursor.fetchone())[0]
            
            # Verificar que no hay balances en users
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE balance > 0")
            users_with_balance = (await cursor.fetchone())[0]
            
            # Verificar total de dinero en bank_accounts
            cursor = await db.execute("SELECT SUM(balance) FROM bank_accounts")
            total_bank_money = (await cursor.fetchone())[0] or 0
            
            logger.info(f"📊 Validación:")
            logger.info(f"   - Usuarios sin cuenta bancaria: {orphaned_users}")
            logger.info(f"   - Usuarios con balance en users: {users_with_balance}")
            logger.info(f"   - Total dinero en bank_accounts: ${total_bank_money}")
            
            return {
                'orphaned_users': orphaned_users,
                'users_with_balance': users_with_balance, 
                'total_bank_money': total_bank_money,
                'success': orphaned_users == 0 and users_with_balance == 0
            }

async def main():
    """Ejecutar migración bancaria completa"""
    migration = SafeBankingMigration()
    
    # Paso 1: Analizar estado actual
    current_state = await migration.analyze_current_state()
    
    # Paso 2: Encontrar conflictos
    conflicts = await migration.find_user_conflicts()
    
    # Paso 3: Crear plan de migración
    migration_plan = await migration.create_unified_migration_plan(conflicts)
    
    # Paso 4: Ejecutar en modo dry run primero
    await migration.execute_migration(migration_plan, dry_run=True)
    
    print("\n" + "="*60)
    print("🔍 REVISIÓN PREVIA COMPLETADA")
    print("Si todo se ve correcto, ejecutar con dry_run=False")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())