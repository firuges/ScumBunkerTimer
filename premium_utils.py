"""
Decoradores y utilidades para verificar suscripciones
"""

import discord
from functools import wraps
from subscription_manager import subscription_manager
import logging

logger = logging.getLogger(__name__)

def premium_required(feature_name: str = "esta funcionalidad"):
    """Decorador que requiere suscripción premium - SIN DEFER AUTOMÁTICO"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            # Verificar suscripción ANTES de cualquier defer
            guild_id = str(interaction.guild.id) if interaction.guild else "default"
            subscription = await subscription_manager.get_subscription(guild_id)
            
            if subscription['plan_type'] == 'free':
                # Plan gratuito - mostrar mensaje de upgrade
                embed = discord.Embed(
                    title="💎 Funcionalidad Premium",
                    description=f"Para usar {feature_name} necesitas actualizar a **Premium**.",
                    color=0xffa500
                )
                embed.add_field(
                    name="🆓 Plan Actual: Gratuito",
                    value="• 1 bunker activo por servidor Discord\n• 1 servidor SCUM\n• Comandos básicos",
                    inline=False
                )
                embed.add_field(
                    name="💎 Plan Premium",
                    value="• Bunkers ilimitados\n• Múltiples servidores SCUM\n• Notificaciones avanzadas\n• Estadísticas detalladas\n• DM personal automático",
                    inline=False
                )
                embed.add_field(
                    name="🔗 Actualizar",
                    value="Usa `/ba_suscripcion` para más información",
                    inline=False
                )
                
                # Responder inmediatamente sin defer
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Si es premium, ejecutar función original
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

def check_limits(limit_type: str):
    """Decorador para verificar límites de uso"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            
            guild_id = str(interaction.guild.id) if interaction.guild else "default"
            
            # Obtener contadores actuales y verificar uso diario
            if limit_type == "bunkers":
                from database_v2 import BunkerDatabaseV2
                db = BunkerDatabaseV2()
                
                # Para plan gratuito, verificar uso diario
                guild_id = str(interaction.guild.id) if interaction.guild else "default"
                subscription = await subscription_manager.get_subscription(guild_id)
                
                if subscription['plan_type'] == 'free':
                    # NUEVA LÓGICA: Verificar límite global del servidor para plan gratuito
                    server_limit = await db.check_server_bunker_limit(guild_id)
                    
                    if server_limit['has_active_bunker']:
                        active = server_limit['active_bunker']
                        embed = discord.Embed(
                            title="🔒 Servidor con Bunker Activo",
                            description=f"**Plan Gratuito**: Solo 1 bunker activo por servidor Discord.\n\nYa hay un bunker registrado por otro usuario.",
                            color=0xff6b6b
                        )
                        embed.add_field(
                            name="🎯 Bunker Activo",
                            value=f"**Sector:** {active['sector']}\n**Servidor SCUM:** {active['server_name']}\n**Registrado por:** <@{active['discord_user_id']}>",
                            inline=True
                        )
                        embed.add_field(
                            name="⏰ Tiempo Restante",
                            value=f"{active['hours_remaining']:.1f} horas\n{active['expiry_time']}",
                            inline=True
                        )
                        embed.add_field(
                            name="💎 Solución",
                            value="• Espera a que expire el bunker actual\n• Actualiza a Premium para bunkers ilimitados\n`/ba_suscripcion`",
                            inline=False
                        )
                        embed.add_field(
                            name="� Filosofía del Plan Gratuito",
                            value="Un bunker por servidor fomenta la coordinación del equipo y evita el spam. ¡Organízense!",
                            inline=False
                        )
                        
                        if not interaction.response.is_done():
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    # Si no hay bunkers activos en el servidor, permitir registro
                    # (Ya no verificamos uso individual del usuario, solo el límite del servidor)
                
                # Para verificación de bunkers simultáneos (ya no se usa para free, pero se mantiene para compatibilidad)
                bunkers = await db.get_all_bunkers_status(guild_id)
                active_bunkers = len([b for b in bunkers if b.get('registered_by')])
                servers = await db.get_servers(guild_id)
                servers_count = len(servers)
                
                limits = await subscription_manager.check_limits(guild_id, active_bunkers, servers_count)
                
                if not limits['bunkers_ok'] and subscription['plan_type'] != 'free':  # No aplicar límite simultáneo a free
                    embed = discord.Embed(
                        title="⚠️ Límite Alcanzado",
                        description=f"Has alcanzado el límite de bunkers activos para tu plan.",
                        color=0xff6b6b
                    )
                    embed.add_field(
                        name="📊 Uso Actual",
                        value=f"**{limits['current_bunkers']}/{limits['max_bunkers']}** bunkers activos",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 Solución",
                        value="Actualiza a Premium para bunkers ilimitados\n`/ba_suscripcion`",
                        inline=True
                    )
                    
                    if not interaction.response.is_done():
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            elif limit_type == "servers":
                from database_v2 import BunkerDatabaseV2
                db = BunkerDatabaseV2()
                servers = await db.get_servers(guild_id)
                servers_count = len(servers)
                bunkers = await db.get_all_bunkers_status(guild_id)
                active_bunkers = len([b for b in bunkers if b.get('registered_by')])
                
                limits = await subscription_manager.check_limits(guild_id, active_bunkers, servers_count)
                
                if not limits['servers_ok']:
                    embed = discord.Embed(
                        title="⚠️ Límite Alcanzado",
                        description=f"Has alcanzado el límite de servidores SCUM para tu plan.",
                        color=0xff6b6b
                    )
                    embed.add_field(
                        name="📊 Uso Actual",
                        value=f"**{limits['current_servers']}/{limits['max_servers']}** servidores SCUM",
                        inline=True
                    )
                    embed.add_field(
                        name="💎 Solución",
                        value="Actualiza a Premium para servidores ilimitados\n`/ba_suscripcion`",
                        inline=True
                    )
                    
                    if not interaction.response.is_done():
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Continuar con la función original
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

async def get_subscription_embed(guild_id: str) -> discord.Embed:
    """Crear embed con información de suscripción"""
    subscription = await subscription_manager.get_subscription(guild_id)
    
    if subscription['plan_type'] == 'free':
        embed = discord.Embed(
            title="🆓 Plan Gratuito",
            description="Estás usando el plan gratuito del bot.",
            color=0x95a5a6
        )
        embed.add_field(
            name="📊 Límites Actuales",
            value=f"• **{subscription['max_bunkers']}** bunker por día\n• **{subscription['max_servers']}** servidor SCUM\n• Comandos básicos",
            inline=False
        )
        embed.add_field(
            name="💎 Actualizar a Premium",
            value="• Bunkers ilimitados\n• Múltiples servidores SCUM\n• Notificaciones avanzadas\n• Estadísticas detalladas\n• Soporte prioritario",
            inline=False
        )
        embed.add_field(
            name="� Contacto",
            value="Contacta al administrador del bot para upgrade",
            inline=True
        )
    else:
        embed = discord.Embed(
            title=f"💎 Plan {subscription['plan_type'].title()}",
            description="¡Gracias por apoyar el desarrollo del bot!",
            color=0xf39c12
        )
        embed.add_field(
            name="✅ Funcionalidades",
            value="• Bunkers ilimitados\n• Servidores SCUM ilimitados\n• Notificaciones avanzadas\n• Estadísticas detalladas\n• Soporte prioritario",
            inline=False
        )
        if subscription['current_period_end']:
            embed.add_field(
                name="📅 Próxima Renovación",
                value=f"<t:{int(subscription['current_period_end'].timestamp())}:D>",
                inline=True
            )
    
    embed.set_footer(text="Usa /ba_suscripcion para gestionar tu suscripción")
    return embed
