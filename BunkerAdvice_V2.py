#!/usr/bin/env python3
"""
Bot Discord para SCUM - Gestión de Bunkers Abandonados V2
Con soporte para múltiples servidores y sistema de suscripciones
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from database_v2 import BunkerDatabaseV2
import os
from typing import List, Optional
from aiohttp import web
import aiohttp
from subscription_manager import subscription_manager
from premium_utils import check_limits, premium_required
from premium_commands import setup_premium_commands
from premium_exclusive_commands import setup_premium_exclusive_commands
from bot_status_system import setup_bot_status
from server_database import server_db
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Importar configuración del bot
try:
    from config import BOT_CREATOR_ID, DISCORD_TOKEN
except ImportError:
    # ID del creador del bot (reemplazar con tu Discord User ID)
    BOT_CREATOR_ID = 123456789012345678  # CAMBIAR POR TU ID DE DISCORD
    DISCORD_TOKEN = None

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True

class BunkerBotV2(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.db = BunkerDatabaseV2()

    async def setup_hook(self):
        """Inicializa el bot"""
        await self.db.initialize()
        
        # Inicializar sistema de suscripciones
        await subscription_manager.initialize()
        logger.info("Sistema de suscripciones inicializado")
        
        # Inicializar tablas de monitoreo de servidores
        await server_db.initialize_server_tables()
        logger.info("Sistema de monitoreo de servidores inicializado")
        
        # === INICIALIZAR SISTEMA DE TAXI MODULAR ===
        try:
            # Inicializar base de datos del taxi
            from taxi_database import taxi_db
            await taxi_db.initialize()
            logger.info("✅ Sistema de taxi - Base de datos inicializada")
            
            # Cargar configuración del taxi
            from taxi_config import taxi_config
            taxi_config.load_config_from_db(taxi_db.db_path)
            logger.info("✅ Sistema de taxi - Configuración cargada")
            
            # Cargar extensiones del taxi
            await self.load_extension('welcome_system')
            
            # Cargar sistema bancario con manejo de errores específico
            try:
                await self.load_extension('banking_system')
                logger.info("✅ Sistema bancario cargado exitosamente")
            except Exception as bank_error:
                logger.error(f"❌ Error cargando sistema bancario: {bank_error}")
            
            await self.load_extension('taxi_system')
            await self.load_extension('taxi_admin')  # ✅ Rehabilitado con migración completa
            logger.info("✅ Sistema de taxi - Extensiones principales cargadas")
            
            # Registrar vistas persistentes para el sistema de shop
            try:
                from taxi_admin import DeliveryConfirmationView, PersistentDeliveryView
                
                # Registrar una vista general para todos los botones de entrega
                self.add_view(PersistentDeliveryView())
                logger.info("✅ Vista persistente de confirmación de entrega registrada")
            except Exception as view_error:
                logger.error(f"❌ Error registrando vistas persistentes: {view_error}")
            
        except Exception as e:
                logger.error(f"❌ Error inicializando sistema de taxi: {e}")
        
        # Configurar comandos premium
        await setup_premium_commands(self)
        setup_premium_exclusive_commands(self)
        
        # Cargar cog de comandos de servidor
        await self.load_extension('server_commands')
        logger.info("Comandos de monitoreo de servidores cargados")
        
        # Cargar cog de comandos de alertas de reinicio
        await self.load_extension('reset_alerts_admin')
        logger.info("Comandos administrativos de alertas de reinicio cargados")
        
        self.notification_task.start()
        self.reset_alerts_task.start()
        self.cleanup_task.start()
        
        # NO sincronizar aquí - se hace en on_ready después de que todos los comandos estén registrados

    def should_use_personal_dm(self, user_id: int, guild: discord.Guild) -> bool:
        """
        Determina si debe usar DM personal o canal público.
        
        Args:
            user_id: ID del usuario
            guild: Servidor de Discord
        
        Returns:
            True si debe usar DM personal, False si debe usar canal público
        """
        # Si es el creador del bot, usar canal público
        if user_id == BOT_CREATOR_ID:
            return False
        
        # Si es el owner del servidor, usar canal público
        if guild and user_id == guild.owner_id:
            return False
        
        # Para todos los demás usuarios, usar DM personal
        return True

    async def on_ready(self):
        logger.info(f'{self.user} conectado a Discord!')
        logger.info(f'Bot conectado en {len(self.guilds)} servidores')
        
        # Sincronizar comandos después de que todo esté listo
        try:
            total_commands = len([cmd for cmd in self.tree.walk_commands()])
            logger.info(f"Comandos registrados antes de sync: {total_commands}")
            
            # Sync global con retry si hay errores de signature mismatch
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    synced = await self.tree.sync()
                    logger.info(f"EXITO: Sincronizados {len(synced)} comandos con Discord (intento {attempt + 1})")
                    break
                except Exception as e:
                    if "signature" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"Error de signature en intento {attempt + 1}, reintentando en 2 segundos...")
                        await asyncio.sleep(2)
                        # Force sync clearing cache
                        try:
                            await self.tree.sync()
                        except:
                            pass
                    else:
                        logger.error(f"ERROR: Error sincronizando comandos después de {attempt + 1} intentos: {e}")
                        raise
        except Exception as e:
            logger.error(f"ERROR: Error sincronizando comandos: {e}")
        
        # Inicializar sistema de estado del bot
        try:
            self.status_system = setup_bot_status(self)
            logger.info("Sistema de estado del bot inicializado")
        except Exception as e:
            logger.error(f"Error inicializando sistema de estado: {e}")
            
        # Cargar configuraciones de canales para todos los sistemas
        try:
            logger.info("Cargando configuraciones de canales desde base de datos...")
            
            # Cargar configuraciones de taxi
            taxi_cog = self.get_cog('TaxiSystem')
            if taxi_cog:
                await taxi_cog.load_channel_configs()
            
            # Cargar configuraciones de banking
            banking_cog = self.get_cog('BankingSystem')
            if banking_cog:
                await banking_cog.load_channel_configs()
            
            # Cargar configuraciones de welcome
            welcome_cog = self.get_cog('WelcomePackSystem')
            if welcome_cog:
                await welcome_cog.load_channel_configs()
            
            # Cargar configuraciones de shop (no tiene cog dedicado)
            await self._load_shop_configs()
            
            logger.info("✅ Todas las configuraciones de canales cargadas exitosamente")
            
            # Enviar notificación de startup a canales de estado
            if hasattr(self, 'status_system') and self.status_system:
                try:
                    await self.status_system.send_startup_notification()
                    logger.info("✅ Notificaciones de startup enviadas a canales de estado")
                except Exception as e:
                    logger.error(f"Error enviando notificación de startup: {e}")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de canales: {e}")
    
    async def on_disconnect(self):
        """Evento cuando el bot se desconecta"""
        logger.warning("Bot desconectado de Discord")
        
        # Enviar notificaciones de apagado a canales de estado
        if hasattr(self, 'status_system') and self.status_system:
            try:
                await self.status_system.send_shutdown_notification()
            except Exception as e:
                logger.error(f"Error enviando notificación de apagado: {e}")
    
    async def close(self):
        """Evento cuando el bot se cierra completamente"""
        logger.info("Cerrando bot...")
        
        # Enviar notificaciones de apagado antes de cerrar
        if hasattr(self, 'status_system') and self.status_system:
            try:
                await self.status_system.send_shutdown_notification()
            except Exception as e:
                logger.error(f"Error enviando notificación de cierre: {e}")
        
        # Llamar al close original
        await super().close()
    
    async def _load_shop_configs(self):
        """Cargar configuraciones de shop y recrear paneles"""
        try:
            from taxi_database import taxi_db
            configs = await taxi_db.load_all_channel_configs()
            
            shop_panels_recreated = 0
            
            for guild_id, channels in configs.items():
                guild_id_int = int(guild_id)
                
                # Recrear panel de shop
                if "shop" in channels:
                    channel_id = channels["shop"]
                    await self._recreate_shop_panel(guild_id_int, channel_id)
                    shop_panels_recreated += 1
                
                # Recrear panel de shop_claimer
                if "shop_claimer" in channels:
                    channel_id = channels["shop_claimer"]
                    await self._recreate_shop_claimer_panel(guild_id_int, channel_id)
                
                # Cargar configuraciones de status channels
                if "status" in channels:
                    channel_id = int(channels["status"])
                    if hasattr(self, 'status_system'):
                        self.status_system.status_channel_id = channel_id
                        await self.status_system.setup_status_channel(channel_id)
                        logger.info(f"Status channel {channel_id} cargado para guild {guild_id}")
                
                if "public_status" in channels:
                    channel_id = int(channels["public_status"])
                    if hasattr(self, 'status_system'):
                        self.status_system.public_status_channel_id = channel_id
                        await self.status_system.setup_public_status_channel(channel_id)
                        logger.info(f"Public status channel {channel_id} cargado para guild {guild_id}")
            
            logger.info(f"Sistema de shop: {shop_panels_recreated} paneles recreados")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de shop: {e}")
    
    async def _recreate_shop_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de shop en un canal específico"""
        try:
            channel = self.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de shop {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Limpiar mensajes anteriores del bot (solo los más recientes)
            try:
                deleted_count = 0
                async for message in channel.history(limit=10):
                    if message.author == self.user and message.embeds:
                        # Solo eliminar si es un embed del sistema de shop
                        for embed in message.embeds:
                            if embed.title and ("Tienda" in embed.title or "Shop" in embed.title):
                                await message.delete()
                                deleted_count += 1
                                break
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} paneles de shop anteriores del canal {channel_id}")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes de shop anteriores: {cleanup_e}")
            
            # Crear embed de shop
            try:
                from taxi_admin import ShopSystemView
                
                shop_embed = discord.Embed(
                    title="🛒 Tienda de Supervivencia SCUM",
                    description="¡Intercambia tus recursos por equipamiento de supervivencia de alta gama!\n\nSelecciona tu tier para ver los packs disponibles.",
                    color=discord.Color.gold()
                )
                
                shop_embed.add_field(
                    name="🎯 Tiers Disponibles:",
                    value="🥉 **Tier 1** - Packs básicos de supervivencia\n🥈 **Tier 2** - Equipment intermedio\n🥇 **Tier 3** - Gear profesional y armas",
                    inline=False
                )
                
                shop_embed.add_field(
                    name="💡 Cómo Funciona:",
                    value="1️⃣ Selecciona tu tier\n2️⃣ Elige el pack que necesitas\n3️⃣ Confirma tu compra\n4️⃣ ¡Espera la entrega en el juego!",
                    inline=False
                )
                
                shop_view = ShopSystemView()
                await channel.send(embed=shop_embed, view=shop_view)
                logger.info(f"Panel de shop recreado exitosamente en canal {channel_id}")
                
            except ImportError:
                # Si no se puede importar ShopSystemView, crear panel básico
                shop_embed = discord.Embed(
                    title="🛒 Tienda de Supervivencia SCUM",
                    description="Sistema de tienda temporalmente en mantenimiento.",
                    color=discord.Color.gold()
                )
                await channel.send(embed=shop_embed)
                logger.warning(f"Panel de shop recreado sin botones en canal {channel_id}")
                
        except Exception as e:
            logger.error(f"Error recreando panel de shop para canal {channel_id}: {e}")
    
    async def _recreate_shop_claimer_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de shop_claimer en un canal específico"""
        try:
            channel = self.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de shop_claimer {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Limpiar mensajes anteriores del bot
            try:
                deleted_count = 0
                async for message in channel.history(limit=10):
                    if message.author == self.user and message.embeds:
                        for embed in message.embeds:
                            if embed.title and ("Claimer" in embed.title or "Notificaciones" in embed.title):
                                await message.delete()
                                deleted_count += 1
                                break
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} paneles de shop_claimer anteriores del canal {channel_id}")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes de shop_claimer anteriores: {cleanup_e}")
            
            # Crear embed de shop_claimer
            claimer_embed = discord.Embed(
                title="🔔 Canal de Notificaciones de Compras",
                description="Este canal recibe automáticamente las notificaciones de todas las compras realizadas en la tienda.",
                color=discord.Color.orange()
            )
            
            claimer_embed.add_field(
                name="📋 Información Incluida:",
                value="• **Usuario** que realizó la compra\n• **Pack adquirido** y tier\n• **Recursos entregados**\n• **Timestamp** de la transacción",
                inline=False
            )
            
            claimer_embed.add_field(
                name="⚙️ Para Administradores:",
                value="• Monitorear actividad de la tienda\n• Validar entregas de items\n• Detectar posibles problemas\n• Solo administradores pueden ver este canal",
                inline=False
            )
            
            await channel.send(embed=claimer_embed)
            logger.info(f"Panel de shop_claimer recreado exitosamente en canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel de shop_claimer para canal {channel_id}: {e}")

    @tasks.loop(minutes=5)
    async def notification_task(self):
        """Tarea para enviar notificaciones programadas"""
        try:
            notifications = await self.db.get_pending_notifications()
            logger.info(f"Verificando notificaciones: {len(notifications)} pendientes")
            
            for notification in notifications:
                logger.info(f"Enviando notificación: {notification['type']} para {notification['sector']} en {notification['server_name']}")
                await self.send_notification(notification)
                await self.db.mark_notification_sent(notification["id"])
                logger.info(f"Notificación enviada y marcada como completada")
                
        except Exception as e:
            logger.error(f"Error en notification_task: {e}")

    @tasks.loop(minutes=1)
    async def reset_alerts_task(self):
        """Tarea para enviar alertas de reinicio de servidores"""
        try:
            from taxi_database import taxi_db
            from datetime import datetime, timedelta
            import pytz
            
            # Obtener todos los horarios de reinicio activos
            schedules = await taxi_db.get_reset_schedules()
            current_utc = datetime.now(pytz.UTC)
            
            for schedule in schedules:
                try:
                    # Convertir zona horaria del horario
                    tz = pytz.timezone(schedule['timezone'])
                    current_local = current_utc.astimezone(tz)
                    
                    # Verificar si es un día activo
                    current_weekday = current_local.isoweekday()  # 1=Lunes, 7=Domingo
                    active_days = [int(d.strip()) for d in schedule['days_of_week'].split(',')]
                    
                    if current_weekday not in active_days:
                        continue
                    
                    # Parsear hora del reinicio
                    reset_hour, reset_minute = map(int, schedule['reset_time'].split(':'))
                    
                    # Calcular tiempo hasta el próximo reinicio
                    reset_today = current_local.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
                    
                    # Si ya pasó hoy, será mañana
                    if reset_today <= current_local:
                        reset_today += timedelta(days=1)
                    
                    # Calcular minutos hasta el reinicio
                    time_until_reset = reset_today - current_local
                    minutes_until = int(time_until_reset.total_seconds() / 60)
                    
                    # Obtener usuarios suscritos a este servidor
                    subscribed_users = await taxi_db.get_users_for_reset_alert(schedule['server_name'])
                    
                    for user_alert in subscribed_users:
                        try:
                            # Verificar si es tiempo de alertar (dentro de un rango de 1 minuto)
                            if abs(minutes_until - user_alert['minutes_before']) <= 1:
                                # Verificar si ya se envió esta alerta hoy
                                alert_date = current_local.strftime('%Y-%m-%d')
                                already_sent = await taxi_db.check_alert_already_sent(
                                    user_alert['user_id'],
                                    user_alert['guild_id'],
                                    schedule['server_name'],
                                    schedule['id'],
                                    alert_date
                                )
                                
                                if not already_sent:
                                    success = await self.send_reset_alert(
                                        user_alert['user_id'],
                                        user_alert['guild_id'],
                                        schedule['server_name'],
                                        schedule['reset_time'],
                                        schedule['timezone'],
                                        minutes_until
                                    )
                                    
                                    if success:
                                        # Marcar como enviada en el caché
                                        await taxi_db.mark_alert_sent(
                                            user_alert['user_id'],
                                            user_alert['guild_id'],
                                            schedule['server_name'],
                                            schedule['id'],
                                            alert_date
                                        )
                        except Exception as e:
                            logger.error(f"Error enviando alerta a usuario {user_alert['user_id']}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error procesando horario {schedule['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error en reset_alerts_task: {e}")

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Tarea diaria de limpieza"""
        try:
            from taxi_database import taxi_db
            
            # Limpiar caché de alertas de reinicio (mantener solo últimos 7 días)
            await taxi_db.cleanup_old_alert_cache(days_old=7)
            
            logger.info("✅ Limpieza diaria completada")
            
        except Exception as e:
            logger.error(f"Error en cleanup_task: {e}")

    async def send_reset_alert(self, user_id: str, guild_id: str, server_name: str, 
                             reset_time: str, timezone: str, minutes_until: int) -> bool:
        """Enviar alerta de reinicio a un usuario específico"""
        try:
            # Obtener guild y usuario
            guild = self.get_guild(int(guild_id))
            if not guild:
                logger.warning(f"Guild {guild_id} no encontrado para alerta de reset")
                return False
            
            user = guild.get_member(int(user_id))
            if not user:
                logger.warning(f"Usuario {user_id} no encontrado en guild {guild_id}")
                return False
            
            # Crear embed de alerta
            embed = discord.Embed(
                title="🔔 Alerta de Reinicio de Servidor",
                description=f"El servidor **{server_name}** se reiniciará pronto",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="⏰ Tiempo Restante",
                value=f"**{minutes_until} minutos**",
                inline=True
            )
            
            embed.add_field(
                name="🕐 Hora de Reinicio",
                value=f"{reset_time} ({timezone})",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Servidor",
                value=server_name,
                inline=True
            )
            
            embed.add_field(
                name="💡 Recomendación",
                value="Prepárate para el reinicio:\n• Guarda tu progreso\n• Ve a una zona segura\n• Desconéctate antes del reinicio",
                inline=False
            )
            
            embed.set_footer(text=f"Alerta configurada para {minutes_until} min antes • {guild.name}")
            embed.timestamp = datetime.now()
            
            # Enviar DM al usuario
            try:
                await user.send(embed=embed)
                logger.info(f"Alerta de reinicio enviada a {user.display_name} para {server_name}")
                return True
            except discord.Forbidden:
                # Si no se puede enviar DM, intentar enviar en el canal general del servidor
                try:
                    general_channel = discord.utils.get(guild.text_channels, name='general') or guild.text_channels[0]
                    if general_channel:
                        await general_channel.send(f"{user.mention}", embed=embed)
                        logger.info(f"Alerta de reinicio enviada en canal {general_channel.name} para {user.display_name}")
                        return True
                except:
                    logger.warning(f"No se pudo enviar alerta de reinicio a {user.display_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error enviando alerta de reinicio: {e}")
            return False

    async def send_notification(self, notification):
        """Enviar notificación a los canales configurados"""
        try:
            guild_id = notification["discord_guild_id"]
            guild = self.get_guild(int(guild_id))
            if not guild:
                logger.error(f"Guild {guild_id} no encontrado")
                return
            
            # Buscar configuraciones de notificación para este bunker
            from premium_exclusive_commands import get_notification_configs
            configs = await get_notification_configs(guild_id, notification["server_name"], notification["sector"])
            
            if not configs:
                logger.info(f"No hay configuraciones de notificación para {notification['sector']} en {notification['server_name']}")
                return
            
            # Crear embed de notificación
            color_map = {
                "expiring": 0xff9500,  # Naranja
                "expired": 0xff0000,   # Rojo
                "new": 0x00ff00       # Verde
            }
            
            type_map = {
                "expiring": "⏰ Expira en 30 minutos",
                "expired": "🔴 ¡EXPIRADO!",
                "new": "🆕 Nuevo bunker registrado"
            }
            
            embed = discord.Embed(
                title=type_map.get(notification["type"], "🔔 Notificación"),
                description=f"**Bunker {notification['sector']}** en **{notification['server_name']}**",
                color=color_map.get(notification["type"], 0x0099ff)
            )
            
            # Enviar a cada configuración
            for config in configs:
                try:
                    # Determinar automáticamente si usar DM personal basado en quién creó la configuración
                    config_creator_id = config.get("created_by")
                    use_personal_dm = self.should_use_personal_dm(config_creator_id, guild)
                    
                    # Si debe usar DM personal, enviar solo al registrador
                    if use_personal_dm:
                        # Enviar DM solo si esta configuración es del usuario que registró el bunker
                        if config_creator_id == notification.get("registered_by_id"):
                            try:
                                user = await self.fetch_user(int(notification["registered_by_id"]))
                                if user:
                                    dm_embed = embed.copy()
                                    dm_embed.set_footer(text="💎 Notificación Premium Personal")
                                    await user.send(embed=dm_embed)
                                    logger.info(f"DM automático enviado a {user.display_name} para {notification['sector']}")
                            except Exception as e:
                                logger.error(f"Error enviando DM automático a usuario {notification.get('registered_by_id')}: {e}")
                    else:
                        # Owner del bot o del Discord: usar canal público
                        channel = guild.get_channel(int(config["channel_id"]))
                        if channel:
                            content = f"<@&{config['role_id']}>" if config["role_id"] else None
                            await channel.send(content=content, embed=embed)
                            logger.info(f"Notificación pública enviada a #{channel.name} para {notification['sector']}")
                        else:
                            logger.error(f"Canal {config['channel_id']} no encontrado")
                except Exception as e:
                    logger.error(f"Error enviando notificación: {e}")
                    
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")

bot = BunkerBotV2()

# === AUTOCOMPLETADO ===

async def server_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocompletado para nombres de servidores del Discord guild actual"""
    try:
        # Verificar que la interacción sea válida y no haya expirado
        if not interaction.guild or not interaction.response:
            return [app_commands.Choice(name="Default", value="Default")]
        
        guild_id = str(interaction.guild.id)
        
        # Usar un timeout muy corto para evitar problemas de timing
        import asyncio
        async def get_servers_with_timeout():
            return await bot.db.get_servers(guild_id)
        
        try:
            # Timeout de 1 segundo para evitar interacciones expiradas
            servers = await asyncio.wait_for(get_servers_with_timeout(), timeout=1.0)
        except (asyncio.TimeoutError, Exception):
            # Si hay cualquier error, usar valores por defecto
            return [
                app_commands.Choice(name="Default", value="Default"),
                app_commands.Choice(name="convictos", value="convictos")
            ]
        
        # Filtrar por texto actual
        if current:
            filtered_servers = [
                s for s in servers 
                if current.lower() in s["name"].lower()
            ][:25]
        else:
            filtered_servers = servers[:25]
        
        # Si no hay servidores, devolver opciones por defecto
        if not filtered_servers:
            return [
                app_commands.Choice(name="Default", value="Default"),
                app_commands.Choice(name="convictos", value="convictos")
            ]
        
        return [
            app_commands.Choice(name=server["name"], value=server["name"])
            for server in filtered_servers
        ]
        
    except Exception as e:
        # Log del error pero sin emojis para evitar UnicodeEncodeError
        logger.error(f"Error en server_autocomplete: {e}")
        # Devolver opciones básicas en caso de error
        return [
            app_commands.Choice(name="Default", value="Default"),
            app_commands.Choice(name="convictos", value="convictos")
        ]

async def sector_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocompletado para sectores de bunkers"""
    try:
        sectors = ["D1", "C4", "A1", "A3"]
        
        # Filtrar por texto actual si se proporciona
        if current:
            filtered_sectors = [s for s in sectors if current.upper() in s]
        else:
            filtered_sectors = sectors
        
        # Asegurar que siempre hay al menos una opción
        if not filtered_sectors:
            filtered_sectors = ["D1"]  # Default fallback
        
        return [
            app_commands.Choice(name=f"Sector {sector}", value=sector)
            for sector in filtered_sectors
        ]
        
    except Exception as e:
        logger.error(f"Error en sector_autocomplete: {e}")
        # Fallback básico en caso de error
        return [
            app_commands.Choice(name="Sector D1", value="D1"),
            app_commands.Choice(name="Sector C4", value="C4"),
            app_commands.Choice(name="Sector A1", value="A1"),
            app_commands.Choice(name="Sector A3", value="A3")
        ]

# === COMANDOS DE GESTIÓN DE SERVIDORES ===

@bot.tree.command(name="ba_add_server", description="Agregar un nuevo servidor para tracking de bunkers")
@check_limits("servers")
async def add_server(interaction: discord.Interaction, 
                    name: str, 
                    description: str = ""):
    """Agregar un servidor nuevo al Discord guild actual"""
    # El decorador @check_limits ya maneja defer()
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        success = await bot.db.add_server(name, description, str(interaction.user), guild_id)
        
        if success:
            embed = discord.Embed(
                title="✅ Servidor Agregado",
                description=f"El servidor **{name}** ha sido agregado correctamente a este Discord.",
                color=0x00ff00
            )
            if description:
                embed.add_field(name="📝 Descripción", value=description, inline=False)
            embed.add_field(name="👤 Creado por", value=interaction.user.mention, inline=True)
            embed.add_field(name="🗂️ Bunkers", value="D1, C4, A1, A3", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudo agregar el servidor **{name}**. Puede que ya exista en este Discord.",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en add_server: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al agregar el servidor.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ba_remove_server", description="Eliminar un servidor y todos sus bunkers")
@app_commands.autocomplete(server=server_autocomplete)
async def remove_server(interaction: discord.Interaction, server: str):
    """Eliminar un servidor del Discord guild actual"""
    
    try:
        if server == "Default":
            embed = discord.Embed(
                title="❌ Operación no permitida",
                description="No se puede eliminar el servidor **Default**.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        success = await bot.db.remove_server(server, guild_id)
        
        if success:
            embed = discord.Embed(
                title="✅ Servidor Eliminado",
                description=f"El servidor **{server}** y todos sus bunkers han sido eliminados de este Discord.",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudo eliminar el servidor **{server}**. Puede que no exista en este Discord.",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en remove_server: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al eliminar el servidor.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ba_list_servers", description="Listar todos los servidores disponibles")
async def list_servers(interaction: discord.Interaction):
    """Listar servidores disponibles en este Discord guild"""
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        servers = await bot.db.get_servers(guild_id)
        
        if not servers:
            embed = discord.Embed(
                title="📋 Servidores",
                description="No hay servidores registrados en este Discord. Usa `/ba_add_server` para agregar uno.",
                color=0x808080
            )
        else:
            embed = discord.Embed(
                title="📋 Servidores Disponibles",
                description=f"Total: {len(servers)} servidor(es)",
                color=0x0099ff
            )
            
            for server in servers:
                server_info = f"**Creado por:** {server['created_by'] or 'Sistema'}\n"
                if server['description']:
                    server_info += f"**Descripción:** {server['description']}\n"
                server_info += f"**Fecha:** {server['created_at'][:10] if server['created_at'] else 'N/A'}"
                
                embed.add_field(
                    name=f"🖥️ {server['name']}",
                    value=server_info,
                    inline=True
                )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en list_servers: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al obtener la lista de servidores.",
            color=0xff0000
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)

# === COMANDOS DE BUNKERS (MODIFICADOS) ===

@bot.tree.command(name="ba_register_bunker", description="Registrar tiempo de expiración de un bunker")
@app_commands.autocomplete(sector=sector_autocomplete, server=server_autocomplete)
@app_commands.describe(
    sector="Sector del bunker (D1, C4, A1, A3)",
    hours="Horas hasta la apertura (OBLIGATORIO)",
    server="Servidor donde está el bunker (OBLIGATORIO)",
    minutes="Minutos adicionales (opcional, 0-59)"
)
@check_limits("bunkers")
async def register_bunker(interaction: discord.Interaction, 
                         sector: str, 
                         hours: int, 
                         server: str,
                         minutes: int = 0):
    """Registrar el tiempo de expiración de un bunker en este Discord guild"""
    # El decorador @check_limits ya maneja defer()
    
    try:
        # === VALIDACIONES OBLIGATORIAS ===
        
        # Validar que se proporcione un sector válido
        if not sector or sector.strip() == "":
            embed = discord.Embed(
                title="❌ Sector requerido",
                description="Debes especificar un sector válido (D1, C4, A1, A3)",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            return
        
        # Validar que se proporcione un servidor
        if not server or server.strip() == "":
            embed = discord.Embed(
                title="❌ Servidor requerido",
                description="Debes especificar un servidor válido",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            return
        
        # Validar que se proporcionen horas válidas (no puede ser 0 horas y 0 minutos)
        if hours == 0 and minutes == 0:
            embed = discord.Embed(
                title="❌ Tiempo requerido",
                description="El tiempo debe ser mayor a 0. Especifica al menos 1 minuto o 1 hora.",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            return
        
        # Validar sector permitido
        if sector.upper() not in ["D1", "C4", "A1", "A3"]:
            embed = discord.Embed(
                title="❌ Sector inválido",
                description="El sector debe ser uno de: **D1**, **C4**, **A1**, **A3**",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            return

        # Validar rango de tiempo
        if hours < 0 or hours > 200 or minutes < 0 or minutes >= 60:
            embed = discord.Embed(
                title="❌ Tiempo inválido",
                description="Las horas deben estar entre 0-200 y los minutos entre 0-59",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            return

        sector = sector.upper()
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        success = await bot.db.register_bunker_time(
            sector, hours, minutes, str(interaction.user), guild_id, str(interaction.user.id), server
        )
        
        if success:
            # Incrementar contador de uso diario para plan gratuito
            subscription = await subscription_manager.get_subscription(guild_id)
            if subscription['plan_type'] == 'free':
                await bot.db.increment_daily_usage(guild_id, str(interaction.user.id))
            
            current_time = datetime.now()
            expiry_time = current_time + timedelta(hours=hours, minutes=minutes)
            
            embed = discord.Embed(
                title="✅ Bunker Registrado",
                description=f"**Bunker Abandonado {sector}** registrado correctamente en **{server}**",
                color=0x00ff00
            )
            embed.add_field(name="🖥️ Servidor", value=server, inline=True)
            embed.add_field(name="⏰ Tiempo configurado", value=f"{hours}h {minutes}m", inline=True)
            embed.add_field(name="🗓️ Apertura", value=f"<t:{int(expiry_time.timestamp())}:F>", inline=False)
            embed.add_field(name="👤 Registrado por", value=interaction.user.mention, inline=True)
            embed.set_footer(text="El bunker se abrirá cuando el tiempo llegue a 0")
            
            # Crear notificaciones programadas
            user_id = str(interaction.user.id)
            await bot.db.create_notification(sector, server, guild_id, expiry_time - timedelta(minutes=30), "expiring", user_id)  # 30 min antes
            await bot.db.create_notification(sector, server, guild_id, expiry_time, "expired", user_id)  # Cuando expire
            await bot.db.create_notification(sector, server, guild_id, current_time, "new", user_id)  # Inmediatamente (nuevo bunker)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo registrar el bunker",
                color=0xff0000
            )
        
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en register_bunker: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al registrar el bunker",
            color=0xff0000
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)

@bot.tree.command(name="ba_check_bunker", description="Verificar estado de un bunker específico")
@app_commands.autocomplete(sector=sector_autocomplete, server=server_autocomplete)
async def check_bunker(interaction: discord.Interaction, 
                      sector: str, 
                      server: str = "Default"):
    """Verificar el estado de un bunker específico"""
    
    try:
        if sector.upper() not in ["D1", "C4", "A1", "A3"]:
            embed = discord.Embed(
                title="❌ Sector inválido",
                description="El sector debe ser uno de: D1, C4, A1, A3",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return

        sector = sector.upper()
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        status = await bot.db.get_bunker_status(sector, guild_id, server)
        
        if not status:
            embed = discord.Embed(
                title="❌ Bunker no encontrado",
                description=f"No se encontró el bunker {sector} en el servidor {server}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return

        # Crear embed según el estado
        if status["status"] == "closed":
            color = 0xff9900  # Naranja
            status_icon = "🔒"
            embed = discord.Embed(
                title=f"{status_icon} {status['name']} - {status['status_text']}",
                description="El bunker está cerrado y aún no se puede abrir",
                color=color
            )
            embed.add_field(name="⏳ Tiempo restante", value=status["time_remaining"], inline=True)
            embed.add_field(name="🗓️ Apertura", value=f"<t:{int(status['expiry_time'].timestamp())}:F>", inline=False)
            
        elif status["status"] == "active":
            color = 0x00ff00  # Verde
            status_icon = "🟢"
            embed = discord.Embed(
                title=f"{status_icon} {status['name']} - {status['status_text']}",
                description="¡El bunker está ABIERTO! Puedes entrar ahora",
                color=color
            )
            embed.add_field(name="⏱️ Tiempo restante abierto", value=status["time_remaining"], inline=True)
            embed.add_field(name="🕐 Abierto desde hace", value=status.get("active_since", "N/A"), inline=True)
            embed.add_field(name="🗓️ Se cerrará", value=f"<t:{int(status['final_expiry_time'].timestamp())}:F>", inline=False)
            
        elif status["status"] == "expired":
            color = 0xff0000  # Rojo
            status_icon = "🔴"
            embed = discord.Embed(
                title=f"{status_icon} {status['name']} - {status['status_text']}",
                description="El bunker está cerrado permanentemente",
                color=color
            )
            embed.add_field(name="❌ Estado", value="EXPIRADO", inline=True)
            embed.add_field(name="🕐 Expirado desde hace", value=status.get("expired_since", "N/A"), inline=True)
            
        else:
            color = 0x808080  # Gris
            status_icon = "❓"
            embed = discord.Embed(
                title=f"{status_icon} {status['name']} - SIN REGISTRO",
                description="No hay información de tiempo registrada",
                color=color
            )

        # Información común
        embed.add_field(name="🖥️ Servidor", value=server, inline=True)
        embed.add_field(name="📍 Sector", value=sector, inline=True)
        
        if status.get("registered_by"):
            embed.add_field(name="👤 Último registro", value=status["registered_by"], inline=True)
        
        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en check_bunker: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al verificar el bunker",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ba_status_all", description="Ver estado de todos los bunkers")
@app_commands.autocomplete(server=server_autocomplete)
async def status_all(interaction: discord.Interaction, server: str = "Default"):
    """Ver el estado de todos los bunkers de un servidor en este Discord guild"""
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        bunkers = await bot.db.get_all_bunkers_status(guild_id, server)
        
        if not bunkers:
            embed = discord.Embed(
                title="❌ Sin datos",
                description=f"No se encontraron bunkers en el servidor {server} de este Discord. ¿Necesitas crear el servidor primero?",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=f"📋 Estado de Bunkers - {server}",
            description="Estado actual de todos los bunkers abandonados",
            color=0x0099ff
        )

        for bunker in bunkers:
            # Determinar icono y color según estado
            if bunker["status"] == "closed":
                status_icon = "🔒"
                status_info = f"**CERRADO** - {bunker['time_remaining']}"
            elif bunker["status"] == "active":
                status_icon = "🟢"
                status_info = f"**ACTIVO** - {bunker['time_remaining']} restantes"
            elif bunker["status"] == "expired":
                status_icon = "🔴"
                status_info = f"**EXPIRADO** - {bunker.get('expired_since', 'N/A')}"
            else:
                status_icon = "❓"
                status_info = "**SIN REGISTRO**"
            
            embed.add_field(
                name=f"{status_icon} Sector {bunker['sector']}",
                value=status_info,
                inline=True
            )

        embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en status_all: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al obtener el estado de los bunkers",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

# === COMANDO DE AYUDA ESENCIAL ===

@bot.tree.command(name="ba_help", description="Guía básica del bot")
async def help_command(interaction: discord.Interaction):
    """Mostrar ayuda esencial del bot"""
    
    try:
        # Defer para evitar timeout
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="🤖 SCUM Bunker Timer - Guía Básica",
            description="Los 3 comandos esenciales para empezar",
            color=0x00ff00
        )
        
        # Paso 1: Agregar servidor
        embed.add_field(
            name="1️⃣ Agregar Servidor",
            value="`/ba_add_server name:Mi-Servidor`\nAgregar tu servidor SCUM al bot",
            inline=False
        )
        
        # Paso 2: Registrar bunker
        embed.add_field(
            name="2️⃣ Registrar Bunker",
            value="`/ba_register_bunker sector:D1 hours:5`\nRegistrar cuando encontraste un bunker cerrado",
            inline=False
        )
        
        # Paso 3: Verificar bunker
        embed.add_field(
            name="3️⃣ Verificar Estado",
            value="`/ba_check_bunker sector:D1`\nVer si el bunker ya está abierto",
            inline=False
        )
        
        # Info adicional
        embed.add_field(
            name="📍 Sectores",
            value="D1, C4, A1, A3",
            inline=True
        )
        
        embed.add_field(
            name="🔔 Notificaciones",
            value="`/ba_reset_alerts`\nRecibir alertas de reinicio del servidor",
            inline=True
        )
        
        embed.add_field(
            name="📖 Guía Completa",
            value="[Ver guía detallada](https://scum-bunker-timer.onrender.com/guide.html) 📚",
            inline=True
        )
        
        embed.set_footer(text="¿Necesitas más ayuda? Usa el enlace de la guía completa")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en help_command: {e}")
        try:
            # La interacción ya fue deferida, usar followup
            await interaction.followup.send("❌ Error mostrando ayuda", ephemeral=True)
        except discord.NotFound:
            logger.warning("Interacción no encontrada al enviar mensaje de error")
        except discord.HTTPException as http_error:
            logger.warning(f"Error HTTP al enviar mensaje de error: {http_error}")
        except Exception as follow_error:
            logger.error(f"Error enviando mensaje de error: {follow_error}")

@bot.tree.command(name="ba_my_usage", description="Ver tu uso diario de bunkers")
async def my_usage_command(interaction: discord.Interaction):
    """Ver el uso diario personal"""
    try:
        # Defer para evitar timeout
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        user_id = str(interaction.user.id)
        
        # Obtener suscripción del guild
        subscription = await subscription_manager.get_subscription(guild_id)
        
        # Obtener uso diario
        daily_usage = await bot.db.check_daily_usage(guild_id, user_id)
        
        # Obtener estadísticas de la semana
        weekly_stats = await bot.db.get_daily_usage_stats(guild_id, user_id, 7)
        
        embed = discord.Embed(
            title="📊 Mi Estado de Uso",
            description=f"Estado del servidor para {interaction.user.display_name}",
            color=0x3498db if subscription['plan_type'] == 'premium' else 0x95a5a6
        )
        
        # Plan actual
        plan_emoji = "💎" if subscription['plan_type'] == 'premium' else "🆓"
        plan_name = "Premium" if subscription['plan_type'] == 'premium' else "Gratuito"
        
        embed.add_field(
            name=f"{plan_emoji} Plan Actual",
            value=f"**{plan_name}**",
            inline=True
        )
        
        # Uso actual
        if subscription['plan_type'] == 'free':
            # Para plan gratuito, verificar si el servidor tiene bunker activo
            from database_v2 import BunkerDatabaseV2
            db = BunkerDatabaseV2()
            server_limit = await db.check_server_bunker_limit(guild_id)
            
            if server_limit['has_active_bunker']:
                active = server_limit['active_bunker']
                if active['discord_user_id'] == user_id:
                    usage_text = f"✅ **Tu bunker está activo**\nSector {active['sector']} en {active['server_name']}"
                    reset_info = f"{active['expiry_time']}\n({active['hours_remaining']:.1f} horas restantes)"
                else:
                    usage_text = f"⏳ **Servidor ocupado**\nOtro usuario tiene un bunker activo"
                    reset_info = f"{active['expiry_time']}\n({active['hours_remaining']:.1f} horas restantes)"
            else:
                usage_text = "✅ **Disponible** - Puedes registrar un bunker"
                reset_info = "Disponible ahora"
        else:
            usage_text = "🚀 **Ilimitado**"
            reset_info = "N/A - Plan Premium"
        
        embed.add_field(
            name="⏱️ Estado Actual",
            value=usage_text,
            inline=True
        )
        
        # Próximo disponible (solo para plan gratuito)
        if subscription['plan_type'] == 'free':
            embed.add_field(
                name="🔄 Próximo Disponible", 
                value=reset_info,
                inline=True
            )
        
        # Estadísticas semanales
        if weekly_stats:
            total_bunkers = sum(stat['bunkers_registered'] for stat in weekly_stats)
            avg_daily = total_bunkers / len(weekly_stats) if weekly_stats else 0
            
            embed.add_field(
                name="📈 Última Semana",
                value=f"• **{total_bunkers}** bunkers registrados\n• **{avg_daily:.1f}** promedio diario",
                inline=False
            )
            
            # Gráfico simple de actividad
            activity_chart = "```\n"
            activity_chart += "Actividad últimos 7 días:\n"
            for stat in reversed(weekly_stats[-7:]):  # Últimos 7 días
                date_str = stat['date'][-5:]  # Solo MM-DD
                bars = "█" * stat['bunkers_registered'] + "░" * (3 - stat['bunkers_registered'])
                activity_chart += f"{date_str}: {bars} ({stat['bunkers_registered']})\n"
            activity_chart += "```"
            
            embed.add_field(
                name="📊 Gráfico de Actividad",
                value=activity_chart,
                inline=False
            )
        
        # Información adicional
        if subscription['plan_type'] == 'free':
            embed.add_field(
                name="💎 ¿Quieres más?",
                value="Actualiza a Premium para bunkers ilimitados\nUsa `/ba_suscripcion` para más información",
                inline=False
            )
        
        embed.set_footer(text=f"Servidor Discord | Plan {plan_name} | 1 bunker por servidor")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en my_usage_command: {e}")
        try:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Error obteniendo estadísticas de uso.",
                color=0xff0000
            )
            # La interacción ya fue deferida, usar followup
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except discord.NotFound:
            logger.warning("Interacción no encontrada al enviar mensaje de error")
        except discord.HTTPException as http_error:
            logger.warning(f"Error HTTP al enviar mensaje de error: {http_error}")
        except Exception as follow_error:
            logger.error(f"Error enviando mensaje de error: {follow_error}")

# === COMANDO SIMPLE DE SUSCRIPCIONES ===

@bot.tree.command(name="ba_suscripcion", description="Ver información sobre planes de suscripción")
async def subscription_info(interaction: discord.Interaction):
    """Comando simple de información de suscripciones"""
    try:
        # Defer para evitar timeout
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        
        # Obtener suscripción actual
        subscription = await subscription_manager.get_subscription(guild_id)
        plan = subscription.get('plan', 'free') if subscription else 'free'
        plan_name = "Gratuito" if plan == 'free' else "Premium"
        
        # Crear embed con la nueva lógica
        embed = discord.Embed(
            title="💎 Planes de Suscripción",
            description="Compara los planes disponibles para el bot SCUM Bunker Timer",
            color=0x9b59b6
        )
        
        # Plan Gratuito actualizado
        embed.add_field(
            name="🆓 Plan Gratuito",
            value="• **1 bunker activo por servidor Discord**\n• Solo 1 usuario puede registrar a la vez\n• Fomenta coordinación del equipo\n• Perfecto para clanes organizados",
            inline=True
        )
        
        # Plan Premium sin precio
        embed.add_field(
            name="⭐ Plan Premium",
            value="• **Bunkers ilimitados**\n• Múltiples usuarios simultáneos\n• Sin restricciones de tiempo\n• Estadísticas avanzadas",
            inline=True
        )
        
        # Comparación rápida
        embed.add_field(
            name="🎯 ¿Por qué 1 bunker por servidor?",
            value="Evita spam y fomenta que los equipos se coordinen. Un bunker bien gestionado es mejor que muchos desorganizados.",
            inline=False
        )
        
        # Plan actual
        embed.add_field(
            name="📊 Tu Plan Actual",
            value=f"**{plan_name}**",
            inline=True
        )
        
        # Información adicional
        if plan == 'free':
            embed.add_field(
                name="💡 Ventajas del Plan Gratuito",
                value="• Fomenta trabajo en equipo\n• Evita spam de bunkers\n• Un bunker bien coordinado\n• Perfecto para clanes organizados",
                inline=True
            )
        else:
            embed.add_field(
                name="🎉 Tienes Premium",
                value="• Acceso completo a todas las funciones\n• Sin limitaciones de tiempo\n• ¡Gracias por tu apoyo!",
                inline=True
            )
        
        embed.set_footer(text="Para upgrade contacta al administrador del bot • Sistema optimizado para SCUM")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en subscription_info: {e}")
        try:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Error obteniendo información de suscripción.",
                color=0xff0000
            )
            # La interacción ya fue deferida, usar followup
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except discord.NotFound:
            logger.warning("Interacción no encontrada al enviar mensaje de error")
        except discord.HTTPException as http_error:
            logger.warning(f"Error HTTP al enviar mensaje de error: {http_error}")
        except Exception as follow_error:
            logger.error(f"Error enviando mensaje de error: {follow_error}")
        await interaction.response.send_message(embed=embed)

# === COMANDO PÚBLICO DE ESTADO DEL BOT ===

@bot.tree.command(name="ba_bot_status", description="Ver el estado del bot en este servidor")
async def bot_status_command(interaction: discord.Interaction):
    """Comando público para ver el estado del bot específico del servidor"""
    try:
        # Defer para operaciones de base de datos
        await interaction.response.defer()
        
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        guild_name = interaction.guild.name if interaction.guild else "DM"
        
        # Obtener información del servidor
        subscription = await subscription_manager.get_subscription(guild_id)
        
        # Obtener estadísticas de bunkers del servidor
        server_bunker_stats = await get_server_bunker_stats(guild_id)
        
        # Calcular uptime
        if hasattr(bot, 'status_system'):
            uptime = datetime.now() - bot.status_system.start_time
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        else:
            uptime_str = "Desconocido"
        
        # Crear embed
        embed = discord.Embed(
            title=f"🤖 Estado del Bot - {guild_name}",
            description="Información del bot específica para este servidor",
            color=0x00ff00 if subscription['plan_type'] == 'premium' else 0x3498db
        )
        
        # Estado general del bot
        embed.add_field(
            name="🟢 Estado General",
            value=f"```yaml\nEstado: Online\nUptime: {uptime_str}\nPing: {round(bot.latency * 1000)}ms\nComandos: {len(bot.tree.get_commands())}```",
            inline=False
        )
        
        # Información de suscripción del servidor
        plan_name = "💎 Premium" if subscription['plan_type'] != 'free' else "🆓 Gratuito"
        plan_description = "Acceso completo" if subscription['plan_type'] != 'free' else "1 bunker activo por servidor"
        
        embed.add_field(
            name="📋 Plan de Suscripción",
            value=f"```yaml\nPlan: {subscription['plan_type'].title()}\nEstado: {subscription['status'].title()}\nLímite: {plan_description}```",
            inline=True
        )
        
        # Estadísticas de bunkers del servidor
        embed.add_field(
            name="🏠 Bunkers en este Servidor",
            value=f"```yaml\nTotal registrados: {server_bunker_stats['total']}\nActivos ahora: {server_bunker_stats['active']}\nRegistrados hoy: {server_bunker_stats['today']}\nServidores SCUM: {server_bunker_stats['scum_servers']}```",
            inline=True
        )
        
        # Actividad reciente
        if server_bunker_stats['last_activity']:
            embed.add_field(
                name="⏰ Última Actividad",
                value=f"```yaml\nÚltimo bunker: {server_bunker_stats['last_activity']}\nSector: {server_bunker_stats['last_sector']}\nServidor: {server_bunker_stats['last_server']}```",
                inline=False
            )
        else:
            embed.add_field(
                name="⏰ Actividad",
                value="```yaml\nÚltimo bunker: Sin actividad reciente\nSector: -\nServidor: -```",
                inline=False
            )
        
        # Información adicional según el plan
        if subscription['plan_type'] == 'free':
            embed.add_field(
                name="💡 Plan Gratuito",
                value="• Solo 1 bunker activo por servidor\n• Cooldown de 72 horas\n• Perfecto para coordinación de clan\n• Actualiza a Premium para más funciones",
                inline=False
            )
        else:
            embed.add_field(
                name="⭐ Premium Activo",
                value="• Bunkers ilimitados\n• Sin cooldowns\n• Todas las funciones desbloqueadas\n• ¡Gracias por tu apoyo!",
                inline=False
            )
        
        # Footer con información útil
        embed.set_footer(text=f"Servidor: {guild_name} • Usa /ba_help para comandos básicos")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en bot_status_command: {e}")
        try:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Error obteniendo estado del bot.",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
        except:
            try:
                await interaction.response.send_message("❌ Error obteniendo estado del bot.", ephemeral=True)
            except:
                pass

def is_bot_admin():
    """Decorator para verificar si el usuario es admin del bot"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Primero intentar desde variables de entorno (.env)
        admin_ids_env = os.getenv('BOT_ADMIN_IDS', '').split(',')
        admin_ids_from_env = [id.strip() for id in admin_ids_env if id.strip()]
        
        # Si no hay IDs en .env, usar config.py como respaldo
        if not admin_ids_from_env:
            from config import BOT_ADMIN_IDS
            admin_ids_from_config = [str(id) for id in BOT_ADMIN_IDS]
            admin_ids = admin_ids_from_config
        else:
            admin_ids = admin_ids_from_env
        
        user_id = str(interaction.user.id)
        is_admin = user_id in admin_ids
        return is_admin
    return app_commands.check(predicate)

# === COMANDO TEMPORAL PARA VERIFICAR ID ===
@bot.tree.command(name="mi_id", description="🔍 [OWNER] Mostrar tu ID de Discord")
@is_bot_admin()
async def mi_id_command(interaction: discord.Interaction):
    """Comando temporal para verificar ID de usuario"""
    embed = discord.Embed(
        title="🆔 Tu ID de Discord",
        description=f"**Tu ID es:** `{interaction.user.id}`",
        color=0x00ff00
    )
    embed.add_field(
        name="📋 Para configurar admin:",
        value=f"```python\nBOT_ADMIN_IDS = [{interaction.user.id}]```",
        inline=False
    )
    embed.add_field(
        name="📝 Instrucciones:",
        value="1. Copia el ID de arriba\n2. Actualiza `BOT_ADMIN_IDS` en `config.py`\n3. Reinicia el bot\n4. Prueba `/ba_admin_subs` otra vez",
        inline=False
    )
    embed.set_footer(text="⚠️ Este es un comando temporal para diagnosis")
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def get_server_bunker_stats(guild_id: str):
    """Obtener estadísticas de bunkers específicas del servidor"""
    try:
        # Total de bunkers registrados en este servidor
        total_query = "SELECT COUNT(*) FROM bunkers WHERE discord_guild_id = ?"
        async with bot.db.get_connection() as db:
            cursor = await db.execute(total_query, (guild_id,))
            total_result = await cursor.fetchone()
            total_bunkers = total_result[0] if total_result else 0
        
        # Bunkers activos en este servidor
        current_time = datetime.now()
        active_query = "SELECT COUNT(*) FROM bunkers WHERE discord_guild_id = ? AND expiry_time > ?"
        async with bot.db.get_connection() as db:
            cursor = await db.execute(active_query, (guild_id, current_time))
            active_result = await cursor.fetchone()
            active_bunkers = active_result[0] if active_result else 0
        
        # Bunkers registrados hoy en este servidor
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = "SELECT COUNT(*) FROM bunkers WHERE discord_guild_id = ? AND registered_time >= ?"
        async with bot.db.get_connection() as db:
            cursor = await db.execute(today_query, (guild_id, today_start))
            today_result = await cursor.fetchone()
            today_bunkers = today_result[0] if today_result else 0
        
        # Servidores SCUM únicos en este Discord
        servers_query = "SELECT COUNT(DISTINCT server_name) FROM bunkers WHERE discord_guild_id = ?"
        async with bot.db.get_connection() as db:
            cursor = await db.execute(servers_query, (guild_id,))
            servers_result = await cursor.fetchone()
            scum_servers = servers_result[0] if servers_result else 0
        
        # Última actividad
        last_activity_query = """
            SELECT sector, server_name, registered_time 
            FROM bunkers 
            WHERE discord_guild_id = ? 
            ORDER BY registered_time DESC 
            LIMIT 1
        """
        async with bot.db.get_connection() as db:
            cursor = await db.execute(last_activity_query, (guild_id,))
            last_result = await cursor.fetchone()
            
            if last_result:
                last_time = datetime.fromisoformat(last_result[2]) if isinstance(last_result[2], str) else last_result[2]
                time_diff = datetime.now() - last_time
                if time_diff.days > 0:
                    last_activity = f"Hace {time_diff.days} días"
                elif time_diff.seconds > 3600:
                    last_activity = f"Hace {time_diff.seconds//3600} horas"
                else:
                    last_activity = f"Hace {time_diff.seconds//60} minutos"
                last_sector = last_result[0]
                last_server = last_result[1]
            else:
                last_activity = None
                last_sector = None
                last_server = None
        
        return {
            'total': total_bunkers,
            'active': active_bunkers,
            'today': today_bunkers,
            'scum_servers': scum_servers,
            'last_activity': last_activity,
            'last_sector': last_sector,
            'last_server': last_server
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del servidor: {e}")
        return {
            'total': 0,
            'active': 0,
            'today': 0,
            'scum_servers': 0,
            'last_activity': None,
            'last_sector': None,
            'last_server': None
        }

# === COMANDOS ADMIN SIMPLES ===



@bot.tree.command(name="ba_admin_status", description="[ADMIN] Ver estado de suscripción del servidor")
@is_bot_admin()
async def admin_status(interaction: discord.Interaction):
    """Ver estado de suscripción del servidor actual"""
    
    try:
        # Respuesta rápida sin defer
        guild_id = str(interaction.guild.id)
        guild_name = interaction.guild.name
        subscription = await subscription_manager.get_subscription(guild_id)
        
        embed = discord.Embed(
            title="📊 Estado de Suscripción - Admin",
            color=0x3498db
        )
        
        # Información básica del servidor
        embed.add_field(name="🏰 Servidor", value=guild_name, inline=True)
        embed.add_field(name="📊 Miembros", value=f"{interaction.guild.member_count:,}", inline=True)
        embed.add_field(name="🆔 Guild ID", value=f"`{guild_id}`", inline=False)
        
        # Información de suscripción
        embed.add_field(name="📋 Plan", value=subscription['plan_type'].upper(), inline=True)
        embed.add_field(name="📈 Estado", value=subscription['status'].upper(), inline=True)
        embed.add_field(name="📅 Expira", value=subscription.get('expires_at', 'N/A'), inline=True)
        
        # Información adicional
        embed.add_field(name="💰 Límites", value=f"Bunkers: {subscription.get('max_bunkers', 'Ilimitado')}", inline=True)
        embed.add_field(name="⚙️ Bot Owner", value=f"<@{interaction.user.id}>", inline=True)
        embed.add_field(name="🤖 Bot ID", value=f"`{bot.user.id}`", inline=True)
        
        embed.set_footer(text="🔒 Este mensaje es solo visible para ti")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error en admin_status: {e}")
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_upgrade", description="[ADMIN] Dar premium al servidor actual")
@is_bot_admin()
async def admin_upgrade(interaction: discord.Interaction):
    """Dar premium al servidor actual"""
    
    try:
        await interaction.response.send_message("⏳ Procesando...", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        await subscription_manager.upgrade_subscription(guild_id, "premium")
        
        embed = discord.Embed(
            title="✅ Suscripción Actualizada",
            description=f"Servidor actualizado a plan **premium**",
            color=0x00ff00
        )
        
        await interaction.edit_original_response(content=None, embed=embed)
        
    except Exception as e:
        logger.error(f"Error en admin_upgrade: {e}")
        try:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_cancel", description="[ADMIN] Quitar premium del servidor actual")
@is_bot_admin()
async def admin_cancel(interaction: discord.Interaction):
    """Quitar premium del servidor actual"""
    
    try:
        await interaction.response.send_message("⏳ Procesando...", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        await subscription_manager.cancel_subscription(guild_id)
        
        embed = discord.Embed(
            title="✅ Suscripción Cancelada",
            description=f"Servidor devuelto a plan **gratuito**",
            color=0x00ff00
        )
        
        await interaction.edit_original_response(content=None, embed=embed)
        
    except Exception as e:
        logger.error(f"Error en admin_cancel: {e}")
        try:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_list", description="[ADMIN] Listar todas las suscripciones")
@is_bot_admin()
async def admin_list(interaction: discord.Interaction):
    """Listar todas las suscripciones"""
    
    try:
        await interaction.response.send_message("🔍 Cargando...", ephemeral=True)
        
        subscriptions = await subscription_manager.get_all_subscriptions()
        
        embed = discord.Embed(
            title="📊 Suscripciones",
            color=0x3498db
        )
        
        if not subscriptions:
            embed.add_field(name="📊 Estado", value="Sin suscripciones registradas", inline=False)
        else:
            free_count = len([s for s in subscriptions if s.get('plan_type') == 'free'])
            premium_count = len([s for s in subscriptions if s.get('plan_type') != 'free'])
            
            embed.add_field(name="📊 Totales", value=f"Gratuitos: {free_count}\nPremium: {premium_count}", inline=False)
            
            if premium_count > 0:
                premium_list = []
                for s in subscriptions:
                    if s.get('plan_type') != 'free':
                        guild_short = s.get('guild_id', 'N/A')[:8]
                        premium_list.append(f"• {guild_short}...")
                        if len(premium_list) >= 5:  # Limitar a 5
                            break
                
                if premium_list:
                    embed.add_field(name="💎 Premium", value="\n".join(premium_list), inline=False)
        
        await interaction.edit_original_response(content=None, embed=embed)
        
    except Exception as e:
        logger.error(f"Error en admin_list: {e}")
        try:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_setup_status", description="[ADMIN] Configurar canal de estado del bot")
@is_bot_admin()
async def admin_setup_status(interaction: discord.Interaction, channel: discord.TextChannel):
    """Configurar el canal de estado del bot"""
    
    try:
        await interaction.response.send_message("⚙️ Configurando canal de estado...", ephemeral=True)
        
        # Configurar el canal de estado
        if hasattr(bot, 'status_system'):
            # Guardar en base de datos para persistencia
            from taxi_database import taxi_db
            await taxi_db.save_channel_config(str(interaction.guild.id), "status", str(channel.id), str(interaction.user.id))
            
            # Configurar el canal
            await bot.status_system.setup_status_channel(channel.id)
            
            embed = discord.Embed(
                title="✅ Canal de Estado Configurado",
                description=f"Canal {channel.mention} configurado como canal de estado del bot.\n\n"
                           f"🔄 Se actualizará automáticamente cada 5 minutos\n"
                           f"📊 Mostrará estadísticas en tiempo real",
                color=0x00ff00
            )
            
            await interaction.edit_original_response(content=None, embed=embed)
        else:
            await interaction.edit_original_response(content="❌ Sistema de estado no disponible")
        
    except Exception as e:
        logger.error(f"Error en admin_setup_status: {e}")
        try:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_public_status", description="[ADMIN] Configurar canal de estado público simplificado")
@is_bot_admin()
async def admin_setup_public_status(interaction: discord.Interaction, channel: discord.TextChannel):
    """Configurar el canal de estado público simplificado"""
    
    try:
        await interaction.response.send_message("⚙️ Configurando canal de estado público...", ephemeral=True)
        
        # Configurar el canal de estado público
        if hasattr(bot, 'status_system'):
            await bot.status_system.setup_public_status_channel(channel.id)
            # Guardar en base de datos para persistencia
            from taxi_database import taxi_db
            await taxi_db.save_channel_config(str(interaction.guild.id), "public_status", str(channel.id))
            
            embed = discord.Embed(
                title="✅ Canal de Estado Público Configurado",
                description=f"Canal {channel.mention} configurado como canal de estado público del bot.\n\n"
                           f"📊 **Información que mostrará:**\n"
                           f"• Estado del bot (online, uptime, ping)\n"
                           f"• Estadísticas de bunkers globales\n"
                           f"• Información básica y simplificada\n\n"
                           f"🔄 Se actualizará automáticamente cada 5 minutos\n"
                           f"👥 Perfecto para que todos los usuarios vean el estado",
                color=0x00ff00
            )
            
            await interaction.edit_original_response(content=None, embed=embed)
        else:
            await interaction.edit_original_response(content="❌ Sistema de estado no disponible")
        
    except Exception as e:
        logger.error(f"Error en admin_setup_public_status: {e}")
        try:
            await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ba_admin_guide", description="[ADMIN] Obtener URL de la guía completa")
@is_bot_admin()
async def admin_guide(interaction: discord.Interaction):
    """Obtener la URL de la guía HTML"""
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Buscar el puerto del servidor web
        web_port = getattr(bot, '_web_port', None)
        
        if web_port:
            embed = discord.Embed(
                title="📚 Guía Completa del Bot",
                description=f"La guía completa con todos los **20 comandos** está disponible en:",
                color=0x3498db
            )
            
            embed.add_field(
                name="🔗 URLs Disponibles",
                value=f"• **Principal:** http://localhost:{web_port}\n"
                      f"• **Alternativa:** http://localhost:{web_port}/guide\n"
                      f"• **IP Local:** http://127.0.0.1:{web_port}",
                inline=False
            )
            
            embed.add_field(
                name="📋 Contenido de la Guía",
                value="• **14 comandos públicos** (para todos los usuarios)\n"
                      "• **2 comandos premium** (solo servidores premium)\n"
                      "• **Estados de bunkers** explicados\n"
                      "• **Comparación de planes** gratuito vs premium\n"
                      "• **Ejemplos de uso** y flujos de trabajo",
                inline=False
            )
            
            embed.add_field(
                name="💡 Información",
                value="• La guía se actualiza automáticamente\n"
                      "• Incluye todos los comandos excepto los de administración\n"
                      "• Accesible mientras el bot esté funcionando\n"
                      "• Diseño responsivo para cualquier dispositivo",
                inline=False
            )
            
            embed.set_footer(text="💡 Comparte estas URLs con administradores de Discord para que conozcan todas las funciones")
            
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Servidor Web No Disponible",
                description="El servidor web para la guía no está funcionando.",
                color=0xff0000
            )
            
            embed.add_field(
                name="📝 Archivo Local",
                value="La guía está disponible en el archivo `guide.html` del bot.\n"
                      "Puedes abrirlo directamente en cualquier navegador web.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en admin_guide: {e}")
        try:
            await interaction.followup.send("❌ Error obteniendo información de la guía.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Error interno del bot.", ephemeral=True)

@bot.tree.command(name="ba_admin_resync", description="[ADMIN] Forzar resincronización de comandos")
@is_bot_admin()
async def admin_resync(interaction: discord.Interaction):
    """Forzar resincronización de todos los comandos"""
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Contar comandos antes de sync
        total_commands = len([cmd for cmd in bot.tree.walk_commands()])
        logger.info(f"Comandos encontrados antes del resync: {total_commands}")
        
        # Mostrar detalles de comandos
        command_list = []
        for cmd in bot.tree.walk_commands():
            # Verificar si el comando tiene guild_id (algunos comandos pueden no tenerlo)
            guild_info = 'global'
            if hasattr(cmd, 'guild_id') and cmd.guild_id is not None:
                guild_info = f'guild:{cmd.guild_id}'
            command_list.append(f"• {cmd.name} ({guild_info})")
        
        embed = discord.Embed(
            title="🔄 Resincronizando Comandos",
            description=f"Encontrados **{total_commands}** comandos para sincronizar",
            color=0xffa500
        )
        
        if len('\n'.join(command_list)) < 1000:
            embed.add_field(
                name="📋 Comandos Detectados", 
                value='\n'.join(command_list[:20]) + ('\n...' if len(command_list) > 20 else ''),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
        # Realizar sincronización
        try:
            synced = await bot.tree.sync()
            
            # Respuesta de éxito
            embed = discord.Embed(
                title="✅ Sincronización Completada",
                description=f"Se sincronizaron **{len(synced)}** comandos exitosamente",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📊 Estadísticas",
                value=f"• Comandos detectados: {total_commands}\n• Comandos sincronizados: {len(synced)}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            logger.info(f"RESYNC MANUAL: {len(synced)} comandos sincronizados exitosamente")
            
        except Exception as sync_error:
            embed = discord.Embed(
                title="❌ Error en Sincronización",
                description=f"Error: {str(sync_error)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            logger.error(f"Error en resync manual: {sync_error}")
            
    except Exception as e:
        logger.error(f"Error en admin_resync: {e}")
        try:
            await interaction.followup.send("❌ Error ejecutando resincronización.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Error interno del bot.", ephemeral=True)

@bot.tree.command(name="ba_admin_debug_servers", description="[ADMIN] Debug: Ver servidores en la base de datos")
@is_bot_admin()
async def admin_debug_servers(interaction: discord.Interaction):
    """Debug: Ver qué servidores hay en la base de datos"""
    try:
        await interaction.response.defer(ephemeral=True)
        
        from server_database import server_db
        guild_id = str(interaction.guild.id)
        
        # Obtener servidores monitoreados
        servers = await server_db.get_monitored_servers(guild_id)
        
        embed = discord.Embed(
            title="🔍 Debug: Servidores en Base de Datos",
            description=f"Guild ID: `{guild_id}`",
            color=0x3498db
        )
        
        if not servers:
            embed.add_field(
                name="❌ No hay servidores",
                value="No se encontraron servidores monitoreados para esta guild",
                inline=False
            )
        else:
            embed.add_field(
                name=f"✅ Encontrados {len(servers)} servidores",
                value=f"Total: {len(servers)} servidores monitoreados",
                inline=False
            )
            
            for i, server in enumerate(servers[:5], 1):  # Mostrar máximo 5
                server_info = f"• **Nombre:** {server['server_name']}\n"
                server_info += f"• **IP:** {server['server_ip']}:{server['server_port']}\n"
                server_info += f"• **ID:** {server['server_id']}\n"
                server_info += f"• **Alertas:** {'✅' if server['alerts_enabled'] else '❌'}"
                
                embed.add_field(
                    name=f"🎮 Servidor #{i}",
                    value=server_info,
                    inline=True
                )
        
        # Verificar límites
        try:
            limits = await server_db.check_server_limit(guild_id)
            embed.add_field(
                name="📊 Límites",
                value=f"• **Máximo:** {limits['max_servers']}\n• **Restantes:** {limits['remaining']}",
                inline=False
            )
        except Exception as e:
            embed.add_field(
                name="⚠️ Error en límites",
                value=f"Error: {str(e)}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en admin_debug_servers: {e}")
        try:
            await interaction.followup.send(f"❌ Error en debug: {str(e)}", ephemeral=True)
        except:
            await interaction.response.send_message(f"❌ Error interno: {str(e)}", ephemeral=True)

# Manejador de errores para comandos admin
@admin_status.error
@admin_upgrade.error  
@admin_cancel.error
@admin_list.error
@admin_setup_status.error
@admin_guide.error
@admin_resync.error
@admin_debug_servers.error
@mi_id_command.error
async def admin_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Manejador de errores para comandos de administración"""
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
    else:
        logger.error(f"Error en comando admin: {error}")
        try:
            await interaction.response.send_message("❌ Error interno del bot.", ephemeral=True)
        except:
            pass

# === EVENTOS Y NOTIFICACIONES ===

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Manejo global de errores para app commands"""
    try:
        # Log del error específico
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.NotFound):
                logger.warning(f"Interacción no encontrada para comando: {interaction.command.name if interaction.command else 'unknown'}")
                return
            elif isinstance(original, discord.HTTPException):
                logger.warning(f"Error HTTP en comando {interaction.command.name if interaction.command else 'unknown'}: {original}")
                return
        
        # Para otros errores, intentar responder al usuario
        logger.error(f"Error en comando {interaction.command.name if interaction.command else 'unknown'}: {error}")
        
        try:
            error_message = "❌ Ocurrió un error inesperado. Por favor, inténtalo de nuevo."
            
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        except (discord.NotFound, discord.HTTPException):
            # Si no podemos responder, simplemente logeamos
            logger.warning("No se pudo enviar mensaje de error al usuario")
            
    except Exception as handler_error:
        logger.error(f"Error en el manejador de errores: {handler_error}")

# === SERVIDOR WEB PARA LA GUÍA ===

async def guide_handler(request):
    """Servir la guía HTML"""
    try:
        with open('guide.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="Guía no encontrada", status=404)

async def create_web_server():
    """Crear servidor web para la guía"""
    app = web.Application()
    app.router.add_get('/', guide_handler)
    app.router.add_get('/guide', guide_handler)
    
    # Encontrar un puerto disponible
    for port in range(8080, 8090):
        try:
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', port)
            await site.start()
            logger.info(f"📚 Guía HTML disponible en: http://localhost:{port}")
            logger.info(f"📚 También disponible en: http://localhost:{port}/guide")
            
            # Guardar puerto en el bot para uso posterior
            bot._web_port = port
            
            return runner, port
        except OSError:
            continue
    
    logger.warning("No se pudo encontrar un puerto disponible para el servidor web")
    return None, None

# === COMANDO DE SHUTDOWN SEGURO ===

@bot.tree.command(name="ba_admin_shutdown", description="[ADMIN] ⚠️ Apagar el bot de forma segura")
@is_bot_admin()
async def admin_shutdown(interaction: discord.Interaction):
    """Comando para apagar el bot de forma segura enviando notificaciones"""
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Confirmar la acción
        embed = discord.Embed(
            title="⚠️ Confirmación de Apagado",
            description="¿Estás seguro de que quieres apagar el bot?",
            color=0xff9900
        )
        
        embed.add_field(
            name="🔴 Acciones que se realizarán:",
            value="• Se enviarán notificaciones a canales de estado\n• Se cerrará el bot de forma segura\n• Se detendrán todas las tareas automáticas\n• Se limpiará el servidor web",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Tiempo estimado:",
            value="El proceso tomará aproximadamente 5-10 segundos",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Reinicio:",
            value="Tendrás que reiniciar manualmente el bot",
            inline=True
        )
        
        embed.set_footer(text="⚠️ Esta acción no se puede deshacer")
        
        # Crear vista con botones de confirmación
        view = ShutdownConfirmView()
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error en comando shutdown: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Error ejecutando comando de apagado: {str(e)}",
            color=discord.Color.red()
        )
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ShutdownConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)  # 30 segundos para confirmar

    @discord.ui.button(label="✅ Confirmar Apagado", style=discord.ButtonStyle.danger, emoji="🔴")
    async def confirm_shutdown(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar y ejecutar el apagado"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear embed de confirmación
            embed = discord.Embed(
                title="🔴 Iniciando Apagado Seguro",
                description="El bot se está apagando...",
                color=0xff0000
            )
            
            embed.add_field(
                name="📤 Enviando notificaciones",
                value="Se están enviando notificaciones a los canales de estado...",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Ejecutar apagado seguro
            logger.info(f"🔴 Apagado iniciado por comando de admin: {interaction.user.name}")
            await shutdown_handler()
            
        except Exception as e:
            logger.error(f"Error en shutdown confirm: {e}")
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, emoji="🚫")
    async def cancel_shutdown(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar el apagado"""
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="✅ Apagado Cancelado",
            description="El bot continúa funcionando normalmente",
            color=0x00ff00
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def on_timeout(self):
        """Cuando expira el tiempo de confirmación"""
        # Deshabilitar todos los botones
        for item in self.children:
            item.disabled = True

# === INICIAR BOT ===

async def shutdown_handler():
    """Manejador de apagado seguro"""
    logger.info("🔴 Iniciando apagado seguro del bot...")
    
    # Enviar notificaciones de apagado
    if hasattr(bot, 'status_system') and bot.status_system:
        try:
            await bot.status_system.send_shutdown_notification()
            logger.info("✅ Notificaciones de apagado enviadas")
        except Exception as e:
            logger.error(f"Error enviando notificaciones de apagado: {e}")
    
    # Cerrar el bot
    try:
        await bot.close()
        logger.info("✅ Bot cerrado correctamente")
    except Exception as e:
        logger.error(f"Error cerrando bot: {e}")

async def main():
    """Función principal con manejo de señales"""
    import signal
    
    # Intentar obtener token desde config.py primero, luego desde variables de entorno
    token = DISCORD_TOKEN or os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No se encontró DISCORD_TOKEN en config.py ni en las variables de entorno")
        return
    
    # Variables para el servidor web
    web_runner = None
    web_port = None
    
    # Configurar manejadores de señales para cierre seguro
    def signal_handler():
        logger.warning("🛑 Señal de interrupción recibida (Ctrl+C)")
        # Crear una tarea para el apagado seguro
        asyncio.create_task(shutdown_handler())
    
    # Registrar señales en sistemas que lo soportan
    try:
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        logger.info("✅ Manejadores de señales configurados")
    except Exception as e:
        logger.warning(f"No se pudieron configurar manejadores de señales: {e}")
    
    try:
        # Iniciar servidor web para la guía
        web_runner, web_port = await create_web_server()
        logger.info(f"✅ Servidor web iniciado en puerto {web_port}")
        
        # Iniciar bot de Discord
        logger.info("🚀 Iniciando bot de Discord...")
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.warning("🛑 Interrupción de teclado detectada")
        await shutdown_handler()
    except Exception as e:
        logger.error(f"❌ Error al iniciar el bot: {e}")
        await shutdown_handler()
    finally:
        # Limpiar servidor web si existe
        if web_runner:
            try:
                await web_runner.cleanup()
                logger.info("✅ Servidor web cerrado")
            except Exception as e:
                logger.error(f"Error cerrando servidor web: {e}")
        
        logger.info("🏁 Aplicación terminada")

if __name__ == "__main__":
    asyncio.run(main())
