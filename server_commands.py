#!/usr/bin/env python3
"""
Comandos de Discord para sistema de monitoreo de servidores SCUM
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Importar nuestros módulos
from server_monitor import server_monitor
from server_database import server_db
from premium_utils import check_premium_status

logger = logging.getLogger(__name__)

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("ServerCommands cog inicializado")
    
    async def _safe_send(self, ctx, embed=None, content=None, ephemeral=False):
        """Envía un mensaje de forma segura, manejando tanto slash commands como text commands"""
        try:
            # Para comandos híbridos, verificar si es una interacción (slash command) Y si tiene followup
            if (hasattr(ctx, 'interaction') and ctx.interaction and 
                hasattr(ctx, 'followup') and ctx.interaction.response.is_done()):
                # Es un slash command Y la interacción ya fue respondida
                if embed:
                    return await ctx.followup.send(embed=embed, ephemeral=ephemeral)
                else:
                    return await ctx.followup.send(content=content, ephemeral=ephemeral)
            else:
                # Cualquier otro caso: usar send normal
                if embed:
                    return await ctx.send(embed=embed, ephemeral=ephemeral if hasattr(ctx, 'interaction') and ctx.interaction else False)
                else:
                    return await ctx.send(content=content, ephemeral=ephemeral if hasattr(ctx, 'interaction') and ctx.interaction else False)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            # Fallback más simple: intentar solo send básico
            try:
                if embed:
                    return await ctx.send(embed=embed)
                else:
                    return await ctx.send(content=content)
            except Exception as e2:
                logger.error(f"Error en fallback: {e2}")
                return None
    
    @commands.hybrid_command(name='ba_monitor_add_server')
    async def add_monitored_server(self, ctx, server_ip: str, *, server_name: str):
        """
        [ADMIN] Agregar servidor SCUM para monitorear
        
        Uso: /ba_monitor_add_server <IP:Puerto> <Nombre del Servidor>
        Ejemplo: /ba_monitor_add_server 192.168.1.100:7777 Mi Servidor SCUM
        """
        # Verificar permisos
        if not (ctx.author.guild_permissions.administrator or 
                ctx.author.id == ctx.guild.owner_id):
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="Solo administradores pueden usar este comando",
                color=0xFF0000
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Verificar premium
        if not await check_premium_status(str(ctx.guild.id)):
            embed = discord.Embed(
                title="💎 Funcionalidad Premium",
                description="El monitoreo de servidores requiere suscripción premium.\nUsa `/ba_premium_info` para más información.",
                color=0xFFD700
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        # Defer inmediatamente para evitar timeout (solo para slash commands)
        if hasattr(ctx, 'interaction') and ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()
        
        try:
            # Verificar límites
            limits = await server_db.check_server_limit(str(ctx.guild.id))
            if not limits['can_add']:
                embed = discord.Embed(
                    title="⚠️ Límite Alcanzado",
                    description=f"Ya tienes {limits['current_count']}/{limits['max_servers']} servidores monitoreados.\nContacta al soporte para aumentar el límite.",
                    color=0xFFA500
                )
                await self._safe_send(ctx, embed=embed)
                return
            
            # Parsear IP y puerto
            if ':' in server_ip:
                ip, port_str = server_ip.split(':')
                try:
                    port = int(port_str)
                except ValueError:
                    port = 7777
            else:
                ip = server_ip
                port = 7777
            
            # Buscar servidor en Battlemetrics
            embed_searching = discord.Embed(
                title="🔍 Buscando Servidor",
                description=f"Buscando **{server_name}** en Battlemetrics...",
                color=0x00BFFF
            )
            message = await self._safe_send(ctx, embed=embed_searching)
            
            server_data = await server_monitor.search_server_by_ip(ip, port)
            
            if not server_data:
                embed = discord.Embed(
                    title="❌ Servidor No Encontrado",
                    description=f"No se pudo encontrar el servidor `{ip}:{port}` en Battlemetrics.\n\n**Posibles causas:**\n• El servidor está offline\n• La IP/Puerto es incorrecta\n• El servidor no está registrado en Battlemetrics",
                    color=0xFF0000
                )
                # Solo editar si tenemos un mensaje válido
                if message:
                    try:
                        await message.edit(embed=embed)
                    except:
                        await self._safe_send(ctx, embed=embed)
                else:
                    await self._safe_send(ctx, embed=embed)
                return
            
            # Agregar a la base de datos
            success = await server_db.add_monitored_server(
                guild_id=str(ctx.guild.id),
                server_name=server_name,
                server_ip=ip,
                server_port=port,
                battlemetrics_id=server_data['battlemetrics_id'],
                added_by=str(ctx.author.id)
            )
            
            if not success:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"El servidor **{server_name}** ya está siendo monitoreado en este Discord.",
                    color=0xFF0000
                )
                # Solo editar si tenemos un mensaje válido
                if message:
                    try:
                        await message.edit(embed=embed)
                    except:
                        await self._safe_send(ctx, embed=embed)
                else:
                    await self._safe_send(ctx, embed=embed)
                return
            
            # Obtener estado actual
            status_data = await server_monitor.get_server_status_by_id(server_data['battlemetrics_id'])
            
            embed = discord.Embed(
                title="✅ Servidor Agregado",
                description=f"**{server_name}** se agregó al monitoreo",
                color=0x00FF00
            )
            embed.add_field(
                name="📊 Información",
                value=f"**IP:** `{ip}:{port}`\n**Battlemetrics ID:** `{server_data['battlemetrics_id']}`",
                inline=False
            )
            
            if status_data:
                status_emoji = "🟢" if status_data.get('online') else "🔴"
                embed.add_field(
                    name="📡 Estado Actual",
                    value=f"{status_emoji} {'Online' if status_data.get('online') else 'Offline'}",
                    inline=True
                )
                if status_data.get('online'):
                    players_text = f"{status_data.get('players', 0)}/{status_data.get('max_players', 'N/A')}"
                    
                    # Agregar fuente de datos si está disponible
                    if status_data.get('data_source') == 'player-count-history':
                        players_text += "\n🔄 Datos actualizados"
                    elif status_data.get('data_warning'):
                        players_text += f"\n{status_data['data_warning']}"
                    
                    embed.add_field(
                        name="👥 Jugadores",
                        value=players_text,
                        inline=True
                    )
            
            remaining = limits['remaining'] - 1
            embed.add_field(
                name="📈 Límites",
                value=f"Servidores restantes: **{remaining}**",
                inline=True
            )
            
            embed.set_footer(text=f"Agregado por {ctx.author.display_name}")
            
            # Solo editar si tenemos un mensaje válido
            if message:
                try:
                    await message.edit(embed=embed)
                except:
                    await self._safe_send(ctx, embed=embed)
            else:
                await self._safe_send(ctx, embed=embed)
            
            logger.info(f"Servidor {server_name} agregado por {ctx.author} en guild {ctx.guild.id}")
            
        except Exception as e:
            logger.error(f"Error agregando servidor: {e}")
            embed = discord.Embed(
                title="❌ Error Interno",
                description="Ocurrió un error al agregar el servidor. Inténtalo nuevamente.",
                color=0xFF0000
            )
            await self._safe_send(ctx, embed=embed)
    
    async def monitored_server_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompletado dinámico para servidores monitoreados"""
        try:
            # Verificar que la interacción sea válida
            if not interaction.guild:
                return [app_commands.Choice(name="❌ Ejecutar en servidor", value="no_guild")]
            
            guild_id = str(interaction.guild.id)
            servers = await server_db.get_monitored_servers(guild_id)
            
            if not servers:
                return [app_commands.Choice(name="⚠️ No hay servidores monitoreados", value="no_servers")]
            
            # Filtrar servidores por texto actual
            current_lower = current.lower()
            choices = []
            
            for server in servers:
                server_name = server['server_name']
                if current_lower in server_name.lower():
                    # Agregar emoji de estado
                    status_emoji = "🟢" if server.get('last_status') == 'online' else "🔴"
                    display_name = f"{status_emoji} {server_name}"
                    
                    # Limitar longitud del nombre mostrado
                    if len(display_name) > 100:
                        display_name = display_name[:97] + "..."
                    
                    choices.append(app_commands.Choice(name=display_name, value=server_name))
            
            # Limitar a 25 opciones (límite de Discord)
            return choices[:25]
            
        except Exception as e:
            logger.error(f"Error en monitored_server_autocomplete: {e}")
            return [app_commands.Choice(name="❌ Error cargando servidores", value="error")]

    @commands.hybrid_command(name='ba_monitor_server_remove')
    @app_commands.autocomplete(server_name=monitored_server_autocomplete)
    @app_commands.describe(server_name="Nombre del servidor SCUM a eliminar del monitoreo")
    async def remove_monitored_server(self, ctx, *, server_name: str):
        """
        [ADMIN] Remover servidor del monitoreo
        
        Uso: /ba_monitor_server_remove <Nombre del Servidor>
        """
        # Verificar permisos
        if not (ctx.author.guild_permissions.administrator or 
                ctx.author.id == ctx.guild.owner_id):
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="Solo administradores pueden usar este comando",
                color=0xFF0000
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            success = await server_db.remove_monitored_server(str(ctx.guild.id), server_name)
            
            if success:
                embed = discord.Embed(
                    title="✅ Servidor Removido",
                    description=f"**{server_name}** ya no será monitoreado",
                    color=0x00FF00
                )
                embed.set_footer(text=f"Removido por {ctx.author.display_name}")
            else:
                embed = discord.Embed(
                    title="❌ Servidor No Encontrado",
                    description=f"No se encontró un servidor llamado **{server_name}** en el monitoreo",
                    color=0xFF0000
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error removiendo servidor: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al remover el servidor",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='ba_monitor_list')
    async def list_monitored_servers(self, ctx):
        """
        [ADMIN] Ver servidores monitoreados
        """
        # Verificar permisos
        if not (ctx.author.guild_permissions.administrator or 
                ctx.author.id == ctx.guild.owner_id):
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="Solo administradores pueden usar este comando",
                color=0xFF0000
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            servers = await server_db.get_monitored_servers(str(ctx.guild.id))
            limits = await server_db.check_server_limit(str(ctx.guild.id))
            
            if not servers:
                embed = discord.Embed(
                    title="📋 Servidores Monitoreados",
                    description="No hay servidores siendo monitoreados",
                    color=0x00BFFF
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Usa `/ba_monitor_add_server` para agregar un servidor",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="📋 Servidores Monitoreados",
                    description=f"**{len(servers)}** de **{limits['max_servers']}** servidores",
                    color=0x00BFFF
                )
                
                for i, server in enumerate(servers, 1):
                    # Obtener estado actualizado
                    status_data = None
                    if server['battlemetrics_id']:
                        status_data = await server_monitor.get_server_status_by_id(server['battlemetrics_id'])
                    
                    status_emoji = "🟢" if status_data and status_data.get('online') else "🔴"
                    alerts_emoji = "🔔" if server['alerts_enabled'] else "🔕"
                    
                    server_info = f"{status_emoji} **{server['server_name']}**\n"
                    server_info += f"📍 `{server['server_ip']}:{server['server_port']}`\n"
                    
                    if status_data and status_data.get('online'):
                        players = status_data.get('players', 0)
                        max_players = status_data.get('max_players', 'N/A')
                        server_info += f"👥 {players}/{max_players} jugadores\n"
                    
                    server_info += f"{alerts_emoji} Alertas"
                    
                    embed.add_field(
                        name=f"🎮 Servidor #{i}",
                        value=server_info,
                        inline=True
                    )
                
                if limits['remaining'] > 0:
                    embed.add_field(
                        name="📈 Espacios Disponibles",
                        value=f"Puedes agregar **{limits['remaining']}** servidores más",
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listando servidores: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al obtener la lista de servidores",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='ba_monitor_status')
    async def get_server_status(self, ctx, *, server_name: str = None):
        """
        Ver estado de servidor(es) monitoreados
        
        Uso: /ba_monitor_status [nombre del servidor]
        Si no especificas nombre, muestra todos los servidores
        """
        try:
            # Defer inmediatamente para evitar timeout (solo para slash commands)
            if hasattr(ctx, 'interaction') and ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.defer()
            
            servers = await server_db.get_monitored_servers(str(ctx.guild.id))
            
            if not servers:
                embed = discord.Embed(
                    title="📊 Estado de Servidores",
                    description="No hay servidores siendo monitoreados",
                    color=0x00BFFF
                )
                await self._safe_send(ctx, embed=embed)
                return
            
            # Si se especificó un servidor
            if server_name:
                server = await server_db.get_server_by_name(str(ctx.guild.id), server_name)
                if not server:
                    embed = discord.Embed(
                        title="❌ Servidor No Encontrado",
                        description=f"No se encontró el servidor **{server_name}**",
                        color=0xFF0000
                    )
                    await self._safe_send(ctx, embed=embed)
                    return
                
                servers = [server]
            
            embed = discord.Embed(
                title="📊 Estado de Servidores SCUM",
                color=0x00BFFF,
                timestamp=datetime.now()
            )
            
            total_online = 0
            total_servers = len(servers)
            
            for server in servers:
                # Obtener estado actualizado
                status_data = None
                if server['battlemetrics_id']:
                    status_data = await server_monitor.get_server_status_by_id(server['battlemetrics_id'])
                    
                    # Actualizar en base de datos
                    if status_data:
                        await server_db.update_server_status(server['server_id'], status_data)
                
                # Crear campo para este servidor
                if status_data and status_data.get('online'):
                    total_online += 1
                    status_info = "🟢 **ONLINE**\n"
                    players = status_data.get('players', 0)
                    max_players = status_data.get('max_players', 'N/A')
                    status_info += f"👥 **{players}/{max_players}** jugadores\n"
                    
                    if status_data.get('queue'):
                        status_info += f"⏳ **{status_data['queue']}** en cola\n"
                    
                    # Info adicional del servidor
                    if status_data.get('rank'):
                        status_info += f"📈 Rank: **#{status_data['rank']}**\n"
                    
                    color_indicator = "🟢"
                else:
                    status_info = "🔴 **OFFLINE**\n"
                    color_indicator = "🔴"
                
                status_info += f"📍 `{server['server_ip']}:{server['server_port']}`"
                
                embed.add_field(
                    name=f"{color_indicator} {server['server_name']}",
                    value=status_info,
                    inline=True
                )
            
            # Resumen general
            embed.description = f"**{total_online}/{total_servers}** servidores online"
            
            if len(servers) == 1:
                # Para un solo servidor, agregar más detalles
                server = servers[0]
                if status_data:
                    embed.add_field(
                        name="🔗 Enlaces",
                        value=f"[Ver en Battlemetrics](https://www.battlemetrics.com/servers/scum/{server['battlemetrics_id']})",
                        inline=False
                    )
            
            embed.set_footer(text="🔄 Estado actualizado")
            
            # Enviar respuesta usando _safe_send
            await self._safe_send(ctx, embed=embed)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de servidores: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al obtener el estado de los servidores",
                color=0xFF0000
            )
            # Manejar error response también
            await self._safe_send(ctx, embed=embed)
    
    @commands.hybrid_command(name='ba_monitor_alerts')
    @app_commands.autocomplete(server_name=monitored_server_autocomplete)
    @app_commands.describe(
        server_name="Nombre del servidor SCUM",
        enabled="Activar (True) o desactivar (False) las alertas"
    )
    async def toggle_server_alerts(self, ctx, server_name: str, enabled: bool):
        """
        [ADMIN] Activar/desactivar alertas para un servidor
        
        Uso: /ba_monitor_alerts <servidor> <true/false>
        """
        # Verificar permisos
        if not (ctx.author.guild_permissions.administrator or 
                ctx.author.id == ctx.guild.owner_id):
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="Solo administradores pueden usar este comando",
                color=0xFF0000
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            success = await server_db.toggle_server_alerts(str(ctx.guild.id), server_name, enabled)
            
            if success:
                action = "activadas" if enabled else "desactivadas"
                emoji = "🔔" if enabled else "🔕"
                embed = discord.Embed(
                    title=f"{emoji} Alertas {action.capitalize()}",
                    description=f"Las alertas fueron **{action}** para **{server_name}**",
                    color=0x00FF00 if enabled else 0xFFA500
                )
            else:
                embed = discord.Embed(
                    title="❌ Servidor No Encontrado",
                    description=f"No se encontró el servidor **{server_name}**",
                    color=0xFF0000
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error cambiando alertas: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al cambiar las alertas",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function para cargar el cog"""
    await bot.add_cog(ServerCommands(bot))
    logger.info("ServerCommands cog cargado exitosamente")
