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
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Importar configuración del bot
try:
    from config import BOT_CREATOR_ID
except ImportError:
    # ID del creador del bot (reemplazar con tu Discord User ID)
    BOT_CREATOR_ID = 123456789012345678  # CAMBIAR POR TU ID DE DISCORD

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
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
        
        # Configurar comandos premium
        setup_premium_commands(self)
        setup_premium_exclusive_commands(self)
        
        self.notification_task.start()
        
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
            synced = await self.tree.sync()
            logger.info(f"EXITO: Sincronizados {len(synced)} comandos con Discord")
        except Exception as e:
            logger.error(f"ERROR: Error sincronizando comandos: {e}")

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
        # Verificar que la interacción sea válida
        if not interaction.guild:
            return [app_commands.Choice(name="Default", value="Default")]
        
        guild_id = str(interaction.guild.id)
        
        # Usar un timeout corto para evitar problemas de timing
        import asyncio
        async def get_servers_with_timeout():
            return await bot.db.get_servers(guild_id)
        
        try:
            # Timeout de 2 segundos para evitar interacciones expiradas
            servers = await asyncio.wait_for(get_servers_with_timeout(), timeout=2.0)
        except asyncio.TimeoutError:
            # Si hay timeout, usar valores por defecto
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
        # Log del error pero no fallar
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
            name="� Guía Completa",
            value="[Ver guía detallada](https://scum-bunker-timer.onrender.com/guide.html) 📚",
            inline=True
        )
        
        embed.set_footer(text="¿Necesitas más ayuda? Usa el enlace de la guía completa")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en help_command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Error mostrando ayuda")
        else:
            await interaction.followup.send("❌ Error mostrando ayuda")

@bot.tree.command(name="ba_my_usage", description="Ver tu uso diario de bunkers")
async def my_usage_command(interaction: discord.Interaction):
    """Ver el uso diario personal"""
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        user_id = str(interaction.user.id)
        
        # Obtener suscripción del guild
        subscription = await subscription_manager.get_subscription(guild_id)
        
        # Obtener uso diario
        daily_usage = await bot.db.check_daily_usage(guild_id, user_id)
        
        # Obtener estadísticas de la semana
        weekly_stats = await bot.db.get_daily_usage_stats(guild_id, user_id, 7)
        
        embed = discord.Embed(
            title="📊 Mi Uso Diario",
            description=f"Estadísticas de uso para {interaction.user.display_name}",
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
        
        # Uso de hoy
        if subscription['plan_type'] == 'free':
            usage_text = f"**{daily_usage['bunkers_today']}/1** bunkers hoy"
            if daily_usage['can_register']:
                usage_text += "\n✅ Puedes registrar 1 bunker más"
            else:
                usage_text += "\n❌ Límite diario alcanzado"
        else:
            usage_text = "🚀 **Ilimitado**"
        
        embed.add_field(
            name="🗓️ Uso de Hoy",
            value=usage_text,
            inline=True
        )
        
        # Próximo reset (solo para plan gratuito)
        if subscription['plan_type'] == 'free':
            from datetime import time
            tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)
            embed.add_field(
                name="🔄 Próximo Reset",
                value=f"<t:{int(tomorrow.timestamp())}:R>",
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
                value="Actualiza a Premium para bunkers ilimitados\nUsa `/ba_subscription` para más información",
                inline=False
            )
        
        embed.set_footer(text=f"Uso monitoreado desde hoy | Plan {plan_name}")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en my_usage_command: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error obteniendo estadísticas de uso.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

# === COMANDO SIMPLE DE SUSCRIPCIONES ===

@bot.tree.command(name="ba_suscripcion", description="Ver información sobre planes de suscripción")
async def subscription_info(interaction: discord.Interaction):
    """Comando simple de información de suscripciones"""
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        
        # Obtener suscripción actual
        subscription = await subscription_manager.get_subscription(guild_id)
        plan = subscription.get('plan', 'free') if subscription else 'free'
        
        # Crear embed básico
        embed = discord.Embed(
            title="💎 Planes de Suscripción",
            description="Obtén acceso a funciones premium del bot",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="🆓 Plan Gratuito",
            value="• 5 bunkers por día\n• Comandos básicos\n• Soporte comunitario",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Premium - $5.99/mes",
            value="• 20 bunkers por día\n• Estadísticas avanzadas\n• Exportación de datos",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Enterprise - $15.99/mes",
            value="• 100 bunkers por día\n• Soporte prioritario\n• API personalizada",
            inline=True
        )
        
        embed.add_field(
            name="📊 Tu Plan Actual",
            value=f"**{plan.capitalize()}**",
            inline=False
        )
        
        embed.set_footer(text="Para upgrade contacta al administrador del bot")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en subscription_info: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error obteniendo información de suscripción.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

# === EVENTOS Y NOTIFICACIONES ===

# === INICIAR BOT ===

async def main():
    """Función principal"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No se encontró DISCORD_TOKEN en las variables de entorno")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
