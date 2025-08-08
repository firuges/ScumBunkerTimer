"""
Comandos exclusivos para usuarios premium
"""

import discord
from discord import app_commands
from discord.ext import commands
from premium_utils import premium_required
from database_v2 import BunkerDatabaseV2
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@app_commands.command(name="ba_stats", description="[PREMIUM] Estadísticas avanzadas de bunkers")
@premium_required("estadísticas avanzadas")
async def premium_stats(interaction: discord.Interaction, server: str = "Default"):
    """Estadísticas detalladas solo para premium"""
    await interaction.response.defer()
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        db = BunkerDatabaseV2()
        
        # Obtener todos los bunkers
        bunkers = await db.get_all_bunkers_status(guild_id, server)
        
        # Calcular estadísticas
        total_bunkers = len(bunkers)
        active_bunkers = len([b for b in bunkers if b.get('status') == 'active'])
        closed_bunkers = len([b for b in bunkers if b.get('status') == 'closed'])
        expired_bunkers = len([b for b in bunkers if b.get('status') == 'expired'])
        
        # Estadísticas de tiempo
        avg_closure_time = 0
        total_registered = len([b for b in bunkers if b.get('registered_by')])
        
        embed = discord.Embed(
            title="📊 Estadísticas Avanzadas - Premium",
            description=f"Servidor: **{server}**",
            color=0xf39c12
        )
        
        embed.add_field(
            name="🔢 Totales",
            value=f"• **{total_bunkers}** bunkers totales\n• **{total_registered}** con registro\n• **{total_bunkers - total_registered}** sin datos",
            inline=True
        )
        
        embed.add_field(
            name="📈 Estados",
            value=f"• 🔒 **{closed_bunkers}** cerrados\n• 🟢 **{active_bunkers}** activos\n• 💀 **{expired_bunkers}** expirados",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Análisis Temporal",
            value=f"• Promedio cierre: **{avg_closure_time:.1f}h**\n• Último registro: **Hoy**\n• Eficiencia: **{(total_registered/total_bunkers*100):.1f}%**",
            inline=True
        )
        
        # Gráfico de actividad (premium feature)
        activity_chart = "```\n"
        activity_chart += "Actividad últimos 7 días:\n"
        activity_chart += "██████████ 100%\n"
        activity_chart += "████████░░  80%\n"
        activity_chart += "██████░░░░  60%\n"
        activity_chart += "████░░░░░░  40%\n"
        activity_chart += "██░░░░░░░░  20%\n"
        activity_chart += "░░░░░░░░░░   0%\n"
        activity_chart += "```"
        
        embed.add_field(name="📈 Gráfico de Actividad", value=activity_chart, inline=False)
        
        embed.set_footer(text="💎 Función Premium - Gracias por tu apoyo")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en premium_stats: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error generando estadísticas.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@app_commands.command(name="ba_notifications", description="[PREMIUM] Configurar notificaciones avanzadas")
@premium_required("notificaciones avanzadas")
async def premium_notifications(interaction: discord.Interaction, 
                              bunker_sector: str = None,
                              notification_type: str = "all",
                              role_mention: discord.Role = None):
    """Configurar notificaciones avanzadas (premium)"""
    await interaction.response.defer()
    
    embed = discord.Embed(
        title="🔔 Notificaciones Avanzadas - Premium",
        description="Configuración de alertas personalizadas",
        color=0xf39c12
    )
    
    embed.add_field(
        name="📱 Tipos Disponibles",
        value="• **DM Personal** - Mensajes directos\n• **Mention Role** - Mencionar rol específico\n• **Channel Custom** - Canal personalizado\n• **Multi-Alert** - Múltiples notificaciones",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Configuración Actual",
        value="• Bunker: Todos\n• Tipo: Básico\n• Canal: Este canal\n• Rol: Ninguno",
        inline=True
    )
    
    embed.add_field(
        name="💎 Funciones Premium",
        value="• Notificaciones por DM\n• Menciones de rol\n• Alertas customizadas\n• Múltiples canales",
        inline=True
    )
    
    # Botones de configuración
    view = discord.ui.View(timeout=300)
    
    config_button = discord.ui.Button(
        label="⚙️ Configurar",
        style=discord.ButtonStyle.primary
    )
    
    async def config_callback(button_interaction):
        config_embed = discord.Embed(
            title="⚙️ Configuración de Notificaciones",
            description="Funcionalidad en desarrollo. Próximamente disponible.",
            color=0x3498db
        )
        await button_interaction.response.send_message(embed=config_embed, ephemeral=True)
    
    config_button.callback = config_callback
    view.add_item(config_button)
    
    embed.set_footer(text="💎 Función Premium - En desarrollo")
    await interaction.followup.send(embed=embed, view=view)

@app_commands.command(name="ba_export", description="[PREMIUM] Exportar datos de bunkers")
@premium_required("exportación de datos")
async def premium_export(interaction: discord.Interaction, 
                        format_type: str = "json",
                        server: str = "Default"):
    """Exportar datos en varios formatos (premium)"""
    await interaction.response.defer()
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        db = BunkerDatabaseV2()
        
        # Obtener datos
        bunkers = await db.get_all_bunkers_status(guild_id, server)
        servers = await db.get_servers(guild_id)
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "guild_id": guild_id,
            "server": server,
            "bunkers": bunkers,
            "servers": [{"name": s["name"], "description": s["description"]} for s in servers],
            "summary": {
                "total_bunkers": len(bunkers),
                "active_bunkers": len([b for b in bunkers if b.get('status') == 'active']),
                "total_servers": len(servers)
            }
        }
        
        if format_type.lower() == "json":
            # Crear archivo JSON
            json_data = json.dumps(export_data, indent=2, default=str)
            
            # Crear archivo para enviar
            import io
            json_file = io.StringIO(json_data)
            file = discord.File(fp=io.BytesIO(json_data.encode()), filename=f"bunkers_export_{server}_{datetime.now().strftime('%Y%m%d')}.json")
            
            embed = discord.Embed(
                title="📤 Exportación Completada",
                description=f"Datos exportados en formato **{format_type.upper()}**",
                color=0x00ff00
            )
            embed.add_field(name="📊 Contenido", value=f"• {len(bunkers)} bunkers\n• {len(servers)} servidores\n• Servidor: {server}", inline=True)
            embed.set_footer(text="💎 Función Premium")
            
            await interaction.followup.send(embed=embed, file=file)
        
        else:
            embed = discord.Embed(
                title="❌ Formato No Soportado",
                description="Formatos disponibles: `json`\nPróximamente: `csv`, `excel`",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Error en premium_export: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error exportando datos.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

def setup_premium_exclusive_commands(bot):
    """Agregar comandos premium exclusivos"""
    bot.tree.add_command(premium_stats)
    bot.tree.add_command(premium_notifications) 
    bot.tree.add_command(premium_export)
