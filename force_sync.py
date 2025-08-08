#!/usr/bin/env python3
"""
Script para forzar la sincronización de comandos slash
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

class SyncBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        logger.info(f'{self.user} conectado a Discord!')
        logger.info(f'Bot conectado en {len(self.guilds)} servidores')
        
        # Limpiar comandos del guild primero
        for guild in self.guilds:
            logger.info(f"🧹 Limpiando comandos del guild: {guild.name}")
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)
        
        # Forzar sincronización global
        try:
            logger.info("🔄 Forzando sincronización global de comandos...")
            synced = await self.tree.sync()
            logger.info(f"✅ Sincronizados {len(synced)} comandos globalmente")
            
            # Esperar un momento para que se propaguen
            await asyncio.sleep(5)
            
            # Sincronizar por cada guild
            for guild in self.guilds:
                try:
                    logger.info(f"🔄 Sincronizando comandos para guild: {guild.name}")
                    guild_synced = await self.tree.sync(guild=guild)
                    logger.info(f"✅ Sincronizados {len(guild_synced)} comandos en {guild.name}")
                except Exception as e:
                    logger.error(f"❌ Error sincronizando en {guild.name}: {e}")
            
            logger.info("🎉 Sincronización completada!")
            logger.info("⏳ Los comandos pueden tardar hasta 1 hora en aparecer globalmente")
            logger.info("💡 En el servidor pueden aparecer inmediatamente")
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización: {e}")
        
        # Cerrar el bot después de la sincronización
        await self.close()

async def force_sync():
    """Forzar sincronización de comandos"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("No se encontró DISCORD_TOKEN en las variables de entorno")
        return
    
    bot = SyncBot()
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(force_sync())
            for guild in self.guilds:
                logger.info(f"Sincronizando comandos en {guild.name}...")
                guild_synced = await self.tree.sync(guild=guild)
                logger.info(f"Comandos en {guild.name}: {len(guild_synced)}")
                
                # Mostrar comandos sincronizados
                for cmd in guild_synced:
                    logger.info(f"  ✓ /{cmd.name} - {cmd.description}")
                    
        except Exception as e:
            logger.error(f"Error sincronizando: {e}")
        
        logger.info("Sincronización completada. Presiona Ctrl+C para salir.")

# Comandos de prueba
bot = SyncBot()

@bot.tree.command(name="test_sync", description="Comando de prueba para verificar sincronización")
async def test_sync(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Sincronización funcionando correctamente!")

@bot.tree.command(name="register_bunker", description="Registra el tiempo restante de un bunker")
async def register_bunker_simple(interaction: discord.Interaction, sector: str, hours: int, minutes: int = 0):
    await interaction.response.send_message(f"✅ Bunker {sector}: {hours}h {minutes}m registrado (versión de prueba)")

@bot.tree.command(name="check_bunker", description="Consulta el estado de bunkers")  
async def check_bunker_simple(interaction: discord.Interaction, sector: str = None):
    if sector:
        await interaction.response.send_message(f"🔍 Consultando bunker {sector} (versión de prueba)")
    else:
        await interaction.response.send_message("📊 Mostrando todos los bunkers (versión de prueba)")

async def main():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN no encontrado")
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
