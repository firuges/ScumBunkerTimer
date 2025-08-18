#!/usr/bin/env python3
"""
Sistema de Registro y Welcome Pack Interactivo
Canal dedicado con botones para una experiencia UX optimizada
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime
from taxi_database import taxi_db
from taxi_config import taxi_config

logger = logging.getLogger(__name__)

class InGameNameModal(discord.ui.Modal, title="🎮 Registro - Nombre InGame"):
    def __init__(self):
        super().__init__()
    
    ingame_name = discord.ui.TextInput(
        label="Nombre del Jugador en SCUM",
        placeholder="Escribe tu nombre de jugador tal como aparece en el juego...",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Procesar el registro con el nombre InGame"""
        await interaction.response.defer(ephemeral=True)
        
        ingame_name = self.ingame_name.value.strip()
        
        # Validaciones básicas
        if len(ingame_name) < 2:
            embed = discord.Embed(
                title="❌ Nombre Inválido",
                description="El nombre debe tener al menos 2 caracteres",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Intentar registrar usuario con nombre InGame
        try:
            success, result = await taxi_db.register_user(
                str(interaction.user.id),
                str(interaction.guild.id),
                interaction.user.name,
                display_name=interaction.user.display_name,
                ingame_name=ingame_name
            )
            
            if success:
                # Dar dinero inicial
                await taxi_db.add_money(interaction.user.id, taxi_config.WELCOME_BONUS)
                
                embed = discord.Embed(
                    title="🎉 ¡Welcome Pack Recibido!",
                    description=f"¡Bienvenido **{ingame_name}**! Has sido registrado exitosamente",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🎮 Jugador SCUM",
                    value=f"`{ingame_name}`",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Dinero Recibido",
                    value=f"${taxi_config.WELCOME_BONUS:,.0f}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎫 Vouchers de Taxi",
                    value="3 viajes gratis",
                    inline=True
                )
                
                embed.add_field(
                    name="🚖 Próximos Pasos",
                    value="• Usa `/taxi_solicitar` para pedir un taxi\n• Usa `/banco_balance` para ver tu dinero\n• Usa `/taxi_zonas` para ver zonas disponibles\n• Usa `/bot_presentacion` para conocer todas las funciones",
                    inline=False
                )
                
                # Auto-desplegar presentación para nuevos usuarios
                try:
                    bot = interaction.client
                    if hasattr(bot, 'get_channel'):
                        presentation_channel = None
                        for channel in interaction.guild.channels:
                            if channel.name.lower() in ['bot-presentation', 'presentacion', 'presentation']:
                                presentation_channel = channel
                                break
                        
                        if presentation_channel:
                            from BunkerAdvice_V2 import BotPresentationView
                            view = BotPresentationView()
                            embed_presentation = view.create_overview_embed()
                            
                            intro_text = f"""
🎉 **¡Bienvenido {ingame_name}!**

Como eres nuevo en nuestro sistema, aquí tienes la presentación completa del bot. Navega por las **7 páginas** usando los botones para conocer todas las funcionalidades.

⬇️ **Usa los botones para explorar**
                            """
                            
                            await presentation_channel.send(
                                content=intro_text, 
                                embed=embed_presentation, 
                                view=view
                            )
                except Exception as e:
                    logger.error(f"Error auto-desplegando presentación: {e}")
                    
            else:
                embed = discord.Embed(
                    title="❌ Error de Registro",
                    description=f"No se pudo registrar: {result}",
                    color=discord.Color.red()
                )
                
            embed.set_footer(text="Sistema de Taxi SCUM • Gracias por registrarte")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en registro con nombre InGame: {e}")
            embed = discord.Embed(
                title="❌ Error Interno",
                description="Hubo un error procesando tu registro. Intenta nuevamente.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class WelcomePackSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channels = {}  # {guild_id: channel_id}

    async def load_channel_configs(self):
        """Cargar configuraciones de canales desde la base de datos y recrear paneles"""
        try:
            from taxi_database import taxi_db
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                if "welcome" in channels:
                    guild_id_int = int(guild_id)
                    channel_id = channels["welcome"]
                    
                    # Cargar en memoria
                    self.welcome_channels[guild_id_int] = channel_id
                    
                    # Recrear panel de bienvenida en el canal
                    await self._recreate_welcome_panel(guild_id_int, channel_id)
                    
                    logger.info(f"Cargada y recreada configuración de welcome para guild {guild_id}: canal {channel_id}")
            
            logger.info(f"Sistema de bienvenida: {len(self.welcome_channels)} canales cargados con paneles recreados")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de bienvenida: {e}")
    
    async def _recreate_welcome_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de bienvenida en un canal específico"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de bienvenida {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Limpiar mensajes anteriores del bot (solo los más recientes)
            try:
                deleted_count = 0
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds:
                        # Solo eliminar si es un embed del sistema de bienvenida
                        for embed in message.embeds:
                            if embed.title and ("Sistema de Bienvenida" in embed.title or "Bienvenido" in embed.title):
                                await message.delete()
                                deleted_count += 1
                                break
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} paneles de bienvenida anteriores del canal {channel_id}")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes de bienvenida anteriores: {cleanup_e}")
            
            # Crear embed de bienvenida
            from taxi_admin import WelcomeSystemView
            
            embed = discord.Embed(
                title="🎉 Sistema de Bienvenida",
                description="Usa `/welcome_registro` para registrarte y `/welcome_status` para consultar tu estado.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🎁 ¿Qué incluye el registro?",
                value="• **Cuenta bancaria** con balance inicial\n• **Welcome pack** con beneficios\n• **Acceso completo** a todos los sistemas\n• **Soporte 24/7** del equipo",
                inline=False
            )
            
            view = WelcomeSystemView()
            await channel.send(embed=embed, view=view)
            logger.info(f"Panel de bienvenida recreado exitosamente en canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel de bienvenida para canal {channel_id}: {e}")

    async def setup_welcome_channel(self, guild_id: int, channel_id: int):
        """Configurar canal de bienvenida con embed interactivo"""
        # Guardar en memoria (para acceso rápido)
        self.welcome_channels[guild_id] = channel_id
        
        # Guardar en base de datos (para persistencia)
        from taxi_database import taxi_db
        await taxi_db.save_channel_config(str(guild_id), "welcome", str(channel_id))
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            return False
        
        # Limpiar mensajes anteriores del bot
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user:
                    await message.delete()
        except:
            pass
        
        # Crear embed principal
        embed = discord.Embed(
            title="🎉 ¡Bienvenido al Sistema SCUM!",
            description="Regístrate para acceder a todas las funcionalidades del servidor",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎁 Welcome Pack Incluye:",
            value=f"""
            ```yaml
            💰 Dinero inicial: ${taxi_config.WELCOME_BONUS:,.0f}
            🎫 Vouchers de taxi: 3 gratis
            ⭐ Trial Premium: 7 días
            🏦 Cuenta bancaria automática
            🚖 Acceso al sistema de taxi
            ```
            """,
            inline=False
        )
        
        embed.add_field(
            name="🔧 Funcionalidades Disponibles:",
            value="""
            🏦 **Sistema Bancario** - Transferencias y gestión de dinero
            🚖 **Sistema de Taxi** - Transporte rápido y seguro
            👨‍✈️ **Registro de Conductor** - Gana dinero transportando jugadores
            📊 **Estadísticas** - Seguimiento de tu actividad
            """,
            inline=False
        )
        
        embed.add_field(
            name="🗺️ Zonas del Mapa:",
            value="""
            🛡️ **Zonas Seguras** - Servicio completo de taxi
            ⚔️ **Zonas de Combate** - Solo recogida de emergencia
            🚫 **Zonas Restringidas** - Sin servicio de taxi
            💼 **Zonas Comerciales** - Servicio prioritario
            """,
            inline=False
        )
        
        embed.set_footer(text="Haz clic en el botón de abajo para registrarte y recibir tu Welcome Pack")
        embed.set_thumbnail(url="https://i.imgur.com/scum_logo.png")  # Cambiar por logo real
        
        # Vista con botones
        view = WelcomePackView()
        
        await channel.send(embed=embed, view=view)
        return True

    # === COMANDOS DE WELCOME PACK ===
    
    @app_commands.command(name="welcome_registro", description="🎁 Registrarse para recibir el welcome pack")
    async def welcome_registro(self, interaction: discord.Interaction):
        """Registrarse para recibir el welcome pack"""
        # Verificar si el sistema está habilitado
        if not taxi_config.FEATURE_ENABLED or not taxi_config.WELCOME_PACK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Deshabilitado",
                description="El sistema de welcome pack está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar si ya está registrado
        user_exists = await taxi_db.user_exists(interaction.user.id)
        if user_exists:
            embed = discord.Embed(
                title="ℹ️ Ya Registrado",
                description="Ya tienes una cuenta en el sistema SCUM",
                color=discord.Color.blue()
            )
            
            # Mostrar balance actual
            balance = await taxi_db.get_user_balance(interaction.user.id)
            embed.add_field(
                name="💰 Balance Actual",
                value=f"${balance:,.0f}",
                inline=True
            )
            
            embed.set_footer(text="Sistema de Taxi SCUM • Ya registrado")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para pedir nombre InGame
        modal = InGameNameModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="welcome_status", description="📊 Ver tu estado de registro")
    async def welcome_status(self, interaction: discord.Interaction):
        """Ver estado de registro del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        # Obtener información del usuario
        user_exists = await taxi_db.get_user(interaction.user.id)
        if not user_exists:
            embed = discord.Embed(
                title="❌ Sin Registro",
                description="No estás registrado en el sistema. Usa `/welcome_registro` para registrarte",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener balance
        balance = await taxi_db.get_user_balance(interaction.user.id)
        
        # Obtener estadísticas de taxis
        stats = await taxi_db.get_user_taxi_stats(interaction.user.id)
        
        embed = discord.Embed(
            title="📊 Tu Estado en el Sistema SCUM",
            description=f"Información de {interaction.user.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💰 Balance",
            value=f"${balance:,.0f}",
            inline=True
        )
        
        embed.add_field(
            name="🚖 Viajes Realizados",
            value=f"{stats.get('total_trips', 0)} viajes",
            inline=True
        )
        
        embed.add_field(
            name="👤 Tipo de Usuario",
            value=user_exists.get('user_type', 'player').title(),
            inline=True
        )
        
        embed.add_field(
            name="🗓️ Registrado",
            value=f"<t:{int(user_exists.get('created_at', datetime.now()).timestamp())}:D>",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Servicios Disponibles",
            value="• Sistema de Taxi 🚖\n• Sistema Bancario 🏦\n• Zona PVE/PVP 🗺️",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Taxi SCUM")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # Comando setup temporalmente deshabilitado - requiere migración completa
    # TODO: Migrar completamente a app_commands
    pass

class WelcomePackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Vista persistente

    @discord.ui.button(
        label="🎁 Recibir Welcome Pack", 
        style=discord.ButtonStyle.primary,
        emoji="🎉",
        custom_id="welcome_pack_claim"
    )
    async def claim_welcome_pack(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón para reclamar welcome pack"""
        await interaction.response.defer(ephemeral=True)
        
        # Verificar si el sistema está habilitado
        if not taxi_config.FEATURE_ENABLED or not taxi_config.WELCOME_PACK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Deshabilitado",
                description="El sistema de welcome pack está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Intentar registrar usuario
        success, result = await taxi_db.register_user(
            str(interaction.user.id),
            str(interaction.guild.id),
            interaction.user.name,
            interaction.user.display_name
        )
        
        if not success:
            if "ya registrado" in result.get("error", "").lower():
                # Usuario ya registrado, mostrar información
                user_data = await taxi_db.get_user_by_discord_id(
                    str(interaction.user.id), 
                    str(interaction.guild.id)
                )
                
                embed = discord.Embed(
                    title="ℹ️ Ya Estás Registrado",
                    description="Tu welcome pack ya fue reclamado anteriormente",
                    color=discord.Color.blue()
                )
                
                if user_data:
                    embed.add_field(
                        name="💳 Tu Cuenta",
                        value=f"**Número:** `{user_data['account_number']}`\n**Saldo:** `${user_data['balance']:,.2f}`",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📅 Registro",
                        value=f"Te registraste: <t:{int(datetime.fromisoformat(user_data['joined_at']).timestamp())}:R>",
                        inline=False
                    )
                
                embed.add_field(
                    name="🚀 Próximos Pasos",
                    value="Visita <#🏦┃bank-service> para gestionar tu dinero\nVisita <#🚖┃taxi-service> para usar el taxi",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de Registro",
                    description=f"Error: {result.get('error', 'Error desconocido')}",
                    color=discord.Color.red()
                )
        else:
            # Registro exitoso
            embed = discord.Embed(
                title="🎉 ¡Welcome Pack Recibido!",
                description="¡Te has registrado exitosamente en el sistema!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Dinero Recibido",
                value=f"```diff\n+ ${result['welcome_bonus']:,.2f}\n```",
                inline=True
            )
            
            embed.add_field(
                name="💳 Tu Cuenta Bancaria",
                value=f"```\nNúmero: {result['account_number']}\nSaldo: ${result['welcome_bonus']:,.2f}\n```",
                inline=True
            )
            
            embed.add_field(
                name="🎁 Elementos del Pack",
                value=f"""
                ```yaml
                💵 Dinero: ${result['items']['cash']:,.0f}
                🎫 Vouchers: {result['items']['taxi_vouchers']}
                ⭐ Premium: {result['items']['premium_trial']} días
                ```
                """,
                inline=False
            )
            
            embed.add_field(
                name="🚀 Próximos Pasos",
                value="""
                🏦 Visita el canal bancario para transferencias
                🚖 Usa el servicio de taxi para moverte
                👨‍✈️ Regístrate como conductor para ganar dinero
                """,
                inline=False
            )
            
            embed.set_footer(text="¡Disfruta tu experiencia en el servidor!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="📊 Ver Estadísticas", 
        style=discord.ButtonStyle.secondary,
        emoji="📈",
        custom_id="view_stats"
    )
    async def view_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón para ver estadísticas del sistema"""
        await interaction.response.defer(ephemeral=True)
        
        # Obtener estadísticas del guild
        stats = await taxi_db.get_system_stats(str(interaction.guild.id))
        
        embed = discord.Embed(
            title="📊 Estadísticas del Sistema",
            description=f"Estadísticas de **{interaction.guild.name}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Usuarios",
            value=f"""
            ```yaml
            Registrados: {stats['total_users']:,}
            Conductores: {stats['total_drivers']:,}
            Activos: {stats['active_drivers']:,}
            ```
            """,
            inline=True
        )
        
        embed.add_field(
            name="🚖 Viajes",
            value=f"""
            ```yaml
            Completados: {stats['completed_rides']:,}
            Promedio/día: {stats['completed_rides'] // 30:,}
            ```
            """,
            inline=True
        )
        
        embed.add_field(
            name="💰 Economía",
            value=f"""
            ```yaml
            En circulación: ${stats['total_money']:,.0f}
            Promedio/usuario: ${stats['total_money'] / max(stats['total_users'], 1):,.0f}
            ```
            """,
            inline=True
        )
        
        # Estado del sistema
        status_emoji = "🟢" if taxi_config.FEATURE_ENABLED else "🔴"
        taxi_emoji = "🟢" if taxi_config.TAXI_ENABLED else "🔴"
        bank_emoji = "🟢" if taxi_config.BANK_ENABLED else "🔴"
        
        embed.add_field(
            name="⚙️ Estado del Sistema",
            value=f"""
            {status_emoji} Sistema General
            {taxi_emoji} Servicio de Taxi
            {bank_emoji} Sistema Bancario
            """,
            inline=False
        )
        
        embed.set_footer(text=f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="ℹ️ Información", 
        style=discord.ButtonStyle.secondary,
        emoji="❓",
        custom_id="info_button"
    )
    async def info_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón de información del sistema"""
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="ℹ️ Información del Sistema",
            description="Todo lo que necesitas saber sobre el sistema SCUM",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎁 Welcome Pack",
            value=f"""
            • Recibes **${taxi_config.WELCOME_BONUS:,.0f}** al registrarte
            • Solo se puede reclamar **una vez** por usuario
            • Incluye cuenta bancaria automática
            • Acceso inmediato a todos los servicios
            """,
            inline=False
        )
        
        embed.add_field(
            name="🏦 Sistema Bancario",
            value="""
            • Transferencias entre jugadores
            • Historial de transacciones
            • Cuentas seguras y protegidas
            • Comisiones automáticas del taxi
            """,
            inline=False
        )
        
        embed.add_field(
            name="🚖 Sistema de Taxi",
            value=f"""
            • Tarifa base: **${taxi_config.TAXI_BASE_RATE}**
            • Por kilómetro: **${taxi_config.TAXI_PER_KM_RATE}**
            • Conductor recibe: **{taxi_config.DRIVER_COMMISSION*100:.0f}%**
            • Respeta zonas PVP/PVE del servidor
            """,
            inline=False
        )
        
        embed.add_field(
            name="🗺️ Zonas del Mapa",
            value="""
            🛡️ **Seguras** - Ciudad, puertos (servicio completo)
            ⚔️ **Combate** - Bunkers (solo recogida)
            🚫 **Restringidas** - Base militar (sin servicio)
            💼 **Comerciales** - Aeropuerto (servicio prioritario)
            """,
            inline=False
        )
        
        embed.add_field(
            name="👨‍✈️ Ser Conductor",
            value="""
            • Regístrate con `/driver register`
            • Elige tu tipo de vehículo
            • Ponte online/offline cuando quieras
            • Gana dinero transportando jugadores
            • Sistema de calificaciones y niveles
            """,
            inline=False
        )
        
        embed.set_footer(text="Para soporte adicional, contacta a los administradores del servidor")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    # === COMANDO DE ADMINISTRACIÓN ===
    
    @app_commands.command(name="welcome_admin_setup", description="[ADMIN] Configurar sistema de bienvenida")
    @app_commands.describe(canal="Canal donde configurar el sistema de bienvenida")
    @app_commands.default_permissions(administrator=True)
    async def admin_setup_welcome(self, interaction: discord.Interaction, canal: discord.TextChannel):
        """Configurar canal de bienvenida"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = await self.setup_welcome_channel(interaction.guild.id, canal.id)
            
            if success:
                embed = discord.Embed(
                    title="🎉 Sistema de Bienvenida Configurado",
                    description=f"El sistema de bienvenida ha sido configurado en {canal.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="📍 Canal", value=canal.mention, inline=True)
                embed.add_field(name="💰 Welcome Bonus", value=f"${taxi_config.WELCOME_BONUS:,}", inline=True)
                embed.add_field(name="⚙️ Estado", value="🟢 Activo", inline=True)
                embed.add_field(
                    name="🎁 Welcome Pack Incluye",
                    value=f"• ${taxi_config.WELCOME_BONUS:,} dinero inicial\n• Cuenta bancaria automática\n• Acceso al sistema de taxi\n• 3 vouchers de taxi gratis",
                    inline=False
                )
                embed.add_field(
                    name="🚀 Comandos Disponibles",
                    value="• `/welcome_registro` - Registrarse\n• `/welcome_status` - Ver estado\n• Los usuarios verán botones interactivos en el canal",
                    inline=False
                )
                embed.add_field(
                    name="💡 Próximos Pasos",
                    value="1. Verifica que aparecen los botones en el canal\n2. Prueba el registro con `/welcome_registro`\n3. Configura permisos si es necesario",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de Configuración",
                    description="No se pudo configurar el sistema de bienvenida. Inténtalo de nuevo.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error configurando welcome: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error durante la configuración: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomePackSystem(bot))
