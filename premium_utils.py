"""
Decoradores y utilidades para verificar suscripciones
"""

import discord
from functools import wraps
from subscription_manager import subscription_manager
import logging

logger = logging.getLogger(__name__)

def premium_required(feature_name: str = "esta funcionalidad"):
    """Decorador que requiere suscripción premium"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            guild_id = str(interaction.guild.id) if interaction.guild else "default"
            subscription = await subscription_manager.get_subscription(guild_id)
            
            if subscription['plan_type'] == 'free':
                embed = discord.Embed(
                    title="💎 Funcionalidad Premium",
                    description=f"Para usar {feature_name} necesitas actualizar a **Premium**.",
                    color=0xffa500
                )
                embed.add_field(
                    name="🆓 Plan Actual: Gratuito",
                    value="• 2 bunkers simultáneos\n• 1 servidor SCUM\n• Notificaciones básicas",
                    inline=False
                )
                embed.add_field(
                    name="💎 Plan Premium ($5.99/mes)",
                    value="• Bunkers ilimitados\n• Múltiples servidores SCUM\n• Notificaciones avanzadas\n• Estadísticas detalladas",
                    inline=False
                )
                embed.add_field(
                    name="🔗 Actualizar",
                    value="Usa `/ba_premium` para más información",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Continuar con la función original
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

def check_limits(limit_type: str):
    """Decorador para verificar límites de uso"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            # DEFER INMEDIATAMENTE para evitar timeouts
            if not interaction.response.is_done():
                await interaction.response.defer()
            
            guild_id = str(interaction.guild.id) if interaction.guild else "default"
            
            # Obtener contadores actuales (esto depende de tu implementación)
            if limit_type == "bunkers":
                from database_v2 import BunkerDatabaseV2
                db = BunkerDatabaseV2()
                bunkers = await db.get_all_bunkers_status(guild_id)
                active_bunkers = len([b for b in bunkers if b.get('registered_by')])
                servers = await db.get_servers(guild_id)
                servers_count = len(servers)
                
                limits = await subscription_manager.check_limits(guild_id, active_bunkers, servers_count)
                
                if not limits['bunkers_ok']:
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
                        value="Actualiza a Premium para bunkers ilimitados\n`/ba_premium`",
                        inline=True
                    )
                    
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
                        value="Actualiza a Premium para servidores ilimitados\n`/ba_premium`",
                        inline=True
                    )
                    
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
            value=f"• **{subscription['max_bunkers']}** bunkers simultáneos\n• **{subscription['max_servers']}** servidor SCUM\n• Notificaciones básicas",
            inline=False
        )
        embed.add_field(
            name="💎 Actualizar a Premium",
            value="• Bunkers ilimitados\n• Múltiples servidores SCUM\n• Notificaciones avanzadas\n• Estadísticas detalladas\n• Soporte prioritario",
            inline=False
        )
        embed.add_field(
            name="💰 Precio",
            value=f"**${subscription.get('premium_price', 5.99)}/mes**",
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
    
    embed.set_footer(text="Usa /ba_premium para gestionar tu suscripción")
    return embed
