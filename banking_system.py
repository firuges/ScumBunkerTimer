#!/usr/bin/env python3
"""
Sistema Bancario Interactivo con Canal Dedicado
Gestión completa de dinero con botones y embeds dinámicos
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from taxi_database import taxi_db
from taxi_config import taxi_config

logger = logging.getLogger(__name__)

class BankingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank_channels = {}  # {guild_id: channel_id}

    async def load_channel_configs(self):
        """Cargar configuraciones de canales desde la base de datos y recrear paneles"""
        try:
            from taxi_database import taxi_db
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                if "banking" in channels:
                    guild_id_int = int(guild_id)
                    channel_id = channels["banking"]
                    
                    # Cargar en memoria
                    self.bank_channels[guild_id_int] = channel_id
                    
                    # Recrear panel bancario en el canal
                    await self._recreate_bank_panel(guild_id_int, channel_id)
                    
                    logger.info(f"Cargada y recreada configuración de banking para guild {guild_id}: canal {channel_id}")
            
            logger.info(f"Sistema bancario: {len(self.bank_channels)} canales cargados con paneles recreados")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones bancarias: {e}")
    
    async def _recreate_bank_panel(self, guild_id: int, channel_id: int):
        """Recrear panel bancario en un canal específico"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal bancario {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Limpiar mensajes anteriores del bot (solo los más recientes)
            try:
                deleted_count = 0
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds:
                        # Solo eliminar si es un embed del sistema bancario
                        for embed in message.embeds:
                            if embed.title and "Sistema Bancario" in embed.title:
                                await message.delete()
                                deleted_count += 1
                                break
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} paneles bancarios anteriores del canal {channel_id}")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes bancarios anteriores: {cleanup_e}")
            
            # Crear embed bancario real (igual que en setup_bank_channel)
            embed = discord.Embed(
                title="🏦 Sistema Bancario SCUM",
                description="Gestiona tu dinero de forma segura y eficiente",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="💳 Servicios Disponibles:",
                value="""
                🔍 **Consultar Saldo** - Ver tu balance actual
                💸 **Transferir Dinero** - Enviar dinero a otros jugadores
                📊 **Historial** - Ver tus últimas transacciones
                📈 **Estadísticas** - Análisis de tu actividad financiera
                🎁 **Canje Diario** - Recibe $250 gratis cada día
                """,
                inline=False
            )
            
            embed.add_field(
                name="🔐 Seguridad:",
                value="""
                ✅ Todas las transacciones son seguras
                ✅ Historial completo de movimientos
                ✅ Protección contra fraudes
                ✅ Soporte 24/7 por administradores
                """,
                inline=False
            )
            
            embed.add_field(
                name="💡 Consejos:",
                value="""
                • Verifica siempre el número de cuenta antes de transferir
                • Guarda capturas de transacciones importantes
                • Reporta cualquier actividad sospechosa
                • Usa descripciones claras en tus transferencias
                """,
                inline=False
            )
            
            embed.set_footer(text="Selecciona una opción para comenzar")
            
            # Usar la vista correcta del sistema bancario (BankingView está definida en este mismo archivo)
            view = BankingView()
            
            await channel.send(embed=embed, view=view)
            logger.info(f"Panel bancario recreado exitosamente en canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel bancario para canal {channel_id}: {e}")

    async def setup_bank_channel(self, guild_id: int, channel_id: int):
        """Configurar canal bancario con embed interactivo"""
        # Guardar en memoria (para acceso rápido)
        self.bank_channels[guild_id] = channel_id
        
        # Guardar en base de datos (para persistencia)
        from taxi_database import taxi_db
        await taxi_db.save_channel_config(str(guild_id), "banking", str(channel_id))
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
        
        # Embed principal del banco
        embed = discord.Embed(
            title="🏦 Sistema Bancario SCUM",
            description="Gestiona tu dinero de forma segura y eficiente",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💳 Servicios Disponibles:",
            value="""
            🔍 **Consultar Saldo** - Ver tu balance actual
            💸 **Transferir Dinero** - Enviar dinero a otros jugadores
            📊 **Historial** - Ver tus últimas transacciones
            📈 **Estadísticas** - Análisis de tu actividad financiera
            🎁 **Canje Diario** - Recibe $250 gratis cada día
            """,
            inline=False
        )
        
        embed.add_field(
            name="🔐 Seguridad:",
            value="""
            ✅ Todas las transacciones son seguras
            ✅ Historial completo de movimientos
            ✅ Protección contra fraudes
            ✅ Soporte 24/7 por administradores
            """,
            inline=False
        )
        
        embed.add_field(
            name="💡 Consejos:",
            value="""
            • Verifica siempre el número de cuenta antes de transferir
            • Guarda capturas de transacciones importantes
            • Reporta cualquier actividad sospechosa
            • Usa descripciones claras en tus transferencias
            """,
            inline=False
        )
        
        embed.set_footer(text="Selecciona una opción para comenzar")
        
        # Vista con botones bancarios
        view = BankingView()
        
        await channel.send(embed=embed, view=view)
        return True

    # === COMANDOS DEL BANCO ===
    
    @app_commands.command(name="banco_balance", description="💰 Ver tu balance actual")
    async def banco_balance(self, interaction: discord.Interaction):
        """Ver balance del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        # Verificar si el usuario está registrado
        user_exists = await taxi_db.get_user(interaction.user.id)
        if not user_exists:
            embed = discord.Embed(
                title="❌ Usuario No Registrado",
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener balance
        balance = await taxi_db.get_user_balance(interaction.user.id)
        
        embed = discord.Embed(
            title="💰 Tu Balance Bancario",
            description=f"Balance actual de {interaction.user.display_name}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💵 Dinero Disponible",
            value=f"${balance:,.0f}",
            inline=True
        )
        
        # Obtener transacciones recientes
        recent_transactions = await taxi_db.get_user_transactions(interaction.user.id, limit=5)
        
        if recent_transactions:
            transaction_text = ""
            for transaction in recent_transactions:
                amount = transaction['amount']
                t_type = transaction['type']
                date = transaction['created_at']
                
                emoji = "💚" if amount > 0 else "💸"
                type_text = {
                    'welcome_bonus': 'Welcome Pack',
                    'taxi_payment': 'Pago Taxi',
                    'taxi_earning': 'Ganancia Taxi',
                    'transfer_sent': 'Transferencia Enviada',
                    'transfer_received': 'Transferencia Recibida',
                    'admin_adjustment': 'Ajuste Admin'
                }.get(t_type, t_type.title())
                
                transaction_text += f"{emoji} {type_text}: ${amount:+,.0f}\n"
            
            embed.add_field(
                name="📊 Últimas Transacciones",
                value=transaction_text or "Sin transacciones recientes",
                inline=False
            )
        
        embed.add_field(
            name="🏦 Servicios Disponibles",
            value="• Transferir dinero: `/banco_transferir`\n• Ver historial: `/banco_historial`\n• Pagar servicios: Automático",
            inline=False
        )
        
        embed.set_footer(text="Sistema Bancario SCUM • Dinero seguro")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="banco_transferir", description="💸 Transferir dinero a otro usuario")
    @app_commands.describe(
        usuario="Usuario destinatario",
        cantidad="Cantidad a transferir",
        concepto="Concepto de la transferencia (opcional)"
    )
    async def banco_transferir(self, interaction: discord.Interaction, usuario: discord.User, cantidad: int, concepto: str = "Transferencia"):
        """Transferir dinero a otro usuario"""
        await interaction.response.defer()
        
        # Verificar que no sea a sí mismo
        if usuario.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Operación Inválida",
                description="No puedes transferir dinero a ti mismo",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar cantidad positiva
        if cantidad <= 0:
            embed = discord.Embed(
                title="❌ Cantidad Inválida",
                description="La cantidad debe ser mayor a 0",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar límite máximo
        if cantidad > 1000000:  # 1 millón
            embed = discord.Embed(
                title="❌ Cantidad Muy Alta",
                description="No puedes transferir más de $1,000,000 de una vez",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar que ambos usuarios estén registrados
        sender_exists = await taxi_db.get_user(interaction.user.id)
        receiver_exists = await taxi_db.get_user(usuario.id)
        
        if not sender_exists:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if not receiver_exists:
            embed = discord.Embed(
                title="❌ Usuario Destinatario",
                description=f"{usuario.display_name} no está registrado en el sistema",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar balance suficiente
        sender_balance = await taxi_db.get_user_balance(interaction.user.id)
        if sender_balance < cantidad:
            embed = discord.Embed(
                title="💰 Saldo Insuficiente",
                description=f"Necesitas ${cantidad:,} pero solo tienes ${sender_balance:,}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Realizar transferencia
        success = await taxi_db.transfer_money(
            sender_id=interaction.user.id,
            receiver_id=usuario.id,
            amount=cantidad,
            concept=concepto
        )
        
        if success:
            new_balance = await taxi_db.get_user_balance(interaction.user.id)
            
            embed = discord.Embed(
                title="✅ Transferencia Exitosa",
                description="El dinero ha sido transferido correctamente",
                color=discord.Color.green()
            )
            
            embed.add_field(name="💸 Cantidad", value=f"${cantidad:,}", inline=True)
            embed.add_field(name="👤 Destinatario", value=usuario.display_name, inline=True)
            embed.add_field(name="💰 Tu Nuevo Balance", value=f"${new_balance:,}", inline=True)
            embed.add_field(name="📝 Concepto", value=concepto, inline=False)
            
            # Notificar al receptor
            try:
                receiver_embed = discord.Embed(
                    title="💰 Dinero Recibido",
                    description=f"Has recibido dinero de {interaction.user.display_name}",
                    color=discord.Color.green()
                )
                receiver_embed.add_field(name="💸 Cantidad", value=f"${cantidad:,}", inline=True)
                receiver_embed.add_field(name="📝 Concepto", value=concepto, inline=False)
                receiver_embed.set_footer(text="Sistema Bancario SCUM")
                
                await usuario.send(embed=receiver_embed)
            except:
                pass  # Usuario tiene DMs deshabilitados
            
        else:
            embed = discord.Embed(
                title="❌ Error en Transferencia",
                description="No se pudo completar la transferencia. Intenta nuevamente",
                color=discord.Color.red()
            )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="banco_historial", description="📊 Ver historial de transacciones")
    @app_commands.describe(limite="Número de transacciones a mostrar (1-20)")
    async def banco_historial(self, interaction: discord.Interaction, limite: int = 10):
        """Ver historial de transacciones"""
        await interaction.response.defer(ephemeral=True)
        
        # Verificar límite
        if limite < 1 or limite > 20:
            embed = discord.Embed(
                title="❌ Límite Inválido",
                description="El límite debe estar entre 1 y 20",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar registro
        user_exists = await taxi_db.get_user(interaction.user.id)
        if not user_exists:
            embed = discord.Embed(
                title="❌ Usuario No Registrado",
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener transacciones
        transactions = await taxi_db.get_user_transactions(interaction.user.id, limit=limite)
        
        if not transactions:
            embed = discord.Embed(
                title="📊 Historial Bancario",
                description="No tienes transacciones registradas",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Historial de Transacciones",
            description=f"Últimas {len(transactions)} transacciones de {interaction.user.display_name}",
            color=discord.Color.blue()
        )
        
        # Balance actual
        current_balance = await taxi_db.get_user_balance(interaction.user.id)
        embed.add_field(
            name="💰 Balance Actual",
            value=f"${current_balance:,.0f}",
            inline=True
        )
        
        # Estadísticas generales
        total_in = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_out = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
        
        embed.add_field(name="📈 Total Ingresado", value=f"${total_in:,.0f}", inline=True)
        embed.add_field(name="📉 Total Gastado", value=f"${total_out:,.0f}", inline=True)
        
        # Lista de transacciones
        transaction_text = ""
        for i, transaction in enumerate(transactions, 1):
            amount = transaction['amount']
            t_type = transaction['type']
            date = transaction['created_at']
            
            # Emoji según tipo
            emoji = "💚" if amount > 0 else "💸"
            
            # Texto del tipo
            type_text = {
                'welcome_bonus': 'Welcome Pack',
                'taxi_payment': 'Pago Taxi',
                'taxi_earning': 'Ganancia Taxi',
                'transfer_sent': 'Transferencia Enviada',
                'transfer_received': 'Transferencia Recibida',
                'admin_adjustment': 'Ajuste Admin'
            }.get(t_type, t_type.title())
            
            # Formatear fecha
            if isinstance(date, str):
                date_obj = datetime.fromisoformat(date)
            else:
                date_obj = date
            
            date_str = date_obj.strftime("%d/%m %H:%M")
            
            transaction_text += f"`{i:2}.` {emoji} **{type_text}**: ${amount:+,.0f} _{date_str}_\n"
        
        embed.add_field(
            name="📋 Transacciones",
            value=transaction_text,
            inline=False
        )
        
        embed.set_footer(text="Sistema Bancario SCUM • Página 1")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # Comando setup temporalmente deshabilitado - requiere migración completa  
    # TODO: Migrar completamente a app_commands
    pass
    #    """Comando para configurar el canal bancario"""
    #    success = await self.setup_bank_channel(ctx.guild.id, channel.id)
    #    
    #    if success:
    #        embed = discord.Embed(
    #            title="✅ Canal Bancario Configurado",
    #            description=f"Canal {channel.mention} configurado correctamente",
    #            color=discord.Color.green()
    #        )
    #    else:
    #        embed = discord.Embed(
    #            title="❌ Error",
    #            description="No se pudo configurar el canal bancario",
    #            color=discord.Color.red()
    #        )
    #    
    #    await ctx.respond(embed=embed, ephemeral=True)

class BankingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Vista persistente

    @discord.ui.button(
        label="💰 Ver Saldo", 
        style=discord.ButtonStyle.primary,
        emoji="💳",
        custom_id="check_balance"
    )
    async def check_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para consultar saldo"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.BANK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Bancario Deshabilitado",
                description="El sistema bancario está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener datos del usuario
        user_data = await taxi_db.get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="No tienes una cuenta bancaria. Ve al canal de bienvenida para registrarte.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Crear embed de saldo
        embed = discord.Embed(
            title="💳 Estado de Cuenta",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👤 Titular de la Cuenta",
            value=f"**{user_data['display_name'] or user_data['username']}**",
            inline=True
        )
        
        embed.add_field(
            name="💳 Número de Cuenta",
            value=f"`{user_data['account_number']}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Saldo Disponible",
            value=f"**${user_data['balance']:,.2f}**",
            inline=True
        )
        
        # Calcular estado financiero
        if user_data['balance'] >= 10000:
            status = "🟢 Excelente"
            advice = "Tienes un saldo saludable"
        elif user_data['balance'] >= 5000:
            status = "🟡 Bueno"
            advice = "Saldo moderado, considera ahorrar más"
        elif user_data['balance'] >= 1000:
            status = "🟠 Regular"
            advice = "Considera trabajar como conductor para ganar más"
        else:
            status = "🔴 Bajo"
            advice = "¡Urgente! Busca maneras de generar ingresos"
        
        embed.add_field(
            name="📊 Estado Financiero",
            value=f"{status}\n*{advice}*",
            inline=False
        )
        
        embed.add_field(
            name="📅 Información de Cuenta",
            value=f"**Miembro desde:** <t:{int(datetime.fromisoformat(user_data['joined_at']).timestamp())}:D>\n**Última actividad:** <t:{int(datetime.fromisoformat(user_data['last_active']).timestamp())}:R>",
            inline=False
        )
        
        embed.set_footer(text=f"Consultado: {datetime.now().strftime('%d/%m/%Y a las %H:%M')}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="💸 Transferir", 
        style=discord.ButtonStyle.secondary,
        emoji="📤",
        custom_id="transfer_money"
    )
    async def transfer_money(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para transferir dinero"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.BANK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Bancario Deshabilitado",
                description="Las transferencias están temporalmente deshabilitadas",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar que está registrado
        user_data = await taxi_db.get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="No tienes una cuenta bancaria. Ve al canal de bienvenida para registrarte.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para transferencia
        modal = TransferModal(user_data)
        await interaction.followup.send("💸 Abriendo formulario de transferencia...", ephemeral=True)
        await interaction.edit_original_response(content="", view=TransferModalView(modal, user_data))

    @discord.ui.button(
        label="📊 Historial", 
        style=discord.ButtonStyle.secondary,
        emoji="📋",
        custom_id="transaction_history"
    )
    async def transaction_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para ver historial de transacciones"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.BANK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Bancario Deshabilitado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener datos del usuario
        user_data = await taxi_db.get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="No tienes una cuenta bancaria.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener transacciones (implementar en taxi_database.py)
        await self.show_transaction_history(interaction, user_data)

    @discord.ui.button(
        label="🎁 Canje Diario", 
        style=discord.ButtonStyle.success,
        emoji="🎁",
        custom_id="daily_reward"
    )
    async def daily_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para canje diario de $250"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.BANK_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Bancario Deshabilitado",
                description="El canje diario está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Obtener datos del usuario
        user_data = await taxi_db.get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="No tienes una cuenta bancaria. Ve al canal de bienvenida para registrarte.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar si ya reclamó hoy
        last_daily_claim = await taxi_db.get_last_daily_claim(user_data['user_id'])
        now = datetime.now()
        
        if last_daily_claim:
            last_claim_date = datetime.fromisoformat(last_daily_claim)
            if last_claim_date.date() == now.date():
                # Ya reclamó hoy
                next_claim = (last_claim_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                next_claim_timestamp = int(next_claim.timestamp())
                
                embed = discord.Embed(
                    title="⏰ Ya Reclamaste Hoy",
                    description="Ya has reclamado tu canje diario de hoy",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🕒 Próximo Canje",
                    value=f"<t:{next_claim_timestamp}:R>",
                    inline=True
                )
                embed.add_field(
                    name="💰 Cantidad",
                    value="$250",
                    inline=True
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        # Dar recompensa diaria
        daily_amount = 250
        success = await taxi_db.add_daily_reward(user_data['user_id'], daily_amount)
        
        if success:
            # Actualizar balance
            new_balance = user_data['balance'] + daily_amount
            
            embed = discord.Embed(
                title="🎁 ¡Canje Diario Reclamado!",
                description="Has recibido tu recompensa diaria",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💰 Cantidad Recibida",
                value=f"**+${daily_amount}**",
                inline=True
            )
            embed.add_field(
                name="💳 Nuevo Saldo",
                value=f"**${new_balance:,.2f}**",
                inline=True
            )
            embed.add_field(
                name="⏰ Próximo Canje",
                value="Mañana a las 00:00",
                inline=True
            )
            embed.set_footer(text="¡Vuelve mañana para tu siguiente recompensa!")
            
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error al procesar tu canje diario. Intenta nuevamente.",
                color=discord.Color.red()
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def show_transaction_history(self, interaction, user_data):
        """Mostrar historial de transacciones"""
        # Esta función necesitaría ser implementada en taxi_database.py
        embed = discord.Embed(
            title="📊 Historial de Transacciones",
            description=f"Últimas transacciones de {user_data['username']}",
            color=discord.Color.blue()
        )
        
        # Placeholder - implementar lógica real
        embed.add_field(
            name="📅 Últimos 30 días",
            value="```\nNo hay transacciones recientes\n```",
            inline=False
        )
        
        embed.add_field(
            name="💡 Consejo",
            value="Usa el sistema de taxi para generar más actividad financiera",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class TransferModalView(discord.ui.View):
    def __init__(self, modal, user_data):
        super().__init__(timeout=300)
        self.modal = modal
        self.user_data = user_data

    @discord.ui.button(label="💸 Abrir Formulario", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal)

class TransferModal(discord.ui.Modal):
    def __init__(self, user_data):
        super().__init__(title="💸 Transferir Dinero")
        self.user_data = user_data
        
        self.account_number = discord.ui.TextInput(
            label="Número de Cuenta Destino",
            placeholder="TAX123456",
            required=True,
            max_length=20
        )
        
        self.amount = discord.ui.TextInput(
            label="Cantidad a Transferir",
            placeholder="100.00",
            required=True,
            max_length=10
        )
        
        self.description = discord.ui.TextInput(
            label="Descripción (Opcional)",
            placeholder="Pago por servicios, préstamo, etc.",
            required=False,
            max_length=100,
            style=discord.TextStyle.long
        )
        
        self.add_item(self.account_number)
        self.add_item(self.amount)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar cantidad
            amount = float(self.amount.value)
            if amount <= 0:
                raise ValueError("La cantidad debe ser mayor a 0")
            
            if amount > self.user_data['balance']:
                raise ValueError("Saldo insuficiente")
            
            # Verificar número de cuenta
            to_account = self.account_number.value.upper().strip()
            if not to_account.startswith('TAX'):
                raise ValueError("Número de cuenta inválido")
            
            # Realizar transferencia
            success, message = await taxi_db.transfer_money(
                self.user_data['account_number'],
                to_account,
                amount,
                self.description.value or "Transferencia directa",
                None
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Transferencia Exitosa",
                    description="Tu dinero ha sido transferido correctamente",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="💸 Detalles de la Transferencia",
                    value=f"""
                    **Destino:** `{to_account}`
                    **Cantidad:** `${amount:,.2f}`
                    **Descripción:** {self.description.value or 'Sin descripción'}
                    **Nuevo saldo:** `${self.user_data['balance'] - amount:,.2f}`
                    """,
                    inline=False
                )
                
                embed.set_footer(text=f"Procesado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error en Transferencia",
                    description=f"No se pudo completar la transferencia: {message}",
                    color=discord.Color.red()
                )
                
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Datos Inválidos",
                description=str(e),
                color=discord.Color.red()
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Ocurrió un error inesperado. Contacta al soporte.",
                color=discord.Color.red()
            )
            logger.error(f"Error en transferencia: {e}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    # === COMANDO DE ADMINISTRACIÓN ===
    
    @app_commands.command(name="banco_admin_setup", description="[ADMIN] Configurar canal del banco")
    @app_commands.describe(canal="Canal donde configurar el sistema bancario")
    @app_commands.default_permissions(administrator=True)
    async def admin_setup_bank(self, interaction: discord.Interaction, canal: discord.TextChannel):
        """Configurar canal del banco"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = await self.setup_bank_channel(interaction.guild.id, canal.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Canal Bancario Configurado",
                    description=f"El sistema bancario ha sido configurado en {canal.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="📍 Canal", value=canal.mention, inline=True)
                embed.add_field(name="⚙️ Estado", value="🟢 Activo", inline=True)
                embed.add_field(
                    name="🎯 Funcionalidades Activadas",
                    value="• `/banco_balance` - Ver balance\n• `/banco_transferir` - Transferir dinero\n• `/banco_historial` - Ver transacciones",
                    inline=False
                )
                embed.add_field(
                    name="💡 Próximos Pasos",
                    value="1. Verifica que los usuarios pueden usar `/banco_balance`\n2. Configura permisos del canal si es necesario\n3. Informa a tu comunidad sobre el sistema",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de Configuración",
                    description="No se pudo configurar el canal bancario. Inténtalo de nuevo.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error configurando banco: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error durante la configuración: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BankingSystem(bot))
