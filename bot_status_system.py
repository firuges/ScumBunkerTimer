#!/usr/bin/env python3
"""
Sistema de Estado del Bot para Discord
Actualiza automáticamente un embed con el estado del bot
"""

import discord
from discord.ext import tasks
import asyncio
import psutil
import platform
from datetime import datetime, timedelta
import os
from database_v2 import BunkerDatabaseV2
from subscription_manager import subscription_manager

class BotStatusSystem:
    def __init__(self, bot):
        self.bot = bot
        self.status_channel_id = None
        self.status_message = None
        self.public_status_channel_id = None
        self.public_status_message = None
        self.start_time = datetime.now()
        self.db = BunkerDatabaseV2()
        
    async def setup_status_channel(self, channel_id: int):
        """Configurar el canal de estado"""
        self.status_channel_id = channel_id
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            # Limpiar mensajes anteriores del bot
            async for message in channel.history(limit=50):
                if message.author == self.bot.user:
                    await message.delete()
            
            # Crear mensaje inicial
            embed = await self.create_status_embed()
            self.status_message = await channel.send(embed=embed)
            
            # Iniciar actualizaciones automáticas
            if not self.update_status.is_running():
                self.update_status.start()
    
    async def setup_public_status_channel(self, channel_id: int):
        """Configurar el canal de estado público simplificado"""
        self.public_status_channel_id = channel_id
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            # Limpiar mensajes anteriores del bot
            async for message in channel.history(limit=50):
                if message.author == self.bot.user:
                    await message.delete()
            
            # Crear mensaje inicial público
            embed = await self.create_public_status_embed()
            self.public_status_message = await channel.send(embed=embed)
            
            # Iniciar actualizaciones automáticas si no está corriendo
            if not self.update_status.is_running():
                self.update_status.start()
    
    async def create_status_embed(self):
        """Crear embed con estado del bot"""
        
        # Obtener estadísticas
        guild_count = len(self.bot.guilds)
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        
        # Estadísticas de bunkers
        bunker_stats = await self.get_bunker_stats()
        
        # Estadísticas de suscripciones
        subscription_stats = await self.get_subscription_stats()
        
        # Estado del sistema
        system_stats = self.get_system_stats()
        
        # Uptime
        uptime = datetime.now() - self.start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        # Crear embed
        embed = discord.Embed(
            title="🤖 Estado del Bot - Scum Bunker Timer",
            color=0x00ff00,  # Verde = online
            timestamp=datetime.now()
        )
        
        # Estado general
        embed.add_field(
            name="🟢 Estado General",
            value=f"```yaml\nEstado: Online\nUptime: {uptime_str}\nPing: {round(self.bot.latency * 1000)}ms\nComandos: {len(self.bot.tree.get_commands())}```",
            inline=False
        )
        
        # Estadísticas de Discord
        embed.add_field(
            name="📊 Estadísticas Discord",
            value=f"```yaml\nServidores: {guild_count}\nUsuarios: {user_count:,}\nCanales: {len(list(self.bot.get_all_channels()))}```",
            inline=True
        )
        
        # Estadísticas de bunkers
        embed.add_field(
            name="🏠 Estadísticas Bunkers",
            value=f"```yaml\nTotal: {bunker_stats['total']}\nActivos: {bunker_stats['active']}\nExpirados: {bunker_stats['expired']}\nHoy: {bunker_stats['today']}```",
            inline=True
        )
        
        # Estadísticas de suscripciones
        embed.add_field(
            name="💎 Suscripciones",
            value=f"```yaml\nGratuitas: {subscription_stats['free']}\nPremium: {subscription_stats['premium']}\nTotal: {subscription_stats['total']}```",
            inline=True
        )
        
        # Estado del sistema
        embed.add_field(
            name="💻 Sistema",
            value=f"```yaml\nCPU: {system_stats['cpu']}%\nRAM: {system_stats['memory']}%\nPython: {system_stats['python']}\nOS: {system_stats['os']}```",
            inline=False
        )
        
        # Última actualización
        embed.set_footer(text="🔄 Actualizado automáticamente cada 5 minutos")
        
        return embed
    
    async def create_public_status_embed(self):
        """Crear embed público simplificado con estado del bot"""
        
        # Obtener estadísticas básicas
        guild_count = len(self.bot.guilds)
        
        # Estadísticas de bunkers por servidor
        servers_bunkers = await self.get_bunkers_by_server_status()
        
        # Uptime
        uptime = datetime.now() - self.start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        # Crear embed simplificado
        embed = discord.Embed(
            title="🤖 Scum Bunker Timer - Estado",
            color=0x00ff00,  # Verde = online
            timestamp=datetime.now()
        )
        
        # Estado del bot simplificado
        embed.add_field(
            name="🟢 Bot Online",
            value=f"```yaml\nUptime: {uptime_str}\nPing: {round(self.bot.latency * 1000)}ms\nServidores: {guild_count}```",
            inline=True
        )
        
        # Mostrar bunkers organizados por servidor
        if not servers_bunkers:
            embed.add_field(
                name="🏠 Bunkers Abandonados",
                value="```yaml\nSin bunkers registrados```",
                inline=True
            )
        elif len(servers_bunkers) == 1:
            # Solo un servidor - mostrar detallado
            server_name = list(servers_bunkers.keys())[0]
            bunkers = servers_bunkers[server_name]
            
            bunkers_text = f"Servidor: {server_name}\n"
            for sector in ["D1", "C4", "A1", "A3"]:
                if sector in bunkers:
                    status_emoji = {
                        "Registrado": "🔴",
                        "Activo": "🟢", 
                        "Expirado": "🟡",
                        "NoRegistrado": "⚫"
                    }.get(bunkers[sector]['status'], "⚫")
                    
                    bunkers_text += f"{sector}: {status_emoji} {bunkers[sector]['status']}\n"
            
            embed.add_field(
                name="🏠 Bunkers Abandonados",
                value=f"```yaml\n{bunkers_text.strip()}```",
                inline=True
            )
        else:
            # Múltiples servidores - mostrar compacto con todos
            bunkers_text = ""
            for server_name, bunkers in list(servers_bunkers.items())[:4]:  # Máximo 4 servidores
                bunkers_text += f"{server_name}:\n"
                server_status = ""
                for sector in ["D1", "C4", "A1", "A3"]:
                    if sector in bunkers:
                        status_emoji = {
                            "Registrado": "🔴",
                            "Activo": "🟢", 
                            "Expirado": "🟡",
                            "NoRegistrado": "⚫"
                        }.get(bunkers[sector]['status'], "⚫")
                        
                        server_status += f"{sector}:{status_emoji} "
                bunkers_text += f"{server_status.strip()}\n\n"
            
            if len(servers_bunkers) > 4:
                bunkers_text += f"+ {len(servers_bunkers) - 4} servidores más"
            
            embed.add_field(
                name="🏠 Bunkers Abandonados",
                value=f"```yaml\n{bunkers_text.strip()}```",
                inline=True
            )
        
        # Información básica
        embed.add_field(
            name="📊 Estado General",
            value="```yaml\nEstado: ✅ Funcionando\nComandos: Disponibles\nSistema: Estable```",
            inline=False
        )
        
        # Footer simplificado con leyenda
        embed.set_footer(text="🔴 Registrado • � Activo • 🟡 Expirado • ⚫ Sin datos • /ba_help para comandos")
        
        return embed
    
    async def get_bunker_stats(self):
        """Obtener estadísticas de bunkers"""
        try:
            total_bunkers = await self.db.get_total_bunkers_count()
            active_bunkers = await self.db.get_active_bunkers_count()
            expired_bunkers = total_bunkers - active_bunkers
            today_bunkers = await self.db.get_today_bunkers_count()
            
            return {
                'total': total_bunkers,
                'active': active_bunkers,
                'expired': expired_bunkers,
                'today': today_bunkers
            }
        except Exception as e:
            return {'total': 0, 'active': 0, 'expired': 0, 'today': 0}
    
    async def get_subscription_stats(self):
        """Obtener estadísticas de suscripciones"""
        try:
            subscriptions = await subscription_manager.get_all_subscriptions()
            free_count = len([s for s in subscriptions if s.get('plan_type') == 'free'])
            premium_count = len([s for s in subscriptions if s.get('plan_type') != 'free'])
            
            return {
                'free': free_count,
                'premium': premium_count,
                'total': len(subscriptions)
            }
        except Exception as e:
            return {'free': 0, 'premium': 0, 'total': 0}
    
    def get_system_stats(self):
        """Obtener estadísticas del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            python_version = platform.python_version()
            os_name = f"{platform.system()} {platform.release()}"
            
            return {
                'cpu': round(cpu_percent, 1),
                'memory': round(memory_percent, 1),
                'python': python_version,
                'os': os_name
            }
        except Exception as e:
            return {'cpu': 0, 'memory': 0, 'python': 'Unknown', 'os': 'Unknown'}
    
    @tasks.loop(minutes=5)
    async def update_status(self):
        """Actualizar el estado del bot cada 5 minutos"""
        
        # Actualizar canal de estado completo (admin)
        if self.status_message and self.status_channel_id:
            try:
                embed = await self.create_status_embed()
                await self.status_message.edit(embed=embed)
            except discord.NotFound:
                # Mensaje eliminado, recrear
                channel = self.bot.get_channel(self.status_channel_id)
                if channel:
                    embed = await self.create_status_embed()
                    self.status_message = await channel.send(embed=embed)
            except Exception as e:
                print(f"Error actualizando estado completo: {e}")
        
        # Actualizar canal de estado público simplificado
        if self.public_status_message and self.public_status_channel_id:
            try:
                embed = await self.create_public_status_embed()
                await self.public_status_message.edit(embed=embed)
            except discord.NotFound:
                # Mensaje eliminado, recrear
                channel = self.bot.get_channel(self.public_status_channel_id)
                if channel:
                    embed = await self.create_public_status_embed()
                    self.public_status_message = await channel.send(embed=embed)
            except Exception as e:
                print(f"Error actualizando estado público: {e}")
    
    @update_status.before_loop
    async def before_update_status(self):
        """Esperar a que el bot esté listo"""
        await self.bot.wait_until_ready()
    
    async def stop(self):
        """Detener el sistema de estado"""
        if self.update_status.is_running():
            self.update_status.stop()
    
    async def get_bunkers_individual_status(self):
        """Obtener estado individual de cada bunker globalmente"""
        try:
            return await self.db.get_all_bunkers_global_status()
        except Exception as e:
            return {
                'D1': {'status': 'NoRegistrado'},
                'C4': {'status': 'NoRegistrado'},
                'A1': {'status': 'NoRegistrado'},
                'A3': {'status': 'NoRegistrado'}
            }
    
    async def get_bunkers_by_server_status(self):
        """Obtener estado de bunkers organizados por servidor"""
        try:
            return await self.db.get_bunkers_by_server_status()
        except Exception as e:
            return {
                'Default': {
                    'D1': {'status': 'NoRegistrado'},
                    'C4': {'status': 'NoRegistrado'},
                    'A1': {'status': 'NoRegistrado'},
                    'A3': {'status': 'NoRegistrado'}
                }
            }

# Instancia global
bot_status_system = None

def setup_bot_status(bot):
    """Configurar el sistema de estado del bot"""
    global bot_status_system
    bot_status_system = BotStatusSystem(bot)
    return bot_status_system
