#!/usr/bin/env python3
"""
Script de diagnóstico para comandos Discord
"""

import discord
from discord.ext import commands
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True

class DiagnosticBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        logger.info(f'🤖 {self.user} conectado para diagnóstico!')
        logger.info(f'📊 Bot conectado en {len(self.guilds)} servidores')
        
        # Información de los guilds
        for guild in self.guilds:
            logger.info(f"🏢 Guild: {guild.name} (ID: {guild.id})")
            logger.info(f"   👥 Miembros: {guild.member_count}")
            
            # Verificar permisos del bot
            bot_member = guild.get_member(self.user.id)
            if bot_member:
                permissions = bot_member.guild_permissions
                logger.info(f"   🔑 Permisos importantes:")
                logger.info(f"      - send_messages: {permissions.send_messages}")
                logger.info(f"      - embed_links: {permissions.embed_links}")
                logger.info(f"      - administrator: {permissions.administrator}")
                logger.info(f"      - manage_messages: {permissions.manage_messages}")
                logger.info(f"      - read_message_history: {permissions.read_message_history}")
                logger.info(f"      - use_external_emojis: {permissions.use_external_emojis}")
                
                # Verificar si tiene permisos de aplicación
                logger.info(f"   📱 Permisos de aplicación:")
                logger.info(f"      - Bot en el servidor: ✅")
                logger.info(f"      - Roles del bot: {[role.name for role in bot_member.roles]}")
            
            # Verificar comandos registrados en este guild
            try:
                commands = await self.tree.fetch_commands(guild=guild)
                logger.info(f"   📋 Comandos en guild: {len(commands)}")
                for cmd in commands:
                    logger.info(f"      - {cmd.name}: {cmd.description}")
            except Exception as e:
                logger.error(f"   ❌ Error obteniendo comandos del guild: {e}")
        
        # Verificar comandos globales
        try:
            global_commands = await self.tree.fetch_commands()
            logger.info(f"🌐 Comandos globales: {len(global_commands)}")
            for cmd in global_commands:
                logger.info(f"   - {cmd.name}: {cmd.description}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo comandos globales: {e}")
        
        # Información de aplicación
        try:
            app_info = await self.application_info()
            logger.info(f"📱 Información de aplicación:")
            logger.info(f"   - Nombre: {app_info.name}")
            logger.info(f"   - ID: {app_info.id}")
            logger.info(f"   - Bot público: {app_info.bot_public}")
            logger.info(f"   - Require Code Grant: {app_info.bot_require_code_grant}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de aplicación: {e}")
        
        logger.info("✅ Diagnóstico completado!")
        await self.close()

async def run_diagnostic():
    """Ejecutar diagnóstico"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No se encontró DISCORD_TOKEN en las variables de entorno")
        return
    
    bot = DiagnosticBot()
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
