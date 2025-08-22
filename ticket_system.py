#!/usr/bin/env python3
"""
Sistema de Tickets Independiente
Permite a usuarios crear canales privados para comunicarse con administradores
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime
from typing import Optional, List

from ticket_database import TicketDatabase
from ticket_views import CreateTicketView, CloseTicketView, TicketSubjectModal
from core.user_manager import UserManager

logger = logging.getLogger(__name__)

class TicketSystem(commands.Cog):
    """Sistema completo de tickets"""
    
    def __init__(self, bot, db_path: str = "scum_main.db"):
        self.bot = bot
        self.db_path = db_path
        self.ticket_db = TicketDatabase(db_path)
        self.user_manager = UserManager(db_path)
        self.ticket_channels = {}  # {guild_id: channel_id} - Para paneles principales
        
        # Configuración
        self.TICKET_CATEGORY_NAME = "🎫 Tickets"
        self.TICKET_LOG_CHANNEL = "ticket-logs"
        
    async def cog_load(self):
        """Inicializar al cargar el cog"""
        await self.ticket_db.initialize()
        await self.ticket_db.initialize_ticket_channels_table()
        logger.info("✅ Sistema de Tickets cargado correctamente")
        # Cargar configuraciones de canales (solo paneles principales)
        await self.load_channel_configs()
        
    async def load_channel_configs(self):
        """Cargar configuraciones de canales principales de tickets y recrear paneles"""
        try:
            from taxi_database import taxi_db
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                if "tickets" in channels:  # Solo canales principales de tickets
                    guild_id_int = int(guild_id)
                    channel_id = channels["tickets"]
                    
                    # Guardar en memoria
                    self.ticket_channels[guild_id_int] = channel_id
                    
                    # Obtener canal
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        # Limpiar mensajes anteriores del bot (solo del panel principal)
                        try:
                            deleted_count = 0
                            async for message in channel.history(limit=20):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)
                            
                            if deleted_count > 0:
                                logger.info(f"🧹 {deleted_count} mensajes anteriores eliminados del canal de tickets {channel.name}")
                        except Exception as cleanup_e:
                            logger.warning(f"⚠️ No se pudo limpiar canal de tickets {channel.name}: {cleanup_e}")
                        
                        # Recrear panel de tickets
                        success = await self._create_ticket_panel(channel)
                        if success:
                            logger.info(f"✅ Panel de tickets restaurado en {channel.name} (Guild: {guild_id_int})")
                        else:
                            logger.warning(f"⚠️ Error restaurando panel de tickets en {channel.name}")
                    else:
                        logger.warning(f"❌ Canal de tickets configurado no encontrado: {channel_id}")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de canales de tickets: {e}")
    
    async def _create_ticket_panel(self, channel: discord.TextChannel) -> bool:
        """Crear panel de tickets en un canal específico"""
        try:
            # Crear embed del panel
            embed = discord.Embed(
                title="🎫 Sistema de Tickets",
                description=(
                    "¿Necesitas ayuda? ¡Crea un ticket!\n\n"
                    "**¿Qué es un ticket?**\n"
                    "Un canal privado donde puedes comunicarte directamente con los administradores.\n\n"
                    "**¿Cómo funciona?**\n"
                    "1. Haz clic en **🎫 Crear Ticket**\n"
                    "2. Se creará un canal privado solo para ti\n"
                    "3. Explica tu consulta o problema\n"
                    "4. Un administrador te ayudará\n"
                    "5. El ticket se cerrará cuando esté resuelto\n\n"
                    "**Reglas:**\n"
                    "• Solo puedes tener 1 ticket activo\n"
                    "• Debes estar registrado en el sistema\n"
                    "• Sé claro y respetuoso"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="Sistema de Tickets SCUM Bot")
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
            
            # Crear vista con botón
            view = CreateTicketView(self)
            
            # Enviar panel
            message = await channel.send(embed=embed, view=view)
            view.message = message
            
            # Guardar el message_id del panel principal de tickets para restaurar la vista
            await self.ticket_db.set_ticket_panel_message_id(
                str(channel.guild.id), str(channel.id), str(message.id)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando panel de tickets: {e}")
            return False
    @commands.Cog.listener()
    async def on_ready(self):
        """Ejecutar cuando el bot esté completamente listo"""
        logger.info("🚀 Bot ready - Iniciando restauración de vistas dinámicas de tickets...")
        # Esperar un poco más por si acaso
        await asyncio.sleep(2)
        # Solo restaurar vistas de tickets dinámicos (no tocar paneles principales)
        await self.restore_active_ticket_views()

    async def restore_active_ticket_views(self):
        """Recorrer canales de tickets activos y restaurar vistas persistentes"""
        logger.info("🔄 Iniciando restauración de vistas persistentes de tickets...")
        
        panels_restored = 0
        tickets_restored = 0
        
        # Restaurar vista persistente del panel principal de tickets
        logger.info(f"🏛️ Restaurando paneles para {len(self.bot.guilds)} guilds...")
        logger.info(f"📋 Guilds disponibles: {[f'{g.name}({g.id})' for g in self.bot.guilds]}")
        
        for guild in self.bot.guilds:
            try:
                panel_info = await self.ticket_db.get_ticket_panel_message_id(str(guild.id))
                if panel_info:
                    channel_id = panel_info['channel_id']
                    message_id = panel_info['message_id']
                    channel = guild.get_channel(int(channel_id)) if channel_id else None
                    
                    if channel and message_id:
                        from ticket_views import CreateTicketView
                        view = CreateTicketView(self)
                        self.bot.add_view(view, message_id=int(message_id))
                        logger.info(f"✅ Panel de tickets restaurado: Guild {guild.name}, Canal {channel.name}")
                        panels_restored += 1
                    else:
                        logger.warning(f"❌ Panel configurado pero canal no encontrado: Guild {guild.name}, Canal ID {channel_id}")
                else:
                    logger.debug(f"ℹ️ No hay panel configurado para guild {guild.name}")
            except Exception as e:
                logger.error(f"❌ Error restaurando panel para guild {guild.name}: {e}")
        
        # Restaurar vistas persistentes de tickets activos
        active_channels = await self.ticket_db.get_active_ticket_channels()
        logger.info(f"🎫 Restaurando {len(active_channels)} tickets activos...")
        
        for row in active_channels:
            # row: (ticket_id, channel_id, user_id, guild_id, message_id, created_at)
            channel_id = row[1]
            guild_id = row[3]
            message_id = row[4]
            
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    logger.warning(f"❌ Guild {guild_id} no encontrado para ticket {channel_id}")
                    logger.info(f"🔍 Intentando obtener guild por API...")
                    
                    try:
                        guild = await self.bot.fetch_guild(int(guild_id))
                        logger.info(f"✅ Guild obtenido por API: {guild.name}")
                    except Exception as api_e:
                        logger.error(f"❌ Guild {guild_id} no accesible por API: {api_e}")
                        logger.warning(f"🗑️ El bot probablemente no está en este servidor, limpiando registro...")
                        await self.ticket_db.remove_ticket_channel(str(channel_id))
                        continue
                
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    # Intentar obtener por API
                    try:
                        channel = await guild.fetch_channel(int(channel_id))
                        logger.info(f"🔍 Canal {channel_id} obtenido por API")
                    except Exception:
                        logger.warning(f"❌ Canal {channel_id} no existe, limpiando registro...")
                        await self.ticket_db.remove_ticket_channel(str(channel_id))
                        continue
                
                if channel and message_id:
                    ticket_info = await self.ticket_db.get_ticket_by_channel(str(channel_id))
                    
                    if ticket_info:
                        ticket_data = {
                            'ticket_id': ticket_info['ticket_id'],
                            'ticket_number': ticket_info['ticket_number'],
                            'discord_id': ticket_info['discord_id'],
                            'channel_id': str(channel_id)
                        }
                        
                        from ticket_views import CloseTicketView
                        view = CloseTicketView(self, ticket_data)
                        self.bot.add_view(view, message_id=int(message_id))
                        
                        logger.info(f"✅ Ticket #{ticket_info['ticket_number']:04d} restaurado: {channel.name}")
                        tickets_restored += 1
                    else:
                        logger.warning(f"❌ Ticket info no encontrado para canal {channel_id}, limpiando...")
                        await self.ticket_db.remove_ticket_channel(str(channel_id))
                        
            except Exception as e:
                logger.error(f"❌ Error restaurando ticket {channel_id}: {e}")
        
        logger.info(f"🎯 Restauración completada: {panels_restored} paneles, {tickets_restored} tickets")

    @app_commands.command(name="ticket_debug_restore", description="[DEBUG] Forzar restauración de vistas de tickets")
    @app_commands.default_permissions(administrator=True)
    async def debug_restore_views(self, interaction: discord.Interaction):
        """Comando de debug para forzar restauración de vistas"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            embed = discord.Embed(
                title="🔧 Debug - Restauración de Vistas",
                description="Iniciando diagnóstico y restauración forzada...",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Información del bot
            bot_guilds = [f"{g.name} ({g.id})" for g in self.bot.guilds]
            logger.info(f"[DEBUG] Bot está en {len(self.bot.guilds)} guilds: {bot_guilds}")
            
            # Información de tickets activos
            active_channels = await self.ticket_db.get_active_ticket_channels()
            logger.info(f"[DEBUG] Canales activos en BD: {len(active_channels)}")
            
            for row in active_channels:
                channel_id, guild_id = row[1], row[3]
                logger.info(f"[DEBUG] - Canal {channel_id} en Guild {guild_id}")
            
            # Ejecutar restauración
            await self.restore_active_ticket_views()
            
            # Resultado
            result_embed = discord.Embed(
                title="✅ Debug Completado",
                description="Revisa los logs para detalles de la restauración.",
                color=discord.Color.green()
            )
            result_embed.add_field(
                name="Información",
                value=f"• Guilds del bot: {len(self.bot.guilds)}\n• Tickets activos en BD: {len(active_channels)}",
                inline=False
            )
            
            await interaction.edit_original_response(embed=result_embed)
            
        except Exception as e:
            logger.error(f"Error en debug restore: {e}")
            error_embed = discord.Embed(
                title="❌ Error en Debug",
                description=f"Error: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=error_embed)

    @app_commands.command(name="ticket_setup", description="Configurar panel de tickets (Solo Admin)")
    @app_commands.describe(
        channel="Canal donde se colocará el panel de tickets"
    )
    async def ticket_setup(self, interaction: discord.Interaction, 
                          channel: Optional[discord.TextChannel] = None):
        """Configurar panel de creación de tickets"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden configurar el sistema de tickets.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Usar canal actual si no se especifica
            target_channel = channel or interaction.channel
            
            # Crear embed del panel
            embed = discord.Embed(
                title="🎫 Sistema de Tickets",
                description=(
                    "¿Necesitas ayuda? ¡Crea un ticket!\n\n"
                    "**¿Qué es un ticket?**\n"
                    "Un canal privado donde puedes comunicarte directamente con los administradores.\n\n"
                    "**¿Cómo funciona?**\n"
                    "1. Haz clic en **🎫 Crear Ticket**\n"
                    "2. Se creará un canal privado solo para ti\n"
                    "3. Explica tu consulta o problema\n"
                    "4. Un administrador te ayudará\n"
                    "5. El ticket se cerrará cuando esté resuelto\n\n"
                    "**Reglas:**\n"
                    "• Solo puedes tener 1 ticket activo\n"
                    "• Debes estar registrado en el sistema\n"
                    "• Sé claro y respetuoso"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="Sistema de Tickets SCUM Bot")
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
            
            # Crear vista con botón
            view = CreateTicketView(self)
            
            # Enviar panel
            message = await target_channel.send(embed=embed, view=view)
            view.message = message
            
            # Guardar el message_id del panel principal de tickets para restaurar la vista
            await self.ticket_db.set_ticket_panel_message_id(
                str(target_channel.guild.id), str(target_channel.id), str(message.id)
            )
            
            # Confirmar al admin
            success_embed = discord.Embed(
                title="✅ Panel configurado",
                description=f"El panel de tickets ha sido configurado en {target_channel.mention}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
            logger.info(f"Panel de tickets configurado en {target_channel.name} por {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error configurando panel de tickets: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error al configurar el panel de tickets.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def create_ticket(self, user: discord.Member, guild: discord.Guild, 
                          user_data: dict, subject: str = None) -> bool:
        """Crear nuevo ticket"""
        try:
            # Verificar permisos del bot
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                logger.error("Bot member not found in guild")
                return False
            
            # Verificar permisos necesarios
            required_permissions = [
                'manage_channels',  # Para crear canales
                'manage_permissions'  # Para configurar overwrites
            ]
            
            missing_permissions = []
            for perm_name in required_permissions:
                if not getattr(bot_member.guild_permissions, perm_name):
                    missing_permissions.append(perm_name)
            
            if missing_permissions:
                logger.error(f"Bot missing permissions: {missing_permissions}")
                return False
            # Obtener siguiente número de ticket
            ticket_number = await self.ticket_db.get_next_ticket_number(str(guild.id))
            
            # Buscar o crear categoría de tickets
            category = discord.utils.get(guild.categories, name=self.TICKET_CATEGORY_NAME)
            if not category:
                category = await guild.create_category(
                    self.TICKET_CATEGORY_NAME,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(view_channel=False)
                    }
                )
            
            # Configurar permisos del canal
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )
            }
            
            # Agregar permisos para administradores
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        attach_files=True,
                        embed_links=True,
                        manage_messages=True
                    )
            
            # Crear canal del ticket
            channel_name = f"ticket-{ticket_number:04d}"
            ticket_channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket #{ticket_number:04d} - {user.display_name} ({user.id})"
            )
            
            # Guardar en base de datos
            ticket_id = await self.ticket_db.create_ticket(
                str(user_data['user_id']),
                str(user.id),
                str(guild.id),
                str(ticket_channel.id),
                ticket_number,
                subject
            )
            
            # Crear embed de bienvenida
            welcome_embed = discord.Embed(
                title=f"🎫 Ticket #{ticket_number:04d}",
                description=(
                    f"¡Hola {user.mention}! Bienvenido a tu ticket.\n\n"
                    f"**Usuario:** {user.display_name}\n"
                    f"**Creado:** <t:{int(datetime.now().timestamp())}:F>\n"
                    f"**Asunto:** {subject or 'No especificado'}\n\n"
                    "**¿Qué hacer ahora?**\n"
                    "• Explica tu consulta o problema con detalle\n"
                    "• Un administrador te ayudará pronto\n"
                    "• Mantén este canal organizado y claro\n\n"
                    "**Para cerrar el ticket**, haz clic en el botón de abajo."
                ),
                color=discord.Color.blue()
            )
            welcome_embed.set_footer(text=f"Ticket ID: {ticket_id}")
            
            # Crear vista con botón de cerrar
            ticket_data = {
                'ticket_id': ticket_id,
                'ticket_number': ticket_number,
                'discord_id': str(user.id),
                'channel_id': str(ticket_channel.id)
            }
            close_view = CloseTicketView(self, ticket_data)
            
            # Enviar mensaje de bienvenida
            welcome_message = await ticket_channel.send(
                content=f"{user.mention}",
                embed=welcome_embed, 
                view=close_view
            )
            close_view.message = welcome_message
            
            # Guardar canal en tabla ticket_channels
            await self.ticket_db.add_ticket_channel(
                str(ticket_channel.id), str(user.id), str(guild.id), str(welcome_message.id)
            )
            
            # Log del ticket creado
            await self._log_ticket_action(
                guild, "created", ticket_number, user, 
                f"Canal: {ticket_channel.mention}, Asunto: {subject or 'No especificado'}"
            )
            
            logger.info(f"Ticket #{ticket_number:04d} creado para {user} en {guild.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando ticket: {e}")
            return False

    async def create_ticket_with_subject(self, user: discord.Member, guild: discord.Guild,
                                       user_data: dict, subject: str, description: str = None) -> bool:
        """Crear ticket con asunto especificado"""
        return await self.create_ticket(user, guild, user_data, subject)

    async def close_ticket(self, channel: discord.TextChannel, closed_by: str, 
                          ticket_data: dict) -> bool:
        """Cerrar ticket"""
        try:
            # Cerrar en base de datos
            success = await self.ticket_db.close_ticket(
                ticket_data['ticket_id'], 
                closed_by
            )
            
            if not success:
                return False
            
            # Limpiar tabla ticket_channels
            await self.ticket_db.remove_ticket_channel(str(channel.id))
            
            # Log del ticket cerrado
            await self._log_ticket_action(
                channel.guild, "closed", ticket_data['ticket_number'], 
                channel.guild.get_member(int(closed_by)) or "Sistema",
                f"Canal: {channel.mention}"
            )
            
            # Eliminar canal después de 5 segundos
            async def delete_channel():
                await asyncio.sleep(5)
                try:
                    await channel.delete(reason=f"Ticket #{ticket_data['ticket_number']} cerrado")
                    logger.info(f"Canal {channel.name} eliminado exitosamente")
                except Exception as e:
                    logger.error(f"Error eliminando canal {channel.name}: {e}")
            
            asyncio.create_task(delete_channel())
            
            logger.info(f"Ticket #{ticket_data['ticket_number']} cerrado por {closed_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error cerrando ticket: {e}")
            return False

    async def _log_ticket_action(self, guild: discord.Guild, action: str, 
                               ticket_number: int, user, details: str = ""):
        """Log de acciones de tickets"""
        try:
            log_channel = discord.utils.get(guild.text_channels, name=self.TICKET_LOG_CHANNEL)
            if not log_channel:
                return
            
            color_map = {
                'created': discord.Color.green(),
                'closed': discord.Color.red(),
                'modified': discord.Color.orange()
            }
            
            embed = discord.Embed(
                title=f"🎫 Ticket {action.title()}",
                color=color_map.get(action, discord.Color.blue()),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Ticket", 
                value=f"#{ticket_number:04d}", 
                inline=True
            )
            embed.add_field(
                name="Usuario", 
                value=f"{user.mention}\n({user})", 
                inline=True
            )
            embed.add_field(
                name="Acción", 
                value=action.title(), 
                inline=True
            )
            
            if details:
                embed.add_field(
                    name="Detalles", 
                    value=details, 
                    inline=False
                )
            
            await log_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error enviando log de ticket: {e}")

    @app_commands.command(name="ticket_close", description="Cerrar un ticket específico (Solo Admin)")
    @app_commands.describe(
        ticket_number="Número del ticket a cerrar"
    )
    async def admin_close_ticket(self, interaction: discord.Interaction, ticket_number: int):
        """Cerrar ticket por número (admin)"""
        
        # Verificar permisos
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden usar este comando.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Buscar ticket
            ticket_data = await self.ticket_db.get_ticket_by_number(
                ticket_number, str(interaction.guild.id)
            )
            
            if not ticket_data:
                embed = discord.Embed(
                    title="❌ Ticket no encontrado",
                    description=f"No se encontró el ticket #{ticket_number:04d}.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if ticket_data['status'] != 'open':
                embed = discord.Embed(
                    title="⚠️ Ticket ya cerrado",
                    description=f"El ticket #{ticket_number:04d} ya está cerrado.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener canal
            channel = interaction.guild.get_channel(int(ticket_data['channel_id']))
            if not channel:
                # Cerrar en BD pero no hay canal que eliminar
                await self.ticket_db.close_ticket(ticket_data['ticket_id'], str(interaction.user.id))
                embed = discord.Embed(
                    title="✅ Ticket cerrado",
                    description=f"El ticket #{ticket_number:04d} ha sido cerrado (canal ya eliminado).",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Cerrar ticket
            success = await self.close_ticket(channel, str(interaction.user.id), ticket_data)
            
            if success:
                embed = discord.Embed(
                    title="✅ Ticket cerrado",
                    description=f"El ticket #{ticket_number:04d} ha sido cerrado exitosamente.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Hubo un error al cerrar el ticket.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en admin_close_ticket: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="ticket_list", description="Listar tickets activos (Solo Admin)")
    async def list_active_tickets(self, interaction: discord.Interaction):
        """Listar todos los tickets activos del servidor"""
        
        # Verificar permisos
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden usar este comando.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener tickets activos
            active_tickets = await self.ticket_db.get_active_tickets(str(interaction.guild.id))
            stats = await self.ticket_db.get_ticket_stats(str(interaction.guild.id))
            
            # Crear embed
            embed = discord.Embed(
                title="🎫 Tickets Activos",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Estadísticas",
                value=(
                    f"**Total:** {stats['total']}\n"
                    f"**Activos:** {stats['active']}\n"
                    f"**Cerrados:** {stats['closed']}"
                ),
                inline=False
            )
            
            if not active_tickets:
                embed.add_field(
                    name="Sin tickets activos",
                    value="No hay tickets activos en este momento.",
                    inline=False
                )
            else:
                ticket_list = ""
                for ticket in active_tickets[:10]:  # Máximo 10 para evitar límite de caracteres
                    channel = interaction.guild.get_channel(int(ticket['channel_id']))
                    channel_mention = channel.mention if channel else "Canal eliminado"
                    ticket_list += (
                        f"**#{ticket['ticket_number']:04d}** - {ticket['username'] or 'Usuario desconocido'}\n"
                        f"Canal: {channel_mention}\n"
                        f"Asunto: {ticket['subject'] or 'No especificado'}\n"
                        f"Creado: <t:{int(datetime.fromisoformat(ticket['created_at']).timestamp())}:R>\n\n"
                    )
                
                embed.add_field(
                    name=f"Tickets Activos ({len(active_tickets)})",
                    value=ticket_list[:1024],  # Límite de Discord
                    inline=False
                )
                
                if len(active_tickets) > 10:
                    embed.add_field(
                        name="Nota",
                        value=f"Mostrando 10 de {len(active_tickets)} tickets. Usa comandos específicos para ver más.",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en list_active_tickets: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno al obtener los tickets.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function para cargar el cog"""
    await bot.add_cog(TicketSystem(bot))