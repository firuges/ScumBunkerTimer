#!/usr/bin/env python3
"""
Test rápido para verificar si el bot arranca sin errores
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class TestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f"✅ Bot conectado: {self.user}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        for guild in self.guilds:
            print(f"   - {guild.name} (ID: {guild.id})")
        
        # Verificar comandos
        commands = [cmd for cmd in self.tree.walk_commands()]
        print(f"📊 Comandos registrados: {len(commands)}")
        
        # Intentar sincronizar
        try:
            synced = await self.tree.sync()
            print(f"✅ Sincronizados: {len(synced)} comandos")
        except Exception as e:
            print(f"❌ Error sync: {e}")
        
        await asyncio.sleep(3)
        await self.close()

    async def on_error(self, event, *args, **kwargs):
        print(f"❌ Error en evento {event}: {args}")

async def main():
    bot = TestBot()
    
    # Agregar un comando simple de prueba
    @bot.tree.command(name="test", description="Comando de prueba")
    async def test_command(interaction: discord.Interaction):
        await interaction.response.send_message("✅ Test OK")
    
    token = os.getenv('DISCORD_TOKEN')
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    asyncio.run(main())
