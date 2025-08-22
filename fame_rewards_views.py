#!/usr/bin/env python3
"""
Vistas de Discord UI para Fame Point Rewards
Maneja botones, selectors y modales para el sistema de fama
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from typing import List, Dict
from core.user_manager import get_user_by_discord_id

logger = logging.getLogger(__name__)

class FameRewardsView(discord.ui.View):
    """Vista principal del panel de Fame Point Rewards"""
    
    def __init__(self, fame_system, fame_values: List[int]):
        super().__init__(timeout=None)
        self.fame_system = fame_system
        self.fame_values = fame_values
        self.message = None
        
        # Crear selector con los valores de fama configurables
        self.add_item(FameAmountSelect(fame_values))

class FameAmountSelect(discord.ui.Select):
    """Selector para elegir cantidad de fama a reclamar"""
    
    def __init__(self, fame_values: List[int]):
        options = []
        for value in fame_values:
            # Formatear el valor con separadores de miles
            formatted_value = f"{value:,}"
            options.append(
                discord.SelectOption(
                    label=f"🏆 {formatted_value} Fame Points",
                    value=str(value),
                    description=f"Reclamar premio de {formatted_value} puntos de fama",
                    emoji="⭐"
                )
            )
        
        super().__init__(
            placeholder="🏆 Selecciona la cantidad de fama a reclamar...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona una cantidad de fama"""
        fame_amount = int(self.values[0])
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya tiene una reclamación pendiente
            has_pending = await self.view.fame_system.fame_db.has_pending_claim(
                str(user_data['user_id']), str(interaction.guild.id)
            )
            
            if has_pending:
                embed = discord.Embed(
                    title="⏳ Reclamación Pendiente",
                    description="Ya tienes una reclamación de fama pendiente. Espera a que sea procesada antes de hacer otra.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya reclamó esta cantidad específica de fama
            has_claimed_amount = await self.view.fame_system.fame_db.has_claimed_fame_amount(
                str(user_data['user_id']), str(interaction.guild.id), fame_amount
            )
            
            if has_claimed_amount:
                embed = discord.Embed(
                    title="🚫 Ya Reclamado",
                    description=f"Ya has reclamado y obtenido el premio de **{fame_amount:,} Fame Points** anteriormente. No puedes reclamar la misma cantidad de fama dos veces.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Mostrar modal de confirmación
            modal = FameClaimModal(self.view.fame_system, fame_amount, user_data)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error en callback de FameAmountSelect: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al procesar tu solicitud.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class FameClaimModal(discord.ui.Modal, title="🏆 Reclamar Premio de Fama"):
    """Modal para confirmar la reclamación de fama"""
    
    def __init__(self, fame_system, fame_amount: int, user_data: dict):
        super().__init__()
        self.fame_system = fame_system
        self.fame_amount = fame_amount
        self.user_data = user_data
        
        # Actualizar título con la cantidad específica
        self.title = f"🏆 Reclamar {fame_amount:,} Fame Points"
    
    reason = discord.ui.TextInput(
        label="Razón de la Reclamación",
        placeholder="Explica brevemente por qué mereces estos puntos de fama...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    evidence = discord.ui.TextInput(
        label="Evidencia (URLs, Screenshots, etc.)",
        placeholder="Enlaces a pruebas, screenshots, videos, etc. (opcional)",
        required=False,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar la reclamación de fama"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear reclamación en la base de datos
            claim_id = await self.fame_system.fame_db.create_fame_claim(
                str(self.user_data['user_id']),
                str(interaction.user.id),
                str(interaction.guild.id),
                self.fame_amount
            )
            
            # Enviar notificación a canal de administradores
            notification_sent = await self.fame_system.send_admin_notification(
                interaction.guild, claim_id, interaction.user, self.fame_amount, 
                self.reason.value, self.evidence.value
            )
            
            if notification_sent:
                # Confirmar al usuario
                embed = discord.Embed(
                    title="✅ Reclamación Enviada",
                    description=(
                        f"Tu reclamación de **{self.fame_amount:,} Fame Points** ha sido enviada.\n\n"
                        f"**ID de Reclamación:** #{claim_id:04d}\n"
                        f"**Estado:** Pendiente de revisión\n\n"
                        "Un administrador revisará tu solicitud y la aprobará o rechazará."
                    ),
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Razón proporcionada",
                    value=self.reason.value[:100] + ("..." if len(self.reason.value) > 100 else ""),
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Actualizar el panel principal
                await self.fame_system.update_fame_rewards_panel(interaction.guild.id)
            else:
                # Error enviando notificación
                embed = discord.Embed(
                    title="⚠️ Reclamación Creada con Advertencia",
                    description=(
                        f"Tu reclamación ha sido guardada (ID: #{claim_id:04d}), pero no se pudo "
                        "enviar la notificación a los administradores. "
                        "Contacta directamente con un administrador."
                    ),
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error procesando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="No se pudo procesar tu reclamación. Inténtalo más tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class AdminFameNotificationView(discord.ui.View):
    """Vista para las notificaciones de administradores con botones de confirmación"""
    
    def __init__(self, fame_system, claim_data: dict):
        super().__init__(timeout=None)
        self.fame_system = fame_system
        self.claim_data = claim_data
        self.message = None

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar la reclamación de fama"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden confirmar reclamaciones de fama.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Confirmar en base de datos
            success = await self.fame_system.fame_db.confirm_fame_claim(
                self.claim_data['claim_id'], str(interaction.user.id)
            )
            
            if success:
                # Actualizar embed del mensaje de notificación
                original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if original_embed:
                    original_embed.color = discord.Color.green()
                    original_embed.add_field(
                        name="✅ CONFIRMADO",
                        value=f"Por: {interaction.user.mention}\nFecha: <t:{int(datetime.now().timestamp())}:F>",
                        inline=False
                    )
                
                # Deshabilitar botones
                for item in self.children:
                    item.disabled = True
                
                await interaction.edit_original_response(embed=original_embed, view=self)
                
                # Actualizar panel de rankings
                await self.fame_system.update_fame_rewards_panel(self.claim_data['guild_id'])
                
                # Notificar al usuario (si es posible)
                await self.fame_system.notify_user_claim_result(
                    interaction.guild, self.claim_data, "confirmed", interaction.user
                )
                
                logger.info(f"Reclamación de fama #{self.claim_data['claim_id']} confirmada por {interaction.user}")
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo confirmar la reclamación (posiblemente ya fue procesada).",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error confirmando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al confirmar la reclamación.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rechazar la reclamación de fama"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden rechazar reclamaciones de fama.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para razón del rechazo
        modal = RejectReasonModal(self.fame_system, self.claim_data)
        await interaction.response.send_modal(modal)

class RejectReasonModal(discord.ui.Modal, title="❌ Rechazar Reclamación"):
    """Modal para especificar la razón del rechazo"""
    
    def __init__(self, fame_system, claim_data: dict):
        super().__init__()
        self.fame_system = fame_system
        self.claim_data = claim_data
    
    reason = discord.ui.TextInput(
        label="Razón del Rechazo",
        placeholder="Explica por qué se rechaza esta reclamación...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar el rechazo con razón"""
        await interaction.response.defer()
        
        try:
            # Rechazar en base de datos
            success = await self.fame_system.fame_db.reject_fame_claim(
                self.claim_data['claim_id'], str(interaction.user.id)
            )
            
            if success:
                # Actualizar embed del mensaje de notificación
                original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if original_embed:
                    original_embed.color = discord.Color.red()
                    original_embed.add_field(
                        name="❌ RECHAZADO",
                        value=f"Por: {interaction.user.mention}\nFecha: <t:{int(datetime.now().timestamp())}:F>\nRazón: {self.reason.value}",
                        inline=False
                    )
                
                # Deshabilitar botones de la vista
                view = AdminFameNotificationView(self.fame_system, self.claim_data)
                for item in view.children:
                    item.disabled = True
                
                await interaction.edit_original_response(embed=original_embed, view=view)
                
                # Notificar al usuario (si es posible)
                await self.fame_system.notify_user_claim_result(
                    interaction.guild, self.claim_data, "rejected", interaction.user, self.reason.value
                )
                
                logger.info(f"Reclamación de fama #{self.claim_data['claim_id']} rechazada por {interaction.user}")
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo rechazar la reclamación (posiblemente ya fue procesada).",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error rechazando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al rechazar la reclamación.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)