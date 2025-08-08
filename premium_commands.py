"""
Comandos relacionados con suscripciones premium
"""

import discord
from discord import app_commands
from discord.ext import commands
from subscription_manager import subscription_manager
from premium_utils import get_subscription_embed
import logging
import os

logger = logging.getLogger(__name__)

class PremiumCommands:
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ba_premium", description="Ver información sobre planes premium")
    async def premium_info(self, interaction: discord.Interaction):
        """Mostrar información sobre planes premium"""
        await interaction.response.defer()
        
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
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error en premium_info: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error al obtener información de suscripción.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="ba_admin_premium", description="[ADMIN] Gestionar suscripciones")
    async def admin_premium(self, interaction: discord.Interaction, 
                          action: str, 
                          guild_id: str = None,
                          plan: str = "premium"):
        """Comando de administración para gestionar suscripciones"""
        
        # Verificar permisos de administrador
        admin_ids = os.getenv('BOT_ADMIN_IDS', 'TU_DISCORD_ID_AQUI').split(',')
        if str(interaction.user.id) not in admin_ids:
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
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
                total_revenue = sum([s['monthly_price'] for s in subscriptions if s['plan_type'] != 'free'])
                
                embed.add_field(name="📊 Estadísticas", value=f"• Gratuitos: {free_count}\n• Premium: {premium_count}\n• Ingresos/mes: ${total_revenue:.2f}", inline=False)
                
                if premium_count > 0:
                    premium_list = [f"• {s['guild_id'][:8]}... ({s['plan_type']})" for s in subscriptions if s['plan_type'] != 'free'][:10]
                    embed.add_field(name="💎 Suscripciones Premium", value="\n".join(premium_list), inline=False)
            
            else:
                embed = discord.Embed(
                    title="❌ Acción Inválida",
                    description="Acciones válidas: `upgrade`, `cancel`, `status`, `list`",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error en admin_premium: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error ejecutando acción: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

def setup_premium_commands(bot):
    """Agregar comandos premium al bot"""
    premium = PremiumCommands(bot)
    bot.tree.add_command(premium.premium_info)
    bot.tree.add_command(premium.admin_premium)
