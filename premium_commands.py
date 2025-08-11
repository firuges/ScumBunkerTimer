"""
Comandos relacionados con suscripciones premium
"""

import discord
from discord import app_commands
from discord.ext import commands
from subscription_manager import subscription_manager
from premium_utils import get_subscription_embed
from typing import List
import logging
import os

logger = logging.getLogger(__name__)

async def action_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocompletado para actions del comando admin_premium"""
    try:
        actions = [
            ("cancel", "🔴 cancel - Cancelar premium (volver a gratuito)"),
            ("upgrade", "✅ upgrade - Dar premium al servidor"), 
            ("status", "📊 status - Ver estado de suscripción"),
            ("list", "📋 list - Listar todas las suscripciones")
        ]
        
        # Filtrar por texto actual si se proporciona
        if current:
            filtered_actions = [a for a in actions if current.lower() in a[0].lower()]
        else:
            filtered_actions = actions
        
        # Asegurar que siempre hay al menos una opción
        if not filtered_actions:
            filtered_actions = actions[:2]  # Default: primeras 2 opciones
        
        # Limitar a máximo 25 opciones (límite de Discord)
        filtered_actions = filtered_actions[:25]
        
        return [
            app_commands.Choice(name=name, value=value)
            for value, name in filtered_actions
        ]
        
    except Exception as e:
        logger.error(f"Error en action_autocomplete: {e}")
        # Fallback seguro en caso de error
        return [
            app_commands.Choice(name="✅ upgrade - Dar premium", value="upgrade"),
            app_commands.Choice(name="🔴 cancel - Cancelar premium", value="cancel"),
        ]

async def plan_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """Autocompletado para planes del comando admin_premium"""
    try:
        plans = [
            ("premium", "💎 premium - Plan Premium"),
            ("free", "🆓 free - Plan Gratuito")
        ]
        
        # Filtrar por texto actual si se proporciona
        if current:
            filtered_plans = [p for p in plans if current.lower() in p[0].lower()]
        else:
            filtered_plans = plans
        
        # Asegurar que siempre hay al menos una opción
        if not filtered_plans:
            filtered_plans = plans  # Default: todas las opciones
        
        return [
            app_commands.Choice(name=name, value=value)
            for value, name in filtered_plans
        ]
        
    except Exception as e:
        logger.error(f"Error en plan_autocomplete: {e}")
        # Fallback seguro en caso de error
        return [
            app_commands.Choice(name="💎 premium - Plan Premium", value="premium"),
            app_commands.Choice(name="🆓 free - Plan Gratuito", value="free"),
        ]

class PremiumCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ba_plans", description="Ver planes de suscripción disponibles")
    async def subscription_plans(self, interaction: discord.Interaction):
        """Mostrar información sobre planes premium"""
        
        guild_id = str(interaction.guild.id) if interaction.guild else "default"
        
        try:
            embed = await get_subscription_embed(guild_id)
            
            # Botones de acción
            view = discord.ui.View(timeout=300)
            
            subscription = await subscription_manager.get_subscription(guild_id)
            
            if subscription['plan_type'] == 'free':
                # Botón de upgrade
                upgrade_button = discord.ui.Button(
                    label="💎 Actualizar a Premium",
                    style=discord.ButtonStyle.primary,
                    emoji="💳"
                )
                
                async def upgrade_callback(button_interaction):
                    upgrade_embed = discord.Embed(
                        title="💎 Actualizar a Premium",
                        description="Para activar tu suscripción premium, contacta al administrador del bot.",
                        color=0xf39c12
                    )
                    upgrade_embed.add_field(
                        name="📞 Contacto",
                        value="• Discord: `@admin` (reemplazar por tu contacto)\n• Email: admin@tubot.com\n• Telegram: @tubot_admin",
                        inline=False
                    )
                    upgrade_embed.add_field(
                        name="💳 Métodos de Pago",
                        value="• PayPal\n• Stripe (Tarjeta)\n• Criptomonedas",
                        inline=True
                    )
                    upgrade_embed.add_field(
                        name="🔄 Activación",
                        value="La activación es inmediata tras el pago",
                        inline=True
                    )
                    
                    await button_interaction.response.send_message(embed=upgrade_embed, ephemeral=True)
                
                upgrade_button.callback = upgrade_callback
                view.add_item(upgrade_button)
            
            else:
                # Botón de gestión
                manage_button = discord.ui.Button(
                    label="⚙️ Gestionar Suscripción",
                    style=discord.ButtonStyle.secondary
                )
                
                async def manage_callback(button_interaction):
                    manage_embed = discord.Embed(
                        title="⚙️ Gestionar Suscripción",
                        description="Para cancelar o modificar tu suscripción, contacta al soporte.",
                        color=0x3498db
                    )
                    manage_embed.add_field(
                        name="📞 Soporte Premium",
                        value="• Discord: `@admin`\n• Email: support@tubot.com\n• Respuesta: <24h",
                        inline=False
                    )
                    
                    await button_interaction.response.send_message(embed=manage_embed, ephemeral=True)
                
                manage_button.callback = manage_callback
                view.add_item(manage_button)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error en subscription_plans: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al obtener información de suscripción.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ba_admin_subs", description="[ADMIN] Gestionar suscripciones premium")
    @app_commands.autocomplete(action=action_autocomplete, plan=plan_autocomplete)
    @app_commands.describe(
        action="Acción a realizar (cancel, upgrade, status, list)",
        guild_id="ID del servidor Discord (opcional, usa servidor actual si no se especifica)",
        plan="Tipo de plan para upgrade (solo para action=premium)"
    )
    async def admin_subscriptions(self, interaction: discord.Interaction, 
                          action: str, 
                          guild_id: str = None,
                          plan: str = "premium"):
        """Comando de administración para gestionar suscripciones"""
        
        # Defer la respuesta inmediatamente para evitar timeouts
        await interaction.response.defer(ephemeral=True)
        
        # Verificar permisos de administrador (con fallback a config.py)
        admin_ids_env = os.getenv('BOT_ADMIN_IDS', '').split(',')
        admin_ids_from_env = [id.strip() for id in admin_ids_env if id.strip()]
        
        # Si no hay IDs en .env, usar config.py como respaldo
        if not admin_ids_from_env:
            try:
                from config import BOT_ADMIN_IDS
                admin_ids = [str(id) for id in BOT_ADMIN_IDS]
            except ImportError:
                admin_ids = []
        else:
            admin_ids = admin_ids_from_env
        
        if str(interaction.user.id) not in admin_ids:
            await interaction.followup.send("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return
        
        target_guild_id = guild_id or str(interaction.guild.id)
        
        try:
            if action.lower() == "upgrade":
                await subscription_manager.upgrade_subscription(target_guild_id, plan)
                embed = discord.Embed(
                    title="✅ Suscripción Actualizada",
                    description=f"Guild `{target_guild_id}` actualizado a plan **{plan}**",
                    color=0x00ff00
                )
                
            elif action.lower() == "cancel":
                await subscription_manager.cancel_subscription(target_guild_id)
                embed = discord.Embed(
                    title="✅ Suscripción Cancelada",
                    description=f"Guild `{target_guild_id}` devuelto a plan **gratuito**",
                    color=0x00ff00
                )
                
            elif action.lower() == "status":
                subscription = await subscription_manager.get_subscription(target_guild_id)
                embed = discord.Embed(
                    title="📊 Estado de Suscripción",
                    color=0x3498db
                )
                embed.add_field(name="Guild ID", value=target_guild_id, inline=True)
                embed.add_field(name="Plan", value=subscription['plan_type'], inline=True)
                embed.add_field(name="Estado", value=subscription['status'], inline=True)
                if subscription['current_period_end']:
                    embed.add_field(name="Expira", value=subscription['current_period_end'], inline=True)
                
            elif action.lower() == "list":
                subscriptions = await subscription_manager.get_all_subscriptions()
                embed = discord.Embed(
                    title="📊 Todas las Suscripciones",
                    color=0x3498db
                )
                
                free_count = len([s for s in subscriptions if s['plan_type'] == 'free'])
                premium_count = len([s for s in subscriptions if s['plan_type'] != 'free'])
                
                # Calcular ingresos estimados (precio estándar del plan premium)
                premium_price = 9.99  # Precio estándar del plan premium
                estimated_revenue = premium_count * premium_price
                
                embed.add_field(
                    name="📊 Estadísticas", 
                    value=f"• Gratuitos: {free_count}\n• Premium: {premium_count}\n• Ingresos estimados/mes: ${estimated_revenue:.2f}", 
                    inline=False
                )
                
                if premium_count > 0:
                    premium_list = []
                    for s in subscriptions:
                        if s['plan_type'] != 'free':
                            guild_id_short = s['guild_id'][:8] if len(s['guild_id']) > 8 else s['guild_id']
                            premium_list.append(f"• {guild_id_short}... ({s['plan_type']} - {s['status']})")
                    
                    # Mostrar máximo 10 suscripciones
                    if len(premium_list) > 10:
                        premium_list = premium_list[:10]
                        premium_list.append("...")
                    
                    embed.add_field(name="💎 Suscripciones Premium", value="\n".join(premium_list), inline=False)
                
                if len(subscriptions) == 0:
                    embed.add_field(name="ℹ️ Información", value="No hay suscripciones registradas", inline=False)
            
            else:
                embed = discord.Embed(
                    title="❌ Acción Inválida",
                    description="Acciones válidas: `upgrade`, `cancel`, `status`, `list`",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error en admin_subscriptions: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Error ejecutando comando admin: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed)
            except:
                pass  # Si también falla el followup, no hacer nada más

async def setup_premium_commands(bot):
    """Agregar comandos premium al bot como Cog"""
    await bot.add_cog(PremiumCommands(bot))
