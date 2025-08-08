#!/usr/bin/env python3
"""
Script simple para limpiar cache de comandos Discord
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class CleanBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f"✅ Conectado: {self.user}")
        
        # Limpiar comandos globales
        print("🧹 Limpiando comandos globales...")
        self.tree.clear_commands(guild=None)
        synced = await self.tree.sync()
        print(f"✅ Limpiados: {len(synced)} comandos")
        
        print("⏱️ Esperando 3 segundos...")
        await asyncio.sleep(3)
        await self.close()

async def main():
    bot = CleanBot()
    token = os.getenv('DISCORD_TOKEN')
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
