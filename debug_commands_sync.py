#!/usr/bin/env python3
"""
Script de diagnóstico para verificar sincronización de comandos Discord
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from subscription_manager import subscription_manager
from premium_commands import setup_premium_commands
from premium_exclusive_commands import setup_premium_exclusive_commands

load_dotenv()

class DiagnosticBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        """Inicializa el bot y verifica comandos"""
        print("🔧 Iniciando diagnóstico...")
        
        # Inicializar suscripciones
        await subscription_manager.initialize()
        print("✅ Sistema de suscripciones inicializado")
        
        # Configurar comandos premium
        print("🔧 Configurando comandos premium...")
        setup_premium_commands(self)
        setup_premium_exclusive_commands(self)
        
        # Contar comandos
        total_commands = len([cmd for cmd in self.tree.walk_commands()])
        print(f"📊 Total de comandos registrados: {total_commands}")
        
        print("\n📋 Lista de todos los comandos:")
        for i, cmd in enumerate(self.tree.walk_commands(), 1):
            print(f"  {i}. /{cmd.name} - {cmd.description}")
        
        # Verificar comandos por guild específico
        guild_id = int(os.getenv('DISCORD_GUILD_ID', '0'))
        if guild_id and guild_id != 0:
            print(f"\n🎯 Verificando comandos para guild {guild_id}...")
            guild_commands = self.tree.get_commands(guild=discord.Object(id=guild_id))
            print(f"📊 Comandos específicos del guild: {len(guild_commands)}")
        
        print("\n🔄 Intentando sincronizar comandos...")
        try:
            # Sincronizar globalmente
            synced = await self.tree.sync()
            print(f"✅ Sincronizados {len(synced)} comandos globalmente")
            
            # Si hay guild específico, sincronizar también ahí
            if guild_id and guild_id != 0:
                guild = discord.Object(id=guild_id)
                synced_guild = await self.tree.sync(guild=guild)
                print(f"✅ Sincronizados {len(synced_guild)} comandos en guild {guild_id}")
                
        except Exception as e:
            print(f"❌ Error sincronizando: {e}")

    async def on_ready(self):
        print(f"\n🤖 Bot conectado como {self.user}")
        print(f"🌐 Conectado en {len(self.guilds)} servidores:")
        for guild in self.guilds:
            print(f"   - {guild.name} (ID: {guild.id})")
        
        print("\n⏱️  Esperando 5 segundos y cerrando...")
        await asyncio.sleep(5)
        await self.close()

async def main():
    bot = DiagnosticBot()
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ ERROR: DISCORD_TOKEN no encontrado en .env")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
