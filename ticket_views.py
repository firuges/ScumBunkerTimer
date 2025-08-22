#!/usr/bin/env python3
"""
Views para el Sistema de Tickets
Maneja la interfaz de botones Discord
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BaseTicketView(discord.ui.View):
    """Vista base con manejo de timeout"""
    def __init__(self, timeout: float = None):
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        """Deshabilitar botones al timeout"""
        for item in self.children:
            item.disabled = True
        
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except:
            pass

    async def _safe_send(self, interaction: discord.Interaction, content: str = None, 
                        embed: discord.Embed = None, ephemeral: bool = True, view: discord.ui.View = None):
        """Enviar respuesta de forma segura, soportando views"""
        try:
            send_kwargs = dict(content=content, embed=embed, ephemeral=ephemeral)
            if view is not None:
                send_kwargs['view'] = view
            if interaction.response.is_done():
                await interaction.followup.send(**send_kwargs)
            else:
                await interaction.response.send_message(**send_kwargs)
        except Exception as e:
            logger.error(f"Error enviando respuesta: {e}")

class CreateTicketView(BaseTicketView):
    """Vista para crear tickets"""
    
    def __init__(self, ticket_system):
        super().__init__(timeout=None)  # Vista persistente
        self.ticket_system = ticket_system

    @discord.ui.button(
        label="🎫 Crear Ticket", 
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket_btn"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Crear nuevo ticket"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user = interaction.user
            guild = interaction.guild
            
            # Verificar que el usuario esté registrado
            from core.user_manager import UserManager
            user_manager = UserManager("scum_main.db")
            user_data = await user_manager.get_user_by_discord_id(
                str(user.id), str(guild.id)
            )
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario no registrado",
                    description="Debes registrarte primero usando `/welcome` para crear un ticket.",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed)
                return
            
            # Verificar si ya tiene un ticket activo
            has_active = await self.ticket_system.ticket_db.has_active_ticket(
                str(user_data['user_id']), str(guild.id)
            )
            
            if has_active:
                embed = discord.Embed(
                    title="⚠️ Ticket ya activo",
                    description="Ya tienes un ticket activo. Solo puedes tener un ticket abierto a la vez.",
                    color=discord.Color.orange()
                )
                await self._safe_send(interaction, embed=embed)
                return
            
            # Crear el ticket
            success = await self.ticket_system.create_ticket(user, guild, user_data)
            
            if success:
                embed = discord.Embed(
                    title="✅ Ticket creado",
                    description="Tu ticket ha sido creado exitosamente. Un canal privado se ha abierto para ti.",
                    color=discord.Color.green()
                )
                await self._safe_send(interaction, embed=embed)
            else:
                # Verificar si es problema de permisos
                bot_member = guild.get_member(self.ticket_system.bot.user.id)
                error_msg = "Hubo un error al crear tu ticket."
                
                if bot_member:
                    if not bot_member.guild_permissions.manage_channels:
                        error_msg = "El bot no tiene permisos para crear canales. Contacta a un administrador."
                    elif not bot_member.guild_permissions.manage_permissions:
                        error_msg = "El bot no tiene permisos para configurar canales privados. Contacta a un administrador."
                
                embed = discord.Embed(
                    title="❌ Error",
                    description=error_msg,
                    color=discord.Color.red()
                )
                embed.set_footer(text="Si el problema persiste, contacta a un administrador")
                await self._safe_send(interaction, embed=embed)
                
        except Exception as e:
            logger.error(f"Error creando ticket: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno. Contacta a un administrador.",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed)

class CloseTicketView(BaseTicketView):
    """Vista para cerrar tickets"""
    
    def __init__(self, ticket_system, ticket_data: dict):
        super().__init__(timeout=None)  # Vista persistente
        self.ticket_system = ticket_system
        self.ticket_data = ticket_data

    @discord.ui.button(
        label="🔒 Cerrar Ticket", 
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cerrar ticket"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user = interaction.user
            guild = interaction.guild
            
            # Verificar permisos (solo admin o dueño del ticket)
            is_admin = any(role.permissions.administrator for role in user.roles)
            is_owner = str(user.id) == self.ticket_data['discord_id']
            
            if not (is_admin or is_owner):
                embed = discord.Embed(
                    title="❌ Sin permisos",
                    description="Solo administradores o el dueño del ticket pueden cerrarlo.",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed)
                return
            
            # Confirmar cierre (mover a categoría cerrados)
            embed = discord.Embed(
                title="🔒 Cerrar Ticket",
                description="¿Estás seguro de que quieres cerrar este ticket?\n\n**El ticket se moverá a 'Tickets Cerrados' pero no se eliminará.**",
                color=discord.Color.orange()
            )
            
            confirm_view = ConfirmCloseView(self.ticket_system, self.ticket_data, action="close", original_view=self)
            await self._safe_send(interaction, embed=embed, view=confirm_view)
                
        except Exception as e:
            logger.error(f"Error cerrando ticket: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno al cerrar el ticket.",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed)
    
    @discord.ui.button(
        label="🗑️ Borrar Ticket", 
        style=discord.ButtonStyle.danger,
        custom_id="delete_ticket_btn"
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Borrar ticket permanentemente (solo admin)"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user = interaction.user
            
            # Verificar permisos (solo admin)
            is_admin = any(role.permissions.administrator for role in user.roles)
            
            if not is_admin:
                embed = discord.Embed(
                    title="❌ Sin permisos",
                    description="Solo administradores pueden borrar tickets permanentemente.",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed)
                return
            
            # Confirmar borrado
            embed = discord.Embed(
                title="🗑️ Borrar Ticket",
                description="¿Estás seguro de que quieres **BORRAR PERMANENTEMENTE** este ticket?\n\n**⚠️ Esta acción eliminará el canal completamente y no se puede deshacer.**",
                color=discord.Color.red()
            )
            
            confirm_view = ConfirmCloseView(self.ticket_system, self.ticket_data, action="delete")
            await self._safe_send(interaction, embed=embed, view=confirm_view)
                
        except Exception as e:
            logger.error(f"Error borrando ticket: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno al intentar borrar el ticket.",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed)

class ConfirmCloseView(BaseTicketView):
    """Vista de confirmación para cerrar o borrar ticket"""
    
    def __init__(self, ticket_system, ticket_data: dict, action: str = "close", original_view=None):
        super().__init__(timeout=30.0)  # 30 segundos timeout
        self.ticket_system = ticket_system
        self.ticket_data = ticket_data
        self.action = action  # "close" o "delete"
        self.original_view = original_view  # Vista original para actualizar

    @discord.ui.button(
        label="✅ Confirmar", 
        style=discord.ButtonStyle.success,
        custom_id="confirm_close_btn"
    )
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar cierre o borrado del ticket"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            if self.action == "delete":
                # Borrar permanentemente
                success = await self.ticket_system.delete_ticket(
                    interaction.channel, 
                    str(interaction.user.id),
                    self.ticket_data
                )
                
                if success:
                    # Deshabilitar botones de la vista de confirmación
                    for item in self.children:
                        item.disabled = True
                    
                    # Actualizar mensaje original con botones deshabilitados
                    try:
                        await interaction.edit_original_response(view=self)
                    except:
                        pass
                    
                    embed = discord.Embed(
                        title="✅ Ticket borrado",
                        description="El ticket ha sido borrado permanentemente. Este canal se eliminará en 5 segundos.",
                        color=discord.Color.green()
                    )
                    await self._safe_send(interaction, embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Hubo un error al borrar el ticket.",
                        color=discord.Color.red()
                    )
                    await self._safe_send(interaction, embed=embed)
            
            else:
                # Cerrar (mover a categoría cerrados)
                success = await self.ticket_system.close_ticket(
                    interaction.channel, 
                    str(interaction.user.id),
                    self.ticket_data
                )
                
                if success:
                    # Deshabilitar botones de la vista de confirmación
                    for item in self.children:
                        item.disabled = True
                    
                    # Actualizar mensaje original con botones deshabilitados
                    try:
                        await interaction.edit_original_response(view=self)
                    except:
                        pass
                    
                    # Si tenemos la vista original, deshabilitar solo el botón de cerrar
                    if self.original_view and self.original_view.message:
                        try:
                            # Buscar y deshabilitar solo el botón "Cerrar Ticket"
                            for item in self.original_view.children:
                                if hasattr(item, 'custom_id') and item.custom_id == "close_ticket_btn":
                                    item.disabled = True
                                    item.label = "🔒 Ticket Cerrado"
                                    item.style = discord.ButtonStyle.secondary
                                    break
                            
                            # Actualizar la vista original en el canal
                            await self.original_view.message.edit(view=self.original_view)
                            logger.info("Vista original del ticket actualizada - botón cerrar deshabilitado")
                        except Exception as e:
                            logger.warning(f"No se pudo actualizar vista original: {e}")
                    
                    embed = discord.Embed(
                        title="✅ Ticket cerrado",
                        description="El ticket ha sido cerrado exitosamente. Se ha movido a 'Tickets Cerrados'.",
                        color=discord.Color.green()
                    )
                    await self._safe_send(interaction, embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Hubo un error al cerrar el ticket.",
                        color=discord.Color.red()
                    )
                    await self._safe_send(interaction, embed=embed)
                
        except Exception as e:
            logger.error(f"Error confirmando cierre: {e}")
            
            # Deshabilitar botones en caso de error también
            for item in self.children:
                item.disabled = True
            
            try:
                await interaction.edit_original_response(view=self)
            except:
                pass
            
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno al confirmar el cierre.",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed)
    
    @discord.ui.button(
        label="❌ Cancelar", 
        style=discord.ButtonStyle.secondary,
        custom_id="cancel_close_btn"
    )
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar cierre del ticket"""
        embed = discord.Embed(
            title="❌ Cancelado",
            description="El cierre del ticket ha sido cancelado.",
            color=discord.Color.blue()
        )
        await self._safe_send(interaction, embed=embed)
        
        # Deshabilitar botones
        for item in self.children:
            item.disabled = True
        
        try:
            await interaction.edit_original_response(view=self)
        except:
            pass

class TicketSubjectModal(discord.ui.Modal):
    """Modal para especificar asunto del ticket"""
    
    def __init__(self, ticket_system, user_data: dict):
        super().__init__(title="🎫 Crear Ticket")
        self.ticket_system = ticket_system
        self.user_data = user_data

    subject = discord.ui.TextInput(
        label="Asunto del ticket",
        placeholder="Describe brevemente el motivo de tu ticket...",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    description = discord.ui.TextInput(
        label="Descripción detallada",
        placeholder="Proporciona más detalles sobre tu consulta o problema...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar creación del ticket con asunto"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear el ticket con asunto
            success = await self.ticket_system.create_ticket_with_subject(
                interaction.user, 
                interaction.guild, 
                self.user_data,
                self.subject.value,
                self.description.value
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Ticket creado",
                    description=f"Tu ticket **{self.subject.value}** ha sido creado exitosamente.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Hubo un error al crear tu ticket. Intenta nuevamente.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en modal de ticket: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno. Contacta a un administrador.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)