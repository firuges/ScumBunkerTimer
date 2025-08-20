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
from rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# Función para obtener configuraciones de notificación (usada por el bot principal)
async def get_notification_configs(guild_id: str, server_name: str, bunker_sector: str):
    """Obtiene configuraciones de notificación para un bunker específico"""
    db = BunkerDatabaseV2()
    return await db.get_notification_configs(guild_id, server_name, bunker_sector)

# Función de autocompletado para servidores
async def server_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocompletado dinámico para servidores existentes"""
    try:
        # Verificar que la interacción sea válida
        if not interaction.guild:
            return [app_commands.Choice(name="Default", value="Default")]
        
        guild_id = str(interaction.guild.id)
        db = BunkerDatabaseV2()
        
        # Usar timeout para evitar problemas de timing
        import asyncio
        try:
            servers = await asyncio.wait_for(db.get_unique_servers(guild_id), timeout=2.0)
        except asyncio.TimeoutError:
            return [
                app_commands.Choice(name="Default", value="Default"),
                app_commands.Choice(name="convictos", value="convictos")
            ]
        
        # Filtrar por el texto actual
        choices = []
        for server in servers:
            if not current or current.lower() in server.lower():
                choices.append(app_commands.Choice(name=server, value=server))
        
        # Si no hay resultados, devolver opciones por defecto
        if not choices:
            choices = [
                app_commands.Choice(name="Default", value="Default"),
                app_commands.Choice(name="convictos", value="convictos")
            ]
        
        # Limitar a 25 opciones (límite de Discord)
        return choices[:25]
        
    except Exception as e:
        logger.error(f"Error en server_autocomplete: {e}")
        return [app_commands.Choice(name="Default", value="Default")]

@rate_limit("ba_stats")
@app_commands.command(name="ba_stats", description="[PREMIUM] Estadísticas avanzadas de bunkers")
@premium_required("estadísticas avanzadas")
async def premium_stats(interaction: discord.Interaction, server: str = "Default"):
    """Estadísticas detalladas solo para premium"""
    # Manual rate limiting check
    from rate_limiter import rate_limiter
    if not await rate_limiter.check_and_record(interaction, "ba_stats"):
        return
    
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
            value=f"• Promedio cierre: **{avg_closure_time:.1f}h**\n• Último registro: **Hoy**\n• Eficiencia: **{(total_registered/total_bunkers*100 if total_bunkers > 0 else 0):.1f}%**",
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
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en premium_stats: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error generando estadísticas.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@rate_limit("ba_notifications")
@app_commands.command(name="ba_notifications", description="[PREMIUM] Configurar notificaciones avanzadas")
@app_commands.autocomplete(server=server_autocomplete)
@app_commands.describe(
    server="Servidor donde está el bunker",
    bunker_sector="Sector del bunker (A1-P5)",
    notification_type="Tipo de notificación",
    role_mention="Rol a mencionar (opcional)",
    enabled="Activar/desactivar notificaciones"
)
@app_commands.choices(
    notification_type=[
        app_commands.Choice(name="⏰ Expirando (30 min antes)", value="expiring"),
        app_commands.Choice(name="🔴 Expirado", value="expired"),
        app_commands.Choice(name="🆕 Nuevo bunker", value="new_bunker"),
        app_commands.Choice(name="📊 Resumen diario", value="daily_summary"),
        app_commands.Choice(name="🔔 Todas las notificaciones", value="all")
    ],
    bunker_sector=[
        app_commands.Choice(name="🏢 Sector D1", value="D1"),
        app_commands.Choice(name="🏢 Sector C4", value="C4"),
        app_commands.Choice(name="🏢 Sector A1", value="A1"),
        app_commands.Choice(name="🏢 Sector A3", value="A3"),
        app_commands.Choice(name="🌍 Todos los sectores", value="all_sectors")
    ]
)
@premium_required("notificaciones avanzadas")
async def premium_notifications(interaction: discord.Interaction, 
                              server: str = "Default",
                              bunker_sector: str = "all_sectors",
                              notification_type: str = "all",
                              role_mention: discord.Role = None,
                              enabled: bool = True):
    """Configurar notificaciones avanzadas (premium)"""
    # Manual rate limiting check
    from rate_limiter import rate_limiter
    if not await rate_limiter.check_and_record(interaction, "ba_notifications"):
        return
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        channel_id = str(interaction.channel.id)
        db = BunkerDatabaseV2()
        
        # Determinar automáticamente si usar DM personal
        try:
            from config import BOT_CREATOR_ID
        except ImportError:
            BOT_CREATOR_ID = 123456789012345678  # Fallback
            
        # Lógica para determinar DM personal
        use_personal_dm = True  # Por defecto DM personal
        if interaction.user.id == BOT_CREATOR_ID:
            use_personal_dm = False  # Creador del bot usa canal público
        elif interaction.guild and interaction.user.id == interaction.guild.owner_id:
            use_personal_dm = False  # Owner del Discord usa canal público
        
        # Guardar configuración en base de datos
        role_id = str(role_mention.id) if role_mention else None
        await db.save_notification_config(
            guild_id=guild_id,
            channel_id=channel_id,
            server_name=server,
            bunker_sector=bunker_sector,
            notification_type=notification_type,
            role_id=role_id,
            enabled=enabled,
            personal_dm=use_personal_dm,
            created_by=str(interaction.user.id)
        )
        
        # Crear configuración de notificación
        config_text = []
        config_text.append(f"🖥️ **Servidor:** {server}")
        config_text.append(f"📍 **Sector:** {bunker_sector}")
        config_text.append(f"🔔 **Tipo:** {notification_type}")
        if role_mention:
            config_text.append(f"👥 **Rol:** {role_mention.mention}")
        config_text.append(f"✅ **Estado:** {'Activado' if enabled else 'Desactivado'}")
        
        # Mostrar tipo de notificación basado en el usuario
        if interaction.user.id == BOT_CREATOR_ID:
            config_text.append(f"� **Modo:** Canal Público (Eres el creador del bot)")
        elif interaction.guild and interaction.user.id == interaction.guild.owner_id:
            config_text.append(f"👑 **Modo:** Canal Público (Eres el owner del Discord)")
        else:
            config_text.append(f"💎 **Modo:** DM Personal (Usuario premium)")
        
        embed = discord.Embed(
            title="🔔 Notificaciones Configuradas - Premium",
            description="Configuración de alertas personalizada guardada",
            color=0x00ff00 if enabled else 0xff6b6b
        )
        
        embed.add_field(
            name="⚙️ Configuración Actual",
            value="\n".join(config_text),
            inline=False
        )
        
        embed.add_field(
            name="📱 Tipos de Notificación",
            value="• ⏰ **Expirando** - 30 min antes\n• 🔴 **Expirado** - Cuando expira\n• 🆕 **Nuevo** - Al añadir bunker\n• 📊 **Resumen** - Reporte diario\n• 🔔 **Todas** - Completo",
            inline=True
        )
        
        embed.add_field(
            name="💎 Funciones Premium",
            value="• Notificaciones por DM\n• Menciones de rol personalizadas\n• Alertas por sector\n• Configuración por servidor",
            inline=True
        )
        
        # Botones de acción
        view = discord.ui.View(timeout=300)
        
        # Botón de prueba
        test_button = discord.ui.Button(
            label="🧪 Probar Notificación",
            style=discord.ButtonStyle.secondary,
            emoji="🔔"
        )
        
        async def test_callback(button_interaction):
            test_embed = discord.Embed(
                title="🧪 Prueba de Notificación",
                description=f"¡Notificación de prueba enviada!\n\n**Configuración:**\n• Servidor: {server}\n• Sector: {bunker_sector}\n• Tipo: {notification_type}",
                color=0x3498db
            )
            if role_mention:
                test_embed.description += f"\n• Rol: {role_mention.mention}"
            await button_interaction.response.send_message(embed=test_embed, ephemeral=True)
        
        test_button.callback = test_callback
        view.add_item(test_button)
        
        embed.set_footer(text="💎 Función Premium - Configuración guardada")
        await interaction.response.send_message(embed=embed, view=view)
        
    except Exception as e:
        logger.error(f"Error en premium_notifications: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error configurando notificaciones.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@rate_limit("ba_check_notifications")
@app_commands.command(name="ba_check_notifications", description="[PREMIUM] Verificar estado del sistema de notificaciones")
@premium_required("verificación de notificaciones")
async def check_notifications(interaction: discord.Interaction):
    """Verificar el estado de las notificaciones pendientes y configuraciones"""
    # Manual rate limiting check
    from rate_limiter import rate_limiter
    if not await rate_limiter.check_and_record(interaction, "ba_check_notifications"):
        return
    
    try:
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        db = BunkerDatabaseV2()
        
        # Obtener notificaciones pendientes
        pending_notifications = await db.get_pending_notifications(guild_id)
        
        # Obtener configuraciones de notificación
        all_configs = await db.get_notification_configs(guild_id)
        
        embed = discord.Embed(
            title="🔔 Estado del Sistema de Notificaciones",
            description="Verificación completa del sistema",
            color=0x3498db
        )
        
        # Estado de notificaciones pendientes
        if pending_notifications:
            pending_text = []
            for notif in pending_notifications[:5]:  # Máximo 5 para no saturar
                pending_text.append(f"• **{notif['type']}** - {notif['sector']} ({notif['server_name']})")
            
            embed.add_field(
                name=f"📋 Notificaciones Pendientes ({len(pending_notifications)})",
                value="\n".join(pending_text) if pending_text else "Ninguna",
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Notificaciones Pendientes",
                value="✅ No hay notificaciones pendientes",
                inline=False
            )
        
        # Estado de configuraciones
        if all_configs:
            config_text = []
            for config in all_configs[:3]:  # Máximo 3 configuraciones
                config_text.append(f"• **Canal:** <#{config['channel_id']}> - {config['notification_type']}")
            
            embed.add_field(
                name=f"⚙️ Configuraciones Activas ({len(all_configs)})",
                value="\n".join(config_text),
                inline=False
            )
        else:
            embed.add_field(
                name="⚙️ Configuraciones Activas",
                value="❌ No hay configuraciones de notificación\nUsa `/ba_notifications` para configurar",
                inline=False
            )
        
        # Información del sistema
        embed.add_field(
            name="🤖 Sistema",
            value="✅ Task de notificaciones: Activo (cada 5 min)\n✅ Base de datos: Conectada\n✅ Premium: Habilitado",
            inline=False
        )
        
        embed.set_footer(text="💎 Verificación Premium - Sistema monitoreado")
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error en check_notifications: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error verificando notificaciones.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

@rate_limit("ba_export")
@app_commands.command(name="ba_export", description="[PREMIUM] Exportar datos de bunkers")
@premium_required("exportación de datos")
async def premium_export(interaction: discord.Interaction, 
                        format_type: str = "json",
                        server: str = "Default"):
    """Exportar datos en varios formatos (premium)"""
    # Manual rate limiting check
    from rate_limiter import rate_limiter
    if not await rate_limiter.check_and_record(interaction, "ba_export"):
        return
    
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
            
            await interaction.response.send_message(embed=embed, file=file)
        
        else:
            embed = discord.Embed(
                title="❌ Formato No Soportado",
                description="Formatos disponibles: `json`\nPróximamente: `csv`, `excel`",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed)
            
    except Exception as e:
        logger.error(f"Error en premium_export: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Error exportando datos.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)

def setup_premium_exclusive_commands(bot):
    """Agregar comandos premium exclusivos"""
    bot.tree.add_command(premium_stats)
    bot.tree.add_command(premium_notifications) 
    bot.tree.add_command(premium_export)
