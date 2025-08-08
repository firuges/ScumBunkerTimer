#!/usr/bin/env python3
"""
Sincronizar comandos de Discord
"""

import discord
from discord.ext import commands
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        logger.info(f'Bot conectado: {self.user}')
        
        try:
            # Sincronizar globalmente
            synced = await self.tree.sync()
            logger.info(f'Sincronizados {len(synced)} comandos globalmente')
            
            # Sincronizar por servidor
            for guild in self.guilds:
                guild_synced = await self.tree.sync(guild=guild)
                logger.info(f'Sincronizados {len(guild_synced)} comandos en {guild.name}')
            
            logger.info('¡Sincronización completada!')
            
        except Exception as e:
            logger.error(f'Error: {e}')
        
        await self.close()

async def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('Token no encontrado')
        return
    
    bot = SyncBot()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
