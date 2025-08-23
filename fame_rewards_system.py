#!/usr/bin/env python3
"""
Sistema de Fame Point Rewards
Maneja reclamaciones de puntos de fama con ranking y notificaciones para admins
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict

from fame_rewards_database import FameRewardsDatabase
from fame_rewards_views import FameRewardsView, AdminFameNotificationView
from core.user_manager import UserManager

logger = logging.getLogger(__name__)

class FameRewardsSystem(commands.Cog):
    """Sistema completo de Fame Point Rewards"""
    
    def __init__(self, bot, db_path: str = "scum_main.db"):
        self.bot = bot
        self.db_path = db_path
        self.fame_db = FameRewardsDatabase(db_path)
        self.user_manager = UserManager(db_path)
        self.fame_channels = {}  # {guild_id: channel_id} - Para paneles principales
        self.notification_channels = {}  # {guild_id: channel_id} - Para notificaciones de admin
        self.rewards_configs = {}  # {guild_id: {fame_amount: reward_description}} - Configuración de premios
        
    async def cog_load(self):
        """Inicializar al cargar el cog"""
        await self.fame_db.initialize()
        logger.info("✅ Sistema de Fame Point Rewards cargado correctamente")
        # Cargar configuraciones de canales
        await self.load_channel_configs()

    async def load_channel_configs(self):
        """Cargar configuraciones de canales de fame rewards y recrear paneles"""
        try:
            from taxi_database import taxi_db
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                guild_id_int = int(guild_id)
                
                # Canal principal de fame rewards
                if "fame_rewards" in channels:
                    channel_id = channels["fame_rewards"]
                    self.fame_channels[guild_id_int] = channel_id
                    
                    # Obtener canal y recrear panel
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await self._recreate_fame_rewards_panel(guild_id_int, channel_id)
                        logger.info(f"✅ Panel de Fame Rewards restaurado en {channel.name} (Guild: {guild_id_int})")
                    else:
                        logger.warning(f"❌ Canal de fame_rewards configurado no encontrado: {channel_id}")
                
                # Canal de notificaciones de admin
                if "fame_notifications" in channels:
                    notification_channel_id = channels["fame_notifications"]
                    self.notification_channels[guild_id_int] = notification_channel_id
                    logger.info(f"✅ Canal de notificaciones de fama configurado: Guild {guild_id_int}, Canal {notification_channel_id}")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de canales de fame rewards: {e}")

    async def _recreate_fame_rewards_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de fame rewards en un canal específico"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            # Limpiar mensajes anteriores del bot
            try:
                deleted_count = 0
                async for message in channel.history(limit=20):
                    if message.author == self.bot.user:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.1)
                
                if deleted_count > 0:
                    logger.info(f"🧹 {deleted_count} mensajes anteriores eliminados del canal de Fame Rewards {channel.name}")
            except Exception as cleanup_e:
                logger.warning(f"⚠️ No se pudo limpiar canal de Fame Rewards {channel.name}: {cleanup_e}")
            
            # Recrear panel
            success = await self._create_fame_rewards_panel(channel)
            if not success:
                logger.warning(f"⚠️ Error recreando panel de Fame Rewards en {channel.name}")
                
        except Exception as e:
            logger.error(f"Error recreando panel de Fame Rewards: {e}")

    async def _create_fame_rewards_panel(self, channel: discord.TextChannel) -> bool:
        """Crear panel de fame rewards en un canal específico"""
        try:
            # Obtener configuración de valores de fama para este guild
            fame_values = await self.fame_db.get_fame_config(str(channel.guild.id))
            
            # Obtener top 10 actual
            top_claims = await self.fame_db.get_top_fame_claims(str(channel.guild.id), 10)
            
            # Crear embed principal
            embed = discord.Embed(
                title="🏆 Fame Point Rewards",
                description=(
                    "**¡Reclama tus premios por puntos de fama!**\n\n"
                    "Este sistema te permite reclamar recompensas basadas en tus puntos de fama SCUM. "
                    "Selecciona la cantidad correspondiente y proporciona evidencia de tu logro.\n\n"
                    "**¿Cómo funciona?**\n"
                    "1️⃣ Selecciona la cantidad de fama que obtuviste\n"
                    "2️⃣ Proporciona una explicación y evidencia\n"
                    "3️⃣ Un administrador revisará y aprobará tu reclamación\n"
                    "4️⃣ ¡Aparecerás en el ranking si es aprobada!\n\n"
                    "**Reglas:**\n"
                    "• Solo una reclamación pendiente por usuario\n"
                    "• Debes estar registrado en el sistema\n"
                    "• Proporciona evidencia válida (screenshots, etc.)\n"
                    "• Sé honesto con las cantidades"
                ),
                color=discord.Color.gold()
            )
            
            # Agregar ranking actual si hay datos
            if top_claims:
                ranking_text = ""
                medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
                
                for i, claim in enumerate(top_claims):
                    medal = medals[i] if i < len(medals) else "🏅"
                    ingame_name = claim['ingame_name'] or "Nombre InGame Desconocido"
                    fame_formatted = f"{claim['fame_amount']:,}"
                    
                    # Formatear fecha
                    try:
                        claimed_date = datetime.fromisoformat(claim['claimed_at'])
                        date_str = claimed_date.strftime("%d/%m/%Y")
                    except:
                        date_str = "Fecha desconocida"
                    
                    ranking_text += f"{medal} **{ingame_name}** - {fame_formatted} FP ({date_str})\n"
                
                embed.add_field(
                    name="🏆 Top 10 Reclamaciones Confirmadas",
                    value=ranking_text[:1024],  # Límite de Discord
                    inline=False
                )
            else:
                embed.add_field(
                    name="🏆 Top 10 Reclamaciones Confirmadas",
                    value="*Aún no hay reclamaciones confirmadas. ¡Sé el primero!*",
                    inline=False
                )
            
            # Mostrar valores disponibles
            fame_values_text = ", ".join([f"{val:,}" for val in fame_values])
            embed.add_field(
                name="⭐ Valores Disponibles",
                value=f"```{fame_values_text} Fame Points```",
                inline=False
            )
            
            embed.set_footer(text="Sistema de Fame Point Rewards • Mantén la honestidad")
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2583/2583329.png")
            
            # Crear vista con selector
            view = FameRewardsView(self, fame_values)
            
            # Enviar panel
            message = await channel.send(embed=embed, view=view)
            view.message = message
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando panel de fame rewards: {e}")
            return False

    async def update_fame_rewards_panel(self, guild_id: str):
        """Actualizar el panel de rankings cuando hay cambios"""
        try:
            guild_id_int = int(guild_id)
            if guild_id_int not in self.fame_channels:
                return
            
            channel_id = self.fame_channels[guild_id_int]
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                await self._recreate_fame_rewards_panel(guild_id_int, channel_id)
            
        except Exception as e:
            logger.error(f"Error actualizando panel de fame rewards: {e}")

    @app_commands.command(name="fame_rewards_setup", description="Configurar panel de Fame Point Rewards (Solo Admin)")
    @app_commands.describe(
        rewards_channel="Canal donde se mostrará el panel de rankings y reclamaciones",
        notifications_channel="Canal donde llegarán las notificaciones para admins"
    )
    async def fame_rewards_setup(self, interaction: discord.Interaction,
                                rewards_channel: Optional[discord.TextChannel] = None,
                                notifications_channel: Optional[discord.TextChannel] = None):
        """Configurar sistema de Fame Point Rewards"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden configurar el sistema de Fame Point Rewards.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Usar canales actuales si no se especifican
            rewards_target = rewards_channel or interaction.channel
            notifications_target = notifications_channel or interaction.channel
            
            # Crear panel de fame rewards
            success = await self._create_fame_rewards_panel(rewards_target)
            
            if success:
                # Guardar configuraciones en memoria
                self.fame_channels[interaction.guild.id] = rewards_target.id
                self.notification_channels[interaction.guild.id] = notifications_target.id
                
                # Confirmar al admin
                embed = discord.Embed(
                    title="✅ Sistema Configurado",
                    description=(
                        f"El sistema de Fame Point Rewards ha sido configurado:\n\n"
                        f"🏆 **Panel principal:** {rewards_target.mention}\n"
                        f"🔔 **Notificaciones:** {notifications_target.mention}\n\n"
                        "Los usuarios ya pueden empezar a reclamar sus premios de fama."
                    ),
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Sistema Fame Point Rewards configurado en {interaction.guild.name} por {interaction.user}")
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Hubo un error al configurar el sistema.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error configurando sistema Fame Point Rewards: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error interno al configurar el sistema.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def send_admin_notification(self, guild: discord.Guild, claim_id: int, 
                                    user: discord.Member, fame_amount: int, 
                                    reason: str, evidence: str) -> bool:
        """Enviar notificación a canal de administradores"""
        try:
            # Obtener canal de notificaciones
            if guild.id not in self.notification_channels:
                logger.warning(f"No hay canal de notificaciones configurado para guild {guild.id}")
                return False
            
            channel_id = self.notification_channels[guild.id]
            channel = guild.get_channel(channel_id)
            
            if not channel:
                logger.warning(f"Canal de notificaciones {channel_id} no encontrado en guild {guild.id}")
                return False
            
            # Crear embed de notificación
            embed = discord.Embed(
                title="🔔 Nueva Reclamación de Fame Points",
                description=(
                    f"**Usuario:** {user.mention} ({user.display_name})\n"
                    f"**Cantidad:** {fame_amount:,} Fame Points\n"
                    f"**ID Reclamación:** #{claim_id:04d}\n"
                    f"**Fecha:** <t:{int(datetime.now().timestamp())}:F>"
                ),
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📝 Razón proporcionada",
                value=reason[:1024],  # Límite de Discord
                inline=False
            )
            
            if evidence:
                embed.add_field(
                    name="🔗 Evidencia",
                    value=evidence[:1024],  # Límite de Discord
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Información del Usuario",
                value=(
                    f"**Discord ID:** {user.id}\n"
                    f"**Miembro desde:** <t:{int(user.joined_at.timestamp())}:D>\n"
                    f"**Cuenta creada:** <t:{int(user.created_at.timestamp())}:D>"
                ),
                inline=False
            )
            
            embed.set_footer(text="Usa los botones de abajo para aprobar o rechazar la reclamación")
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Obtener datos de la reclamación para la vista
            claim_data = await self.fame_db.get_claim_by_id(claim_id)
            if not claim_data:
                logger.error(f"No se pudo obtener datos de la reclamación {claim_id}")
                return False
            
            # Crear vista con botones de admin
            view = AdminFameNotificationView(self, claim_data)
            
            # Enviar notificación
            message = await channel.send(embed=embed, view=view)
            view.message = message
            
            # Actualizar el message_id de la notificación en la base de datos
            import aiosqlite
            async with aiosqlite.connect(self.fame_db.db_path) as db:
                await db.execute(
                    "UPDATE fame_point_claims SET notification_message_id = ? WHERE claim_id = ?",
                    (str(message.id), claim_id)
                )
                await db.commit()
            
            logger.info(f"Notificación de reclamación #{claim_id} enviada a {channel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación de admin: {e}")
            return False

    async def notify_user_claim_result(self, guild: discord.Guild, claim_data: dict, 
                                     result: str, admin_user: discord.Member, 
                                     reject_reason: str = None):
        """Notificar al usuario el resultado de su reclamación"""
        try:
            user = guild.get_member(int(claim_data['discord_id']))
            if not user:
                logger.warning(f"Usuario {claim_data['discord_id']} no encontrado en guild {guild.id}")
                return
            
            if result == "confirmed":
                embed = discord.Embed(
                    title="✅ Reclamación Confirmada",
                    description=(
                        f"¡Felicitaciones! Tu reclamación de **{claim_data['fame_amount']:,} Fame Points** "
                        f"ha sido **aprobada**.\n\n"
                        f"**ID Reclamación:** #{claim_data['claim_id']:04d}\n"
                        f"**Confirmado por:** {admin_user.mention}\n"
                        f"**Fecha:** <t:{int(datetime.now().timestamp())}:F>\n\n"
                        "Ya apareces en el ranking oficial de Fame Point Rewards."
                    ),
                    color=discord.Color.green()
                )
            else:  # rejected
                embed = discord.Embed(
                    title="❌ Reclamación Rechazada",
                    description=(
                        f"Tu reclamación de **{claim_data['fame_amount']:,} Fame Points** "
                        f"ha sido **rechazada**.\n\n"
                        f"**ID Reclamación:** #{claim_data['claim_id']:04d}\n"
                        f"**Rechazado por:** {admin_user.mention}\n"
                        f"**Fecha:** <t:{int(datetime.now().timestamp())}:F>"
                    ),
                    color=discord.Color.red()
                )
                
                if reject_reason:
                    embed.add_field(
                        name="📝 Razón del Rechazo",
                        value=reject_reason,
                        inline=False
                    )
            
            # Intentar enviar DM al usuario
            try:
                await user.send(embed=embed)
                logger.info(f"Notificación de resultado enviada por DM a {user}")
            except discord.Forbidden:
                logger.warning(f"No se pudo enviar DM a {user}, DMs deshabilitados")
            
        except Exception as e:
            logger.error(f"Error notificando resultado al usuario: {e}")

    @app_commands.command(name="fame_config", description="Configurar valores de fama disponibles (Solo Admin)")
    @app_commands.describe(
        values="Valores separados por comas (ej: 100,500,1000,2000,5000,10000,15000)"
    )
    async def configure_fame_values(self, interaction: discord.Interaction, values: str):
        """Configurar valores de fama disponibles para reclamar"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden configurar los valores de fama.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parsear valores
            fame_values = []
            for value_str in values.split(','):
                value_str = value_str.strip()
                try:
                    value = int(value_str)
                    if value > 0:
                        fame_values.append(value)
                except ValueError:
                    continue
            
            if not fame_values:
                embed = discord.Embed(
                    title="❌ Valores inválidos",
                    description="Debes proporcionar al menos un valor numérico válido.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Limitar a máximo 25 valores (límite de Discord para selectors)
            fame_values = fame_values[:25]
            fame_values.sort()  # Ordenar de menor a mayor
            
            # Guardar configuración
            await self.fame_db.set_fame_config(str(interaction.guild.id), fame_values)
            
            # Actualizar panel si existe
            await self.update_fame_rewards_panel(str(interaction.guild.id))
            
            # Confirmar
            values_text = ", ".join([f"{val:,}" for val in fame_values])
            embed = discord.Embed(
                title="✅ Configuración Actualizada",
                description=(
                    f"Los valores de fama disponibles han sido actualizados:\n\n"
                    f"```{values_text}```\n\n"
                    "El panel de Fame Rewards se ha actualizado automáticamente."
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"Valores de fama configurados para guild {interaction.guild.id}: {fame_values}")
            
        except Exception as e:
            logger.error(f"Error configurando valores de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al configurar los valores de fama.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def get_rewards_config(self, guild_id: str) -> dict:
        """Obtener configuración de premios para el guild"""
        try:
            # Intentar cargar desde base de datos primero
            db_rewards = await self.fame_db.get_rewards_config(guild_id)
            
            # Actualizar caché en memoria
            self.rewards_configs[guild_id] = db_rewards
            
            return db_rewards
            
        except Exception as e:
            logger.error(f"Error cargando premios desde BD para guild {guild_id}: {e}")
            # Fallback a valores por defecto en memoria
            return self.rewards_configs.get(guild_id, {
                "100": "🎒 Kit de Supervivencia Básico",
                "500": "🔫 Set de Armas Avanzadas", 
                "1000": "🛡️ Armadura Completa Nivel 3",
                "2000": "🚗 Vehículo Premium",
                "5000": "🏠 Base Fortificada",
                "10000": "👑 Título VIP por 30 días",
                "15000": "💎 Recompensa Épica Personalizada"
            })

    async def save_rewards_config(self, guild_id: str, rewards_config: dict) -> bool:
        """Guardar configuración de premios"""
        try:
            # Guardar en base de datos
            success = await self.fame_db.save_rewards_config(guild_id, rewards_config)
            
            if success:
                # Actualizar caché en memoria solo si BD fue exitosa
                self.rewards_configs[guild_id] = rewards_config
                logger.info(f"✅ Configuración de premios guardada para guild {guild_id}")
            else:
                logger.error(f"❌ Error guardando premios en BD para guild {guild_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error guardando configuración de premios: {e}")
            return False

async def setup(bot):
    """Setup function para cargar el cog"""
    await bot.add_cog(FameRewardsSystem(bot))