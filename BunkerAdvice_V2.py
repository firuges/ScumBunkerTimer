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
            for notification in notifications:
                await self.send_notification(notification)
                await self.db.mark_notification_sent(notification["id"])
        except Exception as e:
            logger.error(f"Error en notificaciones: {e}")

    async def send_notification(self, notification):
        """Enviar notificación a los canales configurados"""
        try:
            # Aquí puedes configurar el canal donde enviar notificaciones
            # Por ahora solo loguea
            logger.info(f"Notificación: {notification['type']} para bunker {notification['sector']} en servidor {notification['server_name']}")
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
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        servers = await bot.db.get_servers(guild_id)
        filtered_servers = [
            s for s in servers 
            if current.lower() in s["name"].lower()
        ][:25]  # Discord permite máximo 25 opciones
        
        return [
            app_commands.Choice(name=f"{server['name']}", value=server["name"])
            for server in filtered_servers
        ]
    except Exception as e:
        logger.error(f"Error en autocompletado de servidores: {e}")
        return [app_commands.Choice(name="Default", value="Default")]

async def sector_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocompletado para sectores de bunkers"""
    sectors = ["D1", "C4", "A1", "A3"]
    filtered_sectors = [s for s in sectors if current.upper() in s]
    
    return [
        app_commands.Choice(name=f"Sector {sector}", value=sector)
        for sector in filtered_sectors
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en add_server: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al agregar el servidor.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ba_remove_server", description="Eliminar un servidor y todos sus bunkers")
@app_commands.autocomplete(server=server_autocomplete)
async def remove_server(interaction: discord.Interaction, server: str):
    """Eliminar un servidor del Discord guild actual"""
    await interaction.response.defer()
    
    try:
        if server == "Default":
            embed = discord.Embed(
                title="❌ Operación no permitida",
                description="No se puede eliminar el servidor **Default**.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en remove_server: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al eliminar el servidor.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ba_list_servers", description="Listar todos los servidores disponibles")
async def list_servers(interaction: discord.Interaction):
    """Listar servidores disponibles en este Discord guild"""
    await interaction.response.defer()
    
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en list_servers: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al obtener la lista de servidores.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

# === COMANDOS DE BUNKERS (MODIFICADOS) ===

@bot.tree.command(name="ba_register_bunker", description="Registrar tiempo de expiración de un bunker")
@app_commands.autocomplete(sector=sector_autocomplete, server=server_autocomplete)
@check_limits("bunkers")
async def register_bunker(interaction: discord.Interaction, 
                         sector: str, 
                         hours: int, 
                         minutes: int = 0, 
                         server: str = "Default"):
    """Registrar el tiempo de expiración de un bunker en este Discord guild"""
    # El decorador @check_limits ya maneja defer()
    
    try:
        # Validaciones
        if sector.upper() not in ["D1", "C4", "A1", "A3"]:
            embed = discord.Embed(
                title="❌ Sector inválido",
                description="El sector debe ser uno de: D1, C4, A1, A3",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        if hours < 0 or hours > 200 or minutes < 0 or minutes >= 60:
            embed = discord.Embed(
                title="❌ Tiempo inválido",
                description="Las horas deben estar entre 0-200 y los minutos entre 0-59",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        sector = sector.upper()
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        success = await bot.db.register_bunker_time(
            sector, hours, minutes, str(interaction.user), guild_id, str(interaction.user.id), server
        )
        
        if success:
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
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo registrar el bunker",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en register_bunker: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al registrar el bunker",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ba_check_bunker", description="Verificar estado de un bunker específico")
@app_commands.autocomplete(sector=sector_autocomplete, server=server_autocomplete)
async def check_bunker(interaction: discord.Interaction, 
                      sector: str, 
                      server: str = "Default"):
    """Verificar el estado de un bunker específico"""
    await interaction.response.defer()
    
    try:
        if sector.upper() not in ["D1", "C4", "A1", "A3"]:
            embed = discord.Embed(
                title="❌ Sector inválido",
                description="El sector debe ser uno de: D1, C4, A1, A3",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
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
            await interaction.followup.send(embed=embed)
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en check_bunker: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al verificar el bunker",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="ba_status_all", description="Ver estado de todos los bunkers")
@app_commands.autocomplete(server=server_autocomplete)
async def status_all(interaction: discord.Interaction, server: str = "Default"):
    """Ver el estado de todos los bunkers de un servidor en este Discord guild"""
    await interaction.response.defer()
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        bunkers = await bot.db.get_all_bunkers_status(guild_id, server)
        
        if not bunkers:
            embed = discord.Embed(
                title="❌ Sin datos",
                description=f"No se encontraron bunkers en el servidor {server} de este Discord. ¿Necesitas crear el servidor primero?",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en status_all: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al obtener el estado de los bunkers",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

# === COMANDO DE AYUDA ===

@bot.tree.command(name="ba_help", description="Mostrar ayuda y comandos disponibles del bot")
async def help_command(interaction: discord.Interaction):
    """Mostrar ayuda completa del bot"""
    await interaction.response.defer()
    
    try:
        embed = discord.Embed(
            title="🤖 SCUM Bunker Bot V2 - Ayuda",
            description="Bot para gestionar timers de bunkers abandonados en SCUM con soporte multi-servidor",
            color=0x0099ff
        )
        
        # Comandos de servidores
        embed.add_field(
            name="🖥️ Gestión de Servidores",
            value=(
                "`/ba_add_server` - Agregar nuevo servidor SCUM\n"
                "`/ba_remove_server` - Eliminar servidor existente\n"
                "`/ba_list_servers` - Listar todos los servidores"
            ),
            inline=False
        )
        
        # Comandos de bunkers
        embed.add_field(
            name="🏗️ Gestión de Bunkers",
            value=(
                "`/ba_register_bunker` - Registrar tiempo de bunker\n"
                "`/ba_check_bunker` - Consultar estado de bunker\n"
                "`/ba_status_all` - Ver todos los bunkers de un servidor"
            ),
            inline=False
        )
        
        # Estados de bunkers
        embed.add_field(
            name="📊 Estados de Bunkers",
            value=(
                "🔒 **CERRADO** - Esperando apertura\n"
                "🟢 **ACTIVO** - Abierto (24h de acceso)\n"
                "🔴 **EXPIRADO** - Cerrado permanentemente\n"
                "❓ **SIN REGISTRO** - Sin información"
            ),
            inline=False
        )
        
        # Información adicional
        embed.add_field(
            name="💡 Consejos",
            value=(
                "• Usa autocompletado escribiendo para filtrar opciones\n"
                "• El servidor 'Default' es el principal\n"
                "• Los bunkers tienen una ventana de 24h cuando se abren\n"
                "• Todos los comandos incluyen parámetro opcional de servidor"
            ),
            inline=False
        )
        
        # Sectores disponibles
        embed.add_field(
            name="📍 Sectores Disponibles",
            value="D1, C4, A1, A3",
            inline=True
        )
        
        # Ejemplo de uso
        embed.add_field(
            name="📝 Ejemplo de Uso",
            value=(
                "1. `/ba_add_server name:Mi-Servidor`\n"
                "2. `/ba_register_bunker sector:D1 hours:5 server:Mi-Servidor`\n"
                "3. `/ba_check_bunker sector:D1 server:Mi-Servidor`"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name} | Bot V2.0.0")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en help_command: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al mostrar la ayuda.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

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
