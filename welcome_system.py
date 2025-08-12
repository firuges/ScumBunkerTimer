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

class WelcomePackSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channels = {}  # {guild_id: channel_id}

    async def setup_welcome_channel(self, guild_id: int, channel_id: int):
        """Configurar canal de bienvenida con embed interactivo"""
        self.welcome_channels[guild_id] = channel_id
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
            interaction.user.id,
            interaction.user.display_name,
            "player"  # Tipo de usuario por defecto
        )
        
        if success:
            # Dar dinero inicial
            await taxi_db.add_money(interaction.user.id, taxi_config.WELCOME_BONUS)
            
            embed = discord.Embed(
                title="🎉 ¡Welcome Pack Recibido!",
                description="Has sido registrado exitosamente en el sistema SCUM",
                color=discord.Color.green()
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
                name="📈 Estado",
                value="Usuario registrado",
                inline=True
            )
            
            embed.add_field(
                name="🚖 Próximos Pasos",
                value="• Usa `/taxi_solicitar` para pedir un taxi\n• Usa `/banco_balance` para ver tu dinero\n• Usa `/taxi_zonas` para ver zonas disponibles",
                inline=False
            )
            
        else:
            if "already registered" in result.lower():
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
            else:
                embed = discord.Embed(
                    title="❌ Error de Registro",
                    description=f"No se pudo registrar: {result}",
                    color=discord.Color.red()
                )
        
        embed.set_footer(text="Sistema de Taxi SCUM • Gracias por registrarte")
        await interaction.followup.send(embed=embed, ephemeral=True)

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
