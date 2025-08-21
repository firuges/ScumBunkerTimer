#!/usr/bin/env python3
"""
Sistema de Mecánico - Seguros de Vehículos
Sistema completo para solicitar y gestionar seguros de vehículos en SCUM
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import aiosqlite
import typing
from datetime import datetime, timedelta
from taxi_database import taxi_db
from taxi_config import taxi_config
from core.user_manager import user_manager, get_user_by_discord_id, get_user_balance, subtract_money
from rate_limiter import rate_limit, rate_limiter

logger = logging.getLogger(__name__)

class BaseView(discord.ui.View):
    """Clase base para todas las vistas con manejo correcto de timeout"""
    
    async def on_timeout(self):
        """Manejar timeout de la vista de forma asíncrona"""
        for item in self.children:
            item.disabled = True

class VehicleInsuranceModal(discord.ui.Modal, title="🔧 Solicitar Seguro de Vehículo"):
    def __init__(self):
        super().__init__()
    
    vehicle_id = discord.ui.TextInput(
        label="ID del Vehículo",
        placeholder="Ingresa el ID único de tu vehículo (ej: VEH123456)",
        required=True,
        max_length=20
    )
    
    description = discord.ui.TextInput(
        label="Descripción Adicional",
        placeholder="Color, estado, modificaciones, etc. (opcional)",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Mostrar formulario con selectors"""
        vehicle_id = self.vehicle_id.value.strip()
        description = self.description.value.strip() if self.description.value else ""
        
        if len(vehicle_id) < 3:
            embed = discord.Embed(
                title="❌ ID Inválido",
                description="El ID del vehículo debe tener al menos 3 caracteres",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # NUEVO: Verificar si el vehículo ya tiene seguro o está pendiente
        try:
            guild_id = str(interaction.guild.id)
            existing_insurance = await check_vehicle_insurance_status(vehicle_id, guild_id)
            
            if existing_insurance:
                status = existing_insurance['status']
                if status == 'active':
                    embed = discord.Embed(
                        title="⚠️ Vehículo Ya Asegurado",
                        description=f"El vehículo `{vehicle_id}` ya tiene un seguro activo.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="📋 Información del Seguro",
                        value=f"**ID Seguro:** `{existing_insurance['insurance_id']}`\n**Costo:** ${existing_insurance['cost']:,.0f}\n**Método:** {existing_insurance['payment_method'].title()}",
                        inline=False
                    )
                    embed.add_field(
                        name="💡 ¿Qué puedo hacer?",
                        value="• Usa `/seguro_consultar` para ver todos tus seguros\n• Si perdiste el vehículo, contacta a un mecánico para el reclamo",
                        inline=False
                    )
                elif status == 'pending_confirmation':
                    embed = discord.Embed(
                        title="⏳ Seguro Pendiente de Confirmación",
                        description=f"El vehículo `{vehicle_id}` ya tiene una solicitud de seguro pendiente.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="🔍 Estado Actual",
                        value="Tu solicitud está esperando confirmación de un mecánico. **No se ha realizado ningún cobro aún.**",
                        inline=False
                    )
                    embed.add_field(
                        name="💡 ¿Qué puedo hacer?",
                        value="• Espera a que un mecánico confirme tu solicitud\n• Los mecánicos reciben notificaciones automáticamente\n• Contacta a un mecánico en el servidor si es urgente",
                        inline=False
                    )
                else:
                    # Otro estado (por ejemplo, rejected, expired, etc.)
                    embed = discord.Embed(
                        title="⚠️ Seguro en Estado Especial",
                        description=f"El vehículo `{vehicle_id}` tiene un seguro en estado: **{status}**",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Recomendación",
                        value="Contacta a un administrador o mecánico para revisar el estado de este seguro.",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        except Exception as e:
            logger.error(f"Error verificando estado del seguro para {vehicle_id}: {e}")
            # Si hay error en la verificación, permitir continuar pero logear el error
        
        # Mostrar vista con selectores
        view = VehicleInsuranceSelectView(vehicle_id, description)
        
        # Auto-detectar zona basada en escuadrón
        await view.auto_detect_zone_type(interaction)
        
        embed = discord.Embed(
            title="🚗 Configurar Seguro de Vehículo",
            description=f"**ID Vehículo:** `{vehicle_id}`\n\nSelecciona las opciones para tu seguro:",
            color=0xff8800
        )
        
        if description:
            embed.add_field(
                name="📝 Descripción",
                value=description,
                inline=False
            )
        
        # Si se detectó zona automáticamente, mostrar información
        if view.squadron_detected and view.zone_type:
            zone_emoji = "🛡️" if view.zone_type == "PVE" else "⚔️"
            embed.add_field(
                name="🏆 Detección Automática",
                value=f"{zone_emoji} **Zona detectada:** {view.zone_type} (basado en tu escuadrón)",
                inline=False
            )
        
        embed.add_field(
            name="📋 Paso Siguiente",
            value="Completa los selectores de abajo y presiona **'Confirmar Seguro'**",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class VehicleInsuranceSelectView(BaseView):
    """Vista con selectores para configurar seguro de vehículo"""
    def __init__(self, vehicle_id: str, description: str, vehicle_type: str = None, auto_zone_detection: bool = True):
        super().__init__(timeout=300)  # 5 minutos
        self.vehicle_id = vehicle_id
        self.description = description
        self.vehicle_type = vehicle_type.lower() if vehicle_type else None  # Pre-establecido desde vehículo registrado
        self.zone_type = None
        self.payment_method = None
        self.auto_zone_detection = auto_zone_detection
        self.squadron_detected = False
        
        # Si el tipo de vehículo ya está definido, remover el selector de tipo después de inicializar
        if self.vehicle_type:
            # Buscar y remover el selector de tipo de vehículo
            for child in list(self.children):
                if hasattr(child, 'placeholder') and child.placeholder and "tipo de vehículo" in child.placeholder:
                    self.remove_item(child)
    
    async def auto_detect_zone_type(self, interaction: discord.Interaction):
        """Detectar automáticamente el tipo de zona basado en el escuadrón del usuario"""
        if not self.auto_zone_detection:
            return
        
        try:
            detected_zone = await get_user_squadron_type(str(interaction.user.id), str(interaction.guild.id))
            
            if detected_zone:
                self.zone_type = detected_zone
                self.squadron_detected = True
                
                # Remover el selector de zona si está presente
                for child in list(self.children):
                    if hasattr(child, 'placeholder') and child.placeholder and "zona del vehículo" in child.placeholder:
                        self.remove_item(child)
                        break
                
                logger.info(f"Zona auto-detectada para {interaction.user.display_name}: {detected_zone}")
        except Exception as e:
            logger.error(f"Error en auto-detección de zona: {e}")
    
    @discord.ui.select(
        placeholder="🚗 Selecciona el tipo de vehículo...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Ranger", description="Vehículo tipo Ranger", emoji="🚗"),
            discord.SelectOption(label="Laika", description="Vehículo tipo Laika", emoji="🚙"),
            discord.SelectOption(label="WW", description="Vehículo tipo WW (Willys Wagon)", emoji="🚐"),
            discord.SelectOption(label="Avion", description="Avión/Aeronave", emoji="✈️"),
            discord.SelectOption(label="Moto", description="Motocicleta", emoji="🏍️"),
        ]
    )
    async def vehicle_type_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.vehicle_type = select.values[0].lower()
        await interaction.response.defer()
        await self.update_embed(interaction)
    
    @discord.ui.select(
        placeholder="🗺️ Selecciona la zona del vehículo...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="PVE", description="Zona PVE (Precio normal)", emoji="🛡️"),
            discord.SelectOption(label="PVP", description="Zona PVP (Recargo aplicado)", emoji="⚔️"),
        ]
    )
    async def zone_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.zone_type = select.values[0]
        await interaction.response.defer()
        await self.update_embed(interaction)
    
    @discord.ui.select(
        placeholder="💰 Selecciona el método de pago...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Discord", description="Pagar con dinero del Discord", emoji="💳"),
            discord.SelectOption(label="InGame", description="Pagar en el juego con mecánico", emoji="🎮"),
        ]
    )
    async def payment_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.payment_method = select.values[0].lower()
        await interaction.response.defer()
        await self.update_embed(interaction)
    
    async def update_embed(self, interaction: discord.Interaction):
        """Actualizar embed con las selecciones actuales"""
        embed = discord.Embed(
            title="🚗 Configurar Seguro de Vehículo",
            description=f"**ID Vehículo:** `{self.vehicle_id}`",
            color=0xff8800
        )
        
        # Mostrar selecciones actuales
        selections = []
        if self.vehicle_type:
            emoji_map = {"Ranger": "🚗", "Laika": "🚙", "WW": "🚐", "Avion": "✈️", "Moto": "🏍️"}
            selections.append(f"{emoji_map.get(self.vehicle_type, '🚗')} **Tipo:** {self.vehicle_type}")
        
        if self.zone_type:
            zone_emoji = "🛡️" if self.zone_type == "PVE" else "⚔️"
            zone_text = f"{zone_emoji} **Zona:** {self.zone_type}"
            if self.squadron_detected:
                zone_text += " (🏆 Auto-detectado)"
            selections.append(zone_text)
        
        if self.payment_method:
            payment_emoji = "💳" if self.payment_method == "discord" else "🎮"
            selections.append(f"{payment_emoji} **Pago:** {self.payment_method.title()}")
        
        if selections:
            embed.add_field(
                name="✅ Selecciones Actuales",
                value="\\n".join(selections),
                inline=False
            )
        
        # Calcular costo si tenemos tipo y zona
        if self.vehicle_type and self.zone_type:
            # Usar precio personalizado si existe, sino usar precio por defecto
            base_cost = await get_vehicle_price(str(interaction.guild.id), self.vehicle_type)
            if self.zone_type == "PVP":
                # Obtener porcentaje de recargo PVP desde configuración del servidor
                pvp_markup = await get_server_pvp_markup(interaction.guild.id)
                final_cost = int(base_cost * (1 + pvp_markup / 100))
                markup_text = f" (+{pvp_markup}% PVP)"
            else:
                final_cost = base_cost
                markup_text = ""
            
            embed.add_field(
                name="💰 Costo del Seguro",
                value=f"**${final_cost:,.0f}**{markup_text}",
                inline=True
            )
        
        if self.description:
            embed.add_field(
                name="📝 Descripción",
                value=self.description,
                inline=False
            )
        
        # Verificar si todas las selecciones están completas
        all_selected = all([self.vehicle_type, self.zone_type, self.payment_method])
        
        # Habilitar/deshabilitar botón de confirmar
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "✅ Confirmar Seguro":
                item.disabled = not all_selected
                break
        
        if all_selected:
            embed.add_field(
                name="🎯 Listo para Confirmar",
                value="Todas las opciones seleccionadas. Presiona **'Confirmar Seguro'** para proceder.",
                inline=False
            )
            embed.color = discord.Color.green()
        else:
            pending = []
            if not self.vehicle_type: pending.append("Tipo de vehículo")
            if not self.zone_type: pending.append("Zona")
            if not self.payment_method: pending.append("Método de pago")
            
            embed.add_field(
                name="⏳ Pendiente",
                value="• " + "\\n• ".join(pending),
                inline=False
            )
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label="⚙️ Cambiar Zona", style=discord.ButtonStyle.secondary, row=1, emoji="⚙️")
    async def change_zone_manually(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Permitir cambio manual de zona"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear vista temporal para selección manual de zona
            manual_zone_view = ManualZoneSelectView(self)
            
            embed = discord.Embed(
                title="⚙️ Selección Manual de Zona",
                description="Selecciona manualmente el tipo de zona para tu vehículo:",
                color=0xffa500
            )
            
            embed.add_field(
                name="🛡️ PVE",
                value="• Zona PVE (Precio estándar)\n• Ideal para exploración y supervivencia",
                inline=True
            )
            
            embed.add_field(
                name="⚔️ PVP",
                value="• Zona PVP (Recargo aplicado)\n• Incluye recargo por mayor riesgo",
                inline=True
            )
            
            if self.squadron_detected:
                embed.add_field(
                    name="📝 Nota",
                    value=f"Tu escuadrón sugiere zona **{self.zone_type}**, pero puedes cambiarla aquí.",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, view=manual_zone_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en cambio manual de zona: {e}")
            await interaction.followup.send("❌ Error al abrir selección manual", ephemeral=True)
    
    @discord.ui.button(label="✅ Confirmar Seguro", style=discord.ButtonStyle.success, disabled=True)
    async def confirm_insurance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar y procesar el seguro"""
        if not all([self.vehicle_type, self.zone_type, self.payment_method]):
            embed = discord.Embed(
                title="❌ Selecciones Incompletas",
                description="Debes completar todas las selecciones antes de confirmar",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Procesar el seguro con los datos seleccionados
        await self.process_insurance_request(interaction)
    
    async def process_insurance_request(self, interaction: discord.Interaction):
        """Procesar la solicitud de seguro con las selecciones del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Faltante",
                    description="Necesitas tener un nombre InGame configurado. Usa el botón 'Actualizar Nombre InGame' en el canal de welcome.",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar si el vehículo ya tiene seguro
            existing_insurance = await get_vehicle_insurance(self.vehicle_id, str(interaction.guild.id))
            
            if existing_insurance:
                embed = discord.Embed(
                    title="⚠️ Vehículo Ya Asegurado",
                    description=f"El vehículo `{self.vehicle_id}` ya tiene un seguro activo.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="📊 Información del Seguro Existente",
                    value=f"**Propietario:** {existing_insurance['owner_ingame_name']}\\n**Tipo:** {existing_insurance['vehicle_type']}\\n**Fecha:** {existing_insurance['created_at'][:10]}",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Calcular costo del seguro con zona - usar precio personalizado si existe
            base_cost = await get_vehicle_price(str(interaction.guild.id), self.vehicle_type)
            if self.zone_type == "PVP":
                pvp_markup = await get_server_pvp_markup(interaction.guild.id)
                insurance_cost = int(base_cost * (1 + pvp_markup / 100))
            else:
                insurance_cost = base_cost
            
            # Manejar pago según método seleccionado
            if self.payment_method == 'discord':
                # Verificar si el usuario tiene suficiente dinero
                user_balance = await get_user_balance(interaction.user.id)
                
                if user_balance < insurance_cost:
                    embed = discord.Embed(
                        title="💰 Fondos Insuficientes",
                        description=f"Necesitas ${insurance_cost:,.0f} para contratar el seguro.",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="💳 Tu Balance",
                        value=f"${user_balance:,.0f}",
                        inline=True
                    )
                    embed.add_field(
                        name="💸 Faltante",
                        value=f"${insurance_cost - user_balance:,.0f}",
                        inline=True
                    )
                    embed.add_field(
                        name="💡 Alternativa",
                        value="Puedes usar método 'InGame' para pagar en el juego",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Crear seguro de vehículo
            insurance_id = await create_vehicle_insurance(
                vehicle_id=self.vehicle_id,
                vehicle_type=self.vehicle_type,
                vehicle_location=self.zone_type,
                description=self.description,
                owner_discord_id=str(interaction.user.id),
                owner_ingame_name=ingame_name,
                guild_id=str(interaction.guild.id),
                cost=insurance_cost,
                payment_method=self.payment_method
            )
            
            if insurance_id:
                # Procesar pago según método
                if self.payment_method == 'discord':
                    # Cobrar el seguro del balance Discord (la transacción se registra automáticamente)
                    await subtract_money(interaction.user.id, insurance_cost, f"Seguro de vehículo {self.vehicle_type} - ID: {self.vehicle_id}")
                    
                    payment_status = "✅ Pagado (Discord)"
                    balance_info = f"**Balance Restante:** ${await get_user_balance(interaction.user.id):,.0f}"
                else:
                    # Pago InGame - solo registrar el seguro
                    payment_status = "⏳ Pendiente (InGame)"
                    balance_info = "**Instrucciones:** Coordina el pago con un mecánico en el juego"
                
                embed = discord.Embed(
                    title="✅ Seguro Contratado Exitosamente",
                    description=f"Tu vehículo `{self.vehicle_id}` ahora está asegurado",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🚗 Información del Vehículo",
                    value=f"**ID:** `{self.vehicle_id}`\\n**Tipo:** {self.vehicle_type}\\n**Zona:** {self.zone_type}",
                    inline=True
                )
                
                embed.add_field(
                    name="👤 Propietario",
                    value=f"**Discord:** {interaction.user.display_name}\\n**InGame:** `{ingame_name}`",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Información del Pago",
                    value=f"**Costo:** ${insurance_cost:,.0f}\\n**Método:** {self.payment_method.title()}\\n**Estado:** {payment_status}\\n{balance_info}",
                    inline=False
                )
                
                embed.add_field(
                    name="📋 Detalles del Seguro",
                    value=f"**ID Seguro:** `{insurance_id}`\\n**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n**Estado:** {'Activo' if self.payment_method == 'discord' else 'Pendiente de pago'}",
                    inline=False
                )
                
                # Agregar al historial
                await add_insurance_history(
                    insurance_id,
                    "created",
                    f"Seguro creado - Método de pago: {self.payment_method}",
                    str(interaction.user.id),
                    str(interaction.guild.id)
                )
                
                if self.description:
                    embed.add_field(
                        name="📝 Descripción",
                        value=self.description,
                        inline=False
                    )
                
                embed.set_footer(text="Sistema de Mecánico SCUM • Seguro vehicular")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Enviar notificaciones a mecánicos
                try:
                    insurance_notification_data = {
                        'insurance_id': insurance_id,
                        'vehicle_id': self.vehicle_id,
                        'vehicle_type': self.vehicle_type,
                        'vehicle_location': self.zone_type,
                        'description': self.description,
                        'client_display_name': interaction.user.display_name,
                        'ingame_name': ingame_name,
                        'owner_ingame_name': ingame_name,  # Agregar campo faltante
                        'owner_discord_id': str(interaction.user.id),  # También agregar este
                        'cost': insurance_cost,
                        'payment_method': self.payment_method,
                        'status': payment_status.split(' ')[0]  # Extraer solo el emoji/estado
                    }
                    
                    # Enviar notificaciones en background para no bloquear la respuesta
                    await send_mechanic_notifications(
                        interaction.client,
                        interaction.guild,
                        insurance_notification_data
                    )
                    
                except Exception as notification_error:
                    logger.error(f"Error enviando notificaciones a mecánicos: {notification_error}")
                    # No interrumpir el flujo principal si fallan las notificaciones
                
                # Log del sistema
                logger.info(f"Seguro creado - Usuario: {ingame_name} ({interaction.user.id}), Vehículo: {self.vehicle_id}, Costo: ${insurance_cost}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error del Sistema",
                    description="Hubo un error creando el seguro. Intenta nuevamente.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error procesando seguro de vehículo: {e}")
            embed = discord.Embed(
                title="❌ Error Interno",
                description="Hubo un error procesando tu solicitud. Contacta a un administrador.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    

def calculate_vehicle_insurance_cost(vehicle_type: str) -> int:
    """Calcular costo del seguro basado en el tipo de vehículo"""
    vehicle_type = vehicle_type.lower()
    
    # Costos para los nuevos tipos de vehículos
    costs = {
        'ranger': 1200,
        'laika': 1500,
        'ww': 900,
        'avion': 3500,
        'moto': 500,
        # Mantener compatibilidad con tipos antiguos
        'motocicleta': 500,
        'motorcycle': 500,
        'automovil': 1000,
        'auto': 1000,
        'car': 1000,
        'truck': 1500,
        'helicopter': 3000,
        'helicoptero': 3000,
        'airplane': 3500,
        'plane': 3500
    }
    
    # Buscar costo específico
    for key, cost in costs.items():
        if key in vehicle_type:
            return cost
    
    # Costo por defecto
    return 1000

async def get_server_pvp_markup(guild_id: int) -> float:
    """Obtener el porcentaje de recargo PVP para el servidor"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT config_value FROM server_config 
                WHERE guild_id = ? AND config_key = 'pvp_insurance_markup'
            """, (str(guild_id),))
            result = await cursor.fetchone()
            
            if result:
                return float(result[0])
            else:
                # Valor por defecto: 25% más caro en zonas PVP
                return 25.0
    except Exception as e:
        logger.error(f"Error obteniendo recargo PVP: {e}")
        return 25.0

def calculate_insurance_cost(vehicle_type: str) -> int:
    """Calcular costo del seguro basado en el tipo de vehículo"""
    vehicle_type = vehicle_type.lower()
    
    costs = {
        'motocicleta': 500,
        'motorcycle': 500,
        'moto': 500,
        'atv': 750,
        'quad': 750,
        'automovil': 1000,
        'auto': 1000,
        'car': 1000,
        'coche': 1000,
        'sedan': 1000,
        'suv': 1200,
        'pickup': 1200,
        'camion': 1500,
        'truck': 1500,
        'bus': 2000,
        'autobus': 2000,
        'helicopter': 3000,
        'helicoptero': 3000,
        'avion': 3500,
        'airplane': 3500,
        'plane': 3500,
        'barco': 2500,
        'boat': 2500,
        'ship': 2500
    }
    
    # Buscar costo específico
    for key, cost in costs.items():
        if key in vehicle_type:
            return cost
    
    # Costo por defecto
    return 1000

async def get_vehicle_price(guild_id: str, vehicle_type: str) -> int:
    """Obtener precio personalizado de vehículo o precio por defecto"""
    vehicle_type_clean = vehicle_type.lower()
    
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT price FROM vehicle_prices 
                WHERE guild_id = ? AND vehicle_type = ?
            """, (guild_id, vehicle_type_clean))
            result = await cursor.fetchone()
            
            if result:
                return result[0]
                
    except Exception as e:
        logger.error(f"Error obteniendo precio de vehículo: {e}")
    
    # Fallback a precios por defecto
    return calculate_insurance_cost(vehicle_type)

async def set_vehicle_price(guild_id: str, vehicle_type: str, price: int, updated_by: str) -> bool:
    """Establecer precio personalizado para un tipo de vehículo"""
    vehicle_type_clean = vehicle_type.lower()
    
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO vehicle_prices 
                (guild_id, vehicle_type, price, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, vehicle_type_clean, price, updated_by, datetime.now().isoformat()))
            await db.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error estableciendo precio de vehículo: {e}")
        return False

async def get_all_vehicle_prices(guild_id: str) -> dict:
    """Obtener todos los precios personalizados para un servidor"""
    prices = {}
    
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT vehicle_type, price FROM vehicle_prices 
                WHERE guild_id = ?
            """, (guild_id,))
            rows = await cursor.fetchall()
            
            for row in rows:
                prices[row[0]] = row[1]
                
    except Exception as e:
        logger.error(f"Error obteniendo precios de vehículos: {e}")
    
    return prices

async def create_vehicle_insurance(vehicle_id: str, vehicle_type: str, vehicle_location: str, 
                                 description: str, owner_discord_id: str, owner_ingame_name: str, 
                                 guild_id: str, cost: int, payment_method: str = 'discord') -> str:
    """Crear un nuevo seguro de vehículo en la base de datos"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Todos los seguros empiezan en estado 'pending_confirmation' hasta que el mecánico confirme
            status = 'pending_confirmation'
            cursor = await db.execute("""
                INSERT INTO vehicle_insurance (
                    vehicle_id, vehicle_type, vehicle_location, description,
                    owner_discord_id, owner_ingame_name, guild_id, cost,
                    payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_id, vehicle_type, vehicle_location, description,
                owner_discord_id, owner_ingame_name, guild_id, cost,
                payment_method, status, datetime.now().isoformat()
            ))
            
            insurance_id = f"INS{cursor.lastrowid:06d}"
            
            # Actualizar con el ID generado
            await db.execute(
                "UPDATE vehicle_insurance SET insurance_id = ? WHERE rowid = ?",
                (insurance_id, cursor.lastrowid)
            )
            
            await db.commit()
            return insurance_id
            
    except Exception as e:
        logger.error(f"Error creando seguro de vehículo: {e}")
        return None

async def check_vehicle_insurance_status(vehicle_id: str, guild_id: str) -> dict:
    """Verificar si un vehículo ya tiene seguro (activo o pendiente)"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT insurance_id, vehicle_id, vehicle_type, vehicle_location, 
                       description, owner_discord_id, owner_ingame_name, guild_id, 
                       cost, payment_method, status, created_at, confirmed_by, confirmed_at
                FROM vehicle_insurance 
                WHERE vehicle_id = ? AND guild_id = ? 
                AND status IN ('active', 'pending_confirmation')
                ORDER BY created_at DESC
                LIMIT 1
            """, (vehicle_id, guild_id))
            
            result = await cursor.fetchone()
            
            if result:
                return {
                    'insurance_id': result[0],
                    'vehicle_id': result[1], 
                    'vehicle_type': result[2],
                    'vehicle_location': result[3],
                    'description': result[4],
                    'owner_discord_id': result[5],
                    'owner_ingame_name': result[6],
                    'guild_id': result[7],
                    'cost': result[8],
                    'payment_method': result[9],
                    'status': result[10],
                    'created_at': result[11],
                    'confirmed_by': result[12],
                    'confirmed_at': result[13]
                }
            return None
            
    except Exception as e:
        logger.error(f"Error verificando estado del seguro para vehículo {vehicle_id}: {e}")
        return None

async def get_vehicle_insurance(vehicle_id: str, guild_id: str) -> dict:
    """Obtener información de seguro de un vehículo"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM vehicle_insurance 
                WHERE vehicle_id = ? AND guild_id = ? AND status = 'active'
            """, (vehicle_id, guild_id))
            
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
    except Exception as e:
        logger.error(f"Error consultando seguro de vehículo: {e}")
        return None

async def add_insurance_history(insurance_id: str, action: str, details: str, performed_by: str, guild_id: str):
    """Agregar entrada al historial de seguros"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            await db.execute("""
                INSERT INTO insurance_history (insurance_id, action, details, performed_by, performed_at, guild_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (insurance_id, action, details, performed_by, datetime.now().isoformat(), guild_id))
            await db.commit()
    except Exception as e:
        logger.error(f"Error agregando historial de seguro: {e}")

async def is_user_mechanic(discord_id: str, guild_id: str) -> bool:
    """Verificar si un usuario es mecánico registrado"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Primero verificar qué registros existen para este usuario
            cursor_debug = await db.execute("""
                SELECT discord_id, discord_guild_id, status, ingame_name FROM registered_mechanics 
                WHERE discord_id = ? AND discord_guild_id = ?
            """, (discord_id, guild_id))
            debug_results = await cursor_debug.fetchall()
            
            # Verificar específicamente con status = 'active'
            cursor = await db.execute("""
                SELECT id FROM registered_mechanics 
                WHERE discord_id = ? AND discord_guild_id = ? AND status = 'active'
            """, (discord_id, guild_id))
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Error verificando mecánico: {e}")
        return False

async def get_all_insurances(guild_id: str) -> list:
    """Obtener todos los seguros del servidor (para mecánicos)"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM vehicle_insurance 
                WHERE guild_id = ? 
                ORDER BY created_at DESC
            """, (guild_id,))
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo seguros: {e}")
        return []

async def get_guild_mechanics(guild_id: str) -> list:
    """Obtener todos los mecánicos activos de un servidor que quieren recibir notificaciones"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT rm.discord_id, rm.ingame_name 
                FROM registered_mechanics rm
                LEFT JOIN mechanic_preferences mp ON rm.discord_id = mp.discord_id 
                    AND rm.discord_guild_id = mp.discord_guild_id
                WHERE rm.discord_guild_id = ? 
                    AND rm.status = 'active'
                    AND (mp.receive_notifications IS NULL OR mp.receive_notifications = TRUE)
            """, (guild_id,))
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo mecánicos: {e}")
        return []

async def get_user_squadron_type(discord_id: str, guild_id: str) -> str:
    """Obtener el tipo de escuadrón del usuario (PvP/PvE) para determinar automáticamente la zona"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT s.squadron_type 
                FROM squadron_members sm
                JOIN squadrons s ON sm.squadron_id = s.id
                WHERE sm.discord_id = ? AND s.guild_id = ? AND sm.status = 'active'
                LIMIT 1
            """, (discord_id, guild_id))
            
            result = await cursor.fetchone()
            if result:
                squadron_type = result[0].upper()
                # Mapear tipos de escuadrón a tipos de zona
                if squadron_type in ['PVP', 'MIXTO']:
                    return 'PVP'
                elif squadron_type == 'PVE':
                    return 'PVE'
            
            # Si no está en ningún escuadrón, usar PVE como default seguro
            return 'PVE'
            
    except Exception as e:
        logger.error(f"Error obteniendo tipo de escuadrón para usuario {discord_id}: {e}")
        return 'PVE'  # Default seguro

async def send_mechanic_notifications(bot, guild, insurance_data: dict):
    """Enviar notificaciones DM a todos los mecánicos del servidor"""
    try:
        mechanics = await get_guild_mechanics(str(guild.id))
        
        if not mechanics:
            logger.info(f"No hay mecánicos registrados en {guild.name} para notificar")
            return
        
        # Crear embed de notificación
        embed = discord.Embed(
            title="🔔 Nueva Solicitud de Seguro",
            description=f"**Un cliente ha solicitado un seguro de vehículo en {guild.name}**",
            color=0xff8800,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🚗 Información del Vehículo",
            value=f"**ID:** `{insurance_data['vehicle_id']}`\n**Tipo:** {insurance_data['vehicle_type']}\n**Ubicación:** {insurance_data['vehicle_location']}",
            inline=True
        )
        
        embed.add_field(
            name="👤 Cliente",
            value=f"**Discord:** {insurance_data['client_display_name']}\n**InGame:** `{insurance_data['ingame_name']}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Detalles del Seguro",
            value=f"**Costo:** ${insurance_data['cost']:,.0f}\n**Método de Pago:** {insurance_data['payment_method'].title()}\n**Estado:** {insurance_data['status']}",
            inline=False
        )
        
        if insurance_data.get('description'):
            embed.add_field(
                name="📝 Descripción Adicional",
                value=insurance_data['description'],
                inline=False
            )
        
        embed.add_field(
            name="🎯 Acción Requerida",
            value=f"• **Si es pago Discord:** Seguro ya activo, cliente notificado\n• **Si es pago InGame:** Coordina con el cliente para recibir el pago\n• **ID Seguro:** `{insurance_data['insurance_id']}`",
            inline=False
        )
        
        embed.add_field(
            name="📞 Contacto",
            value=f"• Busca al cliente **{insurance_data['ingame_name']}** en el juego\n• El vehículo se encuentra en: **{insurance_data['vehicle_location']}**\n• Costo a cobrar: **${insurance_data['cost']:,.0f}**",
            inline=False
        )
        
        embed.set_footer(text=f"Servidor: {guild.name} • Sistema de Mecánico SCUM")
        
        # Enviar DM a cada mecánico
        notifications_sent = 0
        for mechanic in mechanics:
            try:
                discord_id = int(mechanic[0])
                ingame_name = mechanic[1]
                
                # Obtener el usuario de Discord
                user = bot.get_user(discord_id)
                if not user:
                    try:
                        user = await bot.fetch_user(discord_id)
                    except discord.NotFound:
                        logger.warning(f"Usuario mecánico {discord_id} no encontrado")
                        continue
                
                # Crear embed personalizado para cada mecánico
                personal_embed = embed.copy()
                personal_embed.title = f"🔔 Nueva Solicitud - Mecánico {ingame_name}"
                
                # Enviar DM
                await user.send(embed=personal_embed)
                notifications_sent += 1
                
                # Pequeña pausa para evitar rate limits
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                logger.warning(f"No se pudo enviar DM al mecánico {ingame_name} ({discord_id}) - DMs cerrados")
            except Exception as e:
                logger.error(f"Error enviando notificación al mecánico {ingame_name}: {e}")
        
        
        # NUEVO: Enviar también al canal de notificaciones con botones
        await send_channel_notification(bot, guild, insurance_data)
        
        # Si hay múltiples mecánicos, agregar información sobre competencia
        if len(mechanics) > 1:
            try:
                # Enviar un resumen adicional al primer mecánico (opcional)
                if notifications_sent > 1:
                    first_mechanic_id = int(mechanics[0][0])
                    first_user = bot.get_user(first_mechanic_id)
                    
                    if first_user:
                        competition_embed = discord.Embed(
                            title="⚡ Información Adicional",
                            description=f"Se notificó a **{notifications_sent} mecánicos** sobre esta solicitud",
                            color=0xffa500
                        )
                        competition_embed.add_field(
                            name="🏃‍♂️ Consejo",
                            value="Si planeas atender este seguro, responde rápido para coordinarte con el cliente",
                            inline=False
                        )
                        competition_embed.set_footer(text="Solo tú ves este mensaje")
                        
                        await first_user.send(embed=competition_embed)
                        
            except Exception as e:
                logger.error(f"Error enviando información adicional: {e}")
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones a mecánicos: {e}")

async def send_channel_notification(bot, guild, insurance_data: dict):
    """Enviar notificación al canal configurado con botones de confirmación/rechazo"""
    try:
        # Obtener el canal de notificaciones configurado
        mechanic_cog = bot.get_cog('MechanicSystem')
        if not mechanic_cog:
            logger.error("MechanicSystem cog no encontrado")
            return
        
        notification_channel_id = mechanic_cog.mechanic_notification_channels.get(guild.id)
        if not notification_channel_id:
            logger.info(f"No hay canal de notificaciones configurado para {guild.name}")
            return
        
        channel = bot.get_channel(notification_channel_id)
        if not channel:
            logger.error(f"Canal de notificaciones {notification_channel_id} no encontrado")
            return
        
        # Crear embed para el canal
        embed = discord.Embed(
            title="🔔 Nueva Solicitud de Seguro",
            description="**Acción requerida por mecánicos**",
            color=0xff8800,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🚗 Vehículo",
            value=f"**Tipo:** {insurance_data['vehicle_type'].title()}\n**ID:** `{insurance_data['vehicle_id']}`\n**Ubicación:** {insurance_data['vehicle_location']}",
            inline=True
        )
        
        embed.add_field(
            name="👤 Cliente",
            value=f"**Discord:** {insurance_data['client_display_name']}\n**InGame:** `{insurance_data['ingame_name']}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Seguro",
            value=f"**Costo:** ${insurance_data['cost']:,.0f}\n**Pago:** {insurance_data['payment_method'].title()}\n**ID:** `{insurance_data['insurance_id']}`",
            inline=True
        )
        
        if insurance_data.get('description'):
            embed.add_field(
                name="📝 Descripción",
                value=insurance_data['description'],
                inline=False
            )
        
        embed.add_field(
            name="⚠️ Importante",
            value="• **Confirmar:** Procesa el pago y activa el seguro\n• **Rechazar:** Cancela la solicitud sin cobrar\n• El débito de Discord se hará solo tras confirmación",
            inline=False
        )
        
        embed.set_footer(text=f"Servidor: {guild.name} • {datetime.now().strftime('%H:%M:%S')}")
        
        # Crear vista con botones
        view = InsuranceConfirmationView(insurance_data, bot)
        
        # Enviar mensaje al canal
        await channel.send(embed=embed, view=view)
        
    except Exception as e:
        logger.error(f"Error enviando notificación al canal: {e}")

class ManualZoneSelectView(discord.ui.View):
    """Vista para selección manual de zona cuando se quiere sobrescribir la auto-detección"""
    
    def __init__(self, parent_view: 'VehicleInsuranceSelectView'):
        super().__init__(timeout=120)  # 2 minutos de timeout
        self.parent_view = parent_view
    
    @discord.ui.button(label="🛡️ PVE", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def select_pve(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Seleccionar zona PVE manualmente"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            self.parent_view.zone_type = "PVE"
            self.parent_view.squadron_detected = False  # Ya no es auto-detectado
            
            embed = discord.Embed(
                title="✅ Zona Cambiada",
                description="**Zona PVE** seleccionada manualmente.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🛡️ Zona PVE",
                value="• Precio estándar del seguro\n• Sin recargos adicionales",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Actualizar la vista principal
            await self.parent_view.update_embed(interaction)
            
        except Exception as e:
            logger.error(f"Error seleccionando PVE: {e}")
            await interaction.followup.send("❌ Error al cambiar zona", ephemeral=True)
    
    @discord.ui.button(label="⚔️ PVP", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def select_pvp(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Seleccionar zona PVP manualmente"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            self.parent_view.zone_type = "PVP"
            self.parent_view.squadron_detected = False  # Ya no es auto-detectado
            
            embed = discord.Embed(
                title="✅ Zona Cambiada",
                description="**Zona PVP** seleccionada manualmente.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="⚔️ Zona PVP",
                value="• Recargo aplicado por mayor riesgo\n• Precio aumentado según configuración del servidor",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Actualizar la vista principal
            await self.parent_view.update_embed(interaction)
            
        except Exception as e:
            logger.error(f"Error seleccionando PVP: {e}")
            await interaction.followup.send("❌ Error al cambiar zona", ephemeral=True)

class PriceManagementView(discord.ui.View):
    """Vista para gestión interactiva de precios de vehículos"""
    
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutos de timeout
    
    @discord.ui.button(label="💰 Establecer Precio", style=discord.ButtonStyle.primary, emoji="💰")
    async def set_price_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para establecer precio personalizado"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear selector de vehículos para establecer precio
            vehicle_select_view = VehicleSelectForPriceView()
            
            embed = discord.Embed(
                title="💰 Establecer Precio Personalizado",
                description="Selecciona el tipo de vehículo para el cual quieres establecer un precio personalizado:",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📋 Tipos Disponibles",
                value="• **Moto** - Motocicletas\n• **Ranger** - Vehículos 4x4\n• **Laika** - Vehículos compactos\n• **WW** - Vehículos todo terreno\n• **Avion** - Aeronaves\n• **Barca** - Embarcaciones",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=vehicle_select_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en botón establecer precio: {e}")
            await interaction.followup.send("❌ Error al abrir selector de vehículos", ephemeral=True)
    
    @discord.ui.button(label="📋 Ver Precios", style=discord.ButtonStyle.secondary, emoji="📋")
    async def view_prices_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para ver todos los precios"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener precios personalizados y defaults
            custom_prices = await get_all_vehicle_prices(str(interaction.guild.id))
            pvp_markup = await get_server_pvp_markup(interaction.guild.id)
            
            embed = discord.Embed(
                title="📋 Lista Completa de Precios",
                description=f"Precios de seguros configurados para **{interaction.guild.name}**",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🗺️ Configuración PVP",
                value=f"Recargo en zonas PVP: **+{pvp_markup}%**",
                inline=False
            )
            
            # Obtener todos los precios (personalizados y por defecto)
            vehicle_types = ["moto", "ranger", "laika", "ww", "avion", "barca"]
            
            custom_text = ""
            default_text = ""
            
            for vehicle_type in vehicle_types:
                price = await get_vehicle_price(str(interaction.guild.id), vehicle_type)
                pvp_price = int(price * (1 + pvp_markup / 100))
                
                if vehicle_type in custom_prices:
                    custom_text += f"• **{vehicle_type.title()}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
                else:
                    default_text += f"• **{vehicle_type.title()}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
            
            if custom_text:
                embed.add_field(
                    name="🔧 Precios Personalizados",
                    value=custom_text,
                    inline=True
                )
            
            if default_text:
                embed.add_field(
                    name="⚙️ Precios por Defecto",
                    value=default_text,
                    inline=True
                )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando precios: {e}")
            await interaction.followup.send("❌ Error al cargar los precios", ephemeral=True)
    
    @discord.ui.button(label="⚔️ Configurar PVP", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def config_pvp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para configurar recargo PVP"""
        await interaction.response.send_modal(PVPMarkupModal())

class VehicleSelectForPriceView(discord.ui.View):
    """Vista con selector de vehículos para establecer precios"""
    
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.select(
        placeholder="Selecciona el tipo de vehículo...",
        options=[
            discord.SelectOption(label="Moto", value="moto", emoji="🏍️", description="Motocicletas"),
            discord.SelectOption(label="Ranger", value="ranger", emoji="🚗", description="Vehículos 4x4"),
            discord.SelectOption(label="Laika", value="laika", emoji="🚙", description="Vehículos compactos"),
            discord.SelectOption(label="WW", value="ww", emoji="🚐", description="Vehículos todo terreno"),
            discord.SelectOption(label="Avion", value="avion", emoji="✈️", description="Aeronaves"),
            discord.SelectOption(label="Barca", value="barca", emoji="🛥️", description="Embarcaciones"),
        ]
    )
    async def vehicle_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Selector de vehículo para establecer precio"""
        vehicle_type = select.values[0]
        
        # Obtener precio actual
        current_price = await get_vehicle_price(str(interaction.guild.id), vehicle_type)
        
        # Abrir modal para ingresar nuevo precio
        modal = SetPriceModal(vehicle_type, current_price)
        await interaction.response.send_modal(modal)

class SetPriceModal(discord.ui.Modal):
    """Modal para establecer precio de vehículo"""
    
    def __init__(self, vehicle_type: str, current_price: int):
        self.vehicle_type = vehicle_type
        self.current_price = current_price
        super().__init__(title=f"Establecer Precio - {vehicle_type.title()}")
        
        self.price_input = discord.ui.TextInput(
            label="Nuevo Precio",
            placeholder=f"Precio actual: ${current_price:,.0f}",
            default=str(current_price),
            min_length=1,
            max_length=10
        )
        self.add_item(self.price_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            new_price = int(self.price_input.value)
            
            if new_price < 0:
                raise ValueError("El precio no puede ser negativo")
            
            # Establecer nuevo precio
            success = await set_vehicle_price(str(interaction.guild.id), self.vehicle_type, new_price, str(interaction.user.id))
            
            if success:
                # Calcular precio PVP
                pvp_markup = await get_server_pvp_markup(interaction.guild.id)
                pvp_price = int(new_price * (1 + pvp_markup / 100))
                
                embed = discord.Embed(
                    title="✅ Precio Actualizado",
                    description=f"El precio del seguro para **{self.vehicle_type.title()}** ha sido actualizado exitosamente.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="💰 Nuevo Precio",
                    value=f"**Normal:** ${new_price:,.0f}\n**PVP:** ${pvp_price:,.0f} (+{pvp_markup}%)",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Cambio",
                    value=f"**Anterior:** ${self.current_price:,.0f}\n**Diferencia:** ${new_price - self.current_price:+,.0f}",
                    inline=True
                )
                
                embed.set_footer(text=f"Actualizado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Error al actualizar el precio", ephemeral=True)
                
        except ValueError:
            await interaction.followup.send("❌ Ingresa un número válido", ephemeral=True)
        except Exception as e:
            logger.error(f"Error estableciendo precio: {e}")
            await interaction.followup.send("❌ Error interno del sistema", ephemeral=True)

class PVPMarkupModal(discord.ui.Modal):
    """Modal para configurar recargo PVP"""
    
    def __init__(self):
        super().__init__(title="Configurar Recargo PVP")
        
        self.markup_input = discord.ui.TextInput(
            label="Recargo PVP (%)",
            placeholder="Ejemplo: 25 (para 25%)",
            min_length=1,
            max_length=3
        )
        self.add_item(self.markup_input)
    
    async def _safe_send(self, interaction: discord.Interaction, **kwargs):
        """Enviar mensaje de forma segura desde modal"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except discord.errors.NotFound as e:
            # Interacción expiró - no hay nada que hacer
            logger.warning(f"Interacción expirada/no encontrada en PVPMarkupModal: {e}")
        except discord.errors.InteractionResponded as e:
            # Ya fue respondida, intentar followup
            logger.warning(f"Interacción ya respondida en PVPMarkupModal, usando followup: {e}")
            try:
                await interaction.followup.send(**kwargs)
            except Exception as followup_error:
                logger.error(f"Error en followup tras InteractionResponded: {followup_error}")
        except Exception as e:
            logger.error(f"Error enviando mensaje seguro en PVPMarkupModal: {e}")
            # Solo intentar followup si no es un error de interacción expirada
            if "Unknown interaction" not in str(e) and "10062" not in str(e):
                try:
                    await interaction.followup.send(**kwargs)
                except Exception as final_error:
                    logger.error(f"Error final enviando mensaje en PVPMarkupModal: {final_error}")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            markup_percentage = float(self.markup_input.value)
            
            if markup_percentage < 0 or markup_percentage > 100:
                raise ValueError("El porcentaje debe estar entre 0 y 100")
            
            # Actualizar recargo PVP
            success = await update_server_pvp_markup(interaction.guild.id, markup_percentage)
            
            if success:
                embed = discord.Embed(
                    title="✅ Recargo PVP Actualizado",
                    description=f"El recargo para zonas PVP ha sido configurado a **{markup_percentage}%**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="💡 Efecto",
                    value=f"Los seguros en zonas PVP ahora costarán un {markup_percentage}% adicional sobre el precio base",
                    inline=False
                )
                
                embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                
                await self._safe_send(interaction, embed=embed, ephemeral=True)
            else:
                await self._safe_send(interaction, content="❌ Error al actualizar el recargo PVP", ephemeral=True)
                
        except ValueError as e:
            await self._safe_send(interaction, content=f"❌ Valor inválido: {str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error configurando PVP markup: {e}")
            await self._safe_send(interaction, content="❌ Error interno del sistema", ephemeral=True)

class MechanicSystemView(discord.ui.View):
    """Vista con botones para el sistema de mecánico"""
    def __init__(self):
        super().__init__(timeout=None)
    
    async def _safe_send(self, interaction: discord.Interaction, **kwargs):
        """Enviar mensaje de forma segura usando response o followup según disponibilidad"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except discord.errors.NotFound as e:
            # Interacción expiró o no se encontró - no hay nada que hacer
            logger.warning(f"Interacción expirada/no encontrada: {e}")
        except discord.errors.InteractionResponded as e:
            # Ya fue respondida, intentar followup
            logger.warning(f"Interacción ya respondida, usando followup: {e}")
            try:
                await interaction.followup.send(**kwargs)
            except Exception as followup_error:
                logger.error(f"Error en followup tras InteractionResponded: {followup_error}")
        except Exception as e:
            logger.error(f"Error enviando mensaje seguro: {e}")
            # Solo intentar followup si no es un error de interacción expirada
            if "Unknown interaction" not in str(e) and "10062" not in str(e):
                try:
                    await interaction.followup.send(**kwargs)
                except Exception as final_error:
                    logger.error(f"Error final enviando mensaje: {final_error}")
    
    @discord.ui.button(label="🔧 Solicitar Seguro", style=discord.ButtonStyle.success, custom_id="request_insurance")
    async def request_insurance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para solicitar seguro de vehículo"""
        # DEFER INMEDIATAMENTE para evitar timeout y conflictos
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.InteractionResponded:
            # La interacción ya fue respondida, usar followup
            pass
        except Exception as defer_error:
            logger.error(f"Error al hacer defer en request_insurance_button: {defer_error}")
            return
        
        # Verificar si el sistema está habilitado
        if not taxi_config.FEATURE_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Deshabilitado",
                description="El sistema de mecánico está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed, ephemeral=True)
            return
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para solicitar seguros necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 ¿Cómo configurar mi nombre?",
                    value="Ve al canal de **welcome** y usa el botón **'🎮 Actualizar Nombre InGame'**",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener vehículos registrados del usuario
            user_vehicles = await get_user_vehicles(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_vehicles:
                embed = discord.Embed(
                    title="🚗 Sin Vehículos Registrados",
                    description="**No tienes vehículos registrados para asegurar.**",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🎯 ¿Cómo registrar un vehículo?",
                    value="1. Presiona el botón **'🚗 Gestionar Vehículos'** en este mismo panel\n2. Selecciona **'➕ Registrar Vehículo'**\n3. Completa los datos de tu vehículo\n4. Luego podrás solicitar un seguro",
                    inline=False
                )
                embed.add_field(
                    name="⚠️ Requisitos para el Registro",
                    value="• Vehículo **NO** en respawn\n• Todas las **ruedas** funcionales\n• **Asiento de conductor** disponible\n• **ID único** correcto",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Filtrar vehículos que no tienen seguro activo
            vehicles_without_insurance = []
            for vehicle in user_vehicles:
                vehicle_id = vehicle[1]
                existing_insurance = await get_vehicle_insurance(vehicle_id, str(interaction.guild.id))
                if not existing_insurance:
                    vehicles_without_insurance.append(vehicle)
            
            if not vehicles_without_insurance:
                embed = discord.Embed(
                    title="🛡️ Todos los Vehículos Asegurados",
                    description="Todos tus vehículos registrados ya tienen seguro activo.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📋 ¿Quieres ver tus seguros?",
                    value="Usa el botón **'📋 Consultar Seguros'** para ver el estado de tus seguros activos",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear embed de selección de vehículo
            embed = discord.Embed(
                title="🚗 Seleccionar Vehículo para Asegurar",
                description=f"**Vehículos disponibles para asegurar:** {len(vehicles_without_insurance)}",
                color=0xff8800
            )
            
            vehicles_text = ""
            for vehicle in vehicles_without_insurance[:5]:  # Mostrar máximo 5
                vehicle_id = vehicle[1]
                vehicle_type = vehicle[2]
                registered_at = vehicle[8][:10]
                vehicles_text += f"• **{vehicle_type.title()}** - `{vehicle_id}`\n  _{registered_at}_\n"
            
            embed.add_field(
                name="🚗 Vehículos Sin Seguro",
                value=vehicles_text,
                inline=False
            )
            
            if len(vehicles_without_insurance) > 5:
                embed.add_field(
                    name="📋 Información",
                    value=f"Mostrando 5 de {len(vehicles_without_insurance)} vehículos disponibles",
                    inline=False
                )
            
            embed.add_field(
                name="🎯 Siguiente Paso",
                value="Selecciona el vehículo que deseas asegurar del menú de abajo",
                inline=False
            )
            
            # Crear vista de selección de vehículo
            view = VehicleInsuranceSelectionView(vehicles_without_insurance)
            await self._safe_send(interaction, embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en solicitud de seguro: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando tu solicitud",
                color=discord.Color.red()
            )
            
            try:
                await self._safe_send(interaction, embed=embed, ephemeral=True)
            except Exception as final_error:
                logger.error(f"Error final enviando mensaje de error: {final_error}")
    
    @discord.ui.button(label="📋 Consultar Seguros", style=discord.ButtonStyle.primary, custom_id="check_insurance")
    async def check_insurance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para consultar seguros activos"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT * FROM vehicle_insurance 
                    WHERE owner_discord_id = ? AND guild_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                """, (str(interaction.user.id), str(interaction.guild.id)))
                
                insurances = await cursor.fetchall()
                
                if not insurances:
                    embed = discord.Embed(
                        title="📋 Sin Seguros Activos",
                        description="No tienes vehículos asegurados actualmente.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="💡 ¿Quieres asegurar un vehículo?",
                        value="Presiona el botón **'Solicitar Seguro'** para contratar un seguro",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="🚗 Tus Vehículos Asegurados",
                    description=f"Tienes {len(insurances)} vehículo(s) asegurado(s)",
                    color=discord.Color.green()
                )
                
                for insurance in insurances[:5]:  # Mostrar máximo 5
                    embed.add_field(
                        name=f"🚗 {insurance[3]} - `{insurance[2]}`",  # tipo - vehicle_id
                        value=f"**Ubicación:** {insurance[4]}\n**Seguro ID:** `{insurance[1]}`\n**Fecha:** {insurance[11][:10]}\n**Costo:** ${insurance[9]:,.0f}",
                        inline=True
                    )
                
                if len(insurances) > 5:
                    embed.set_footer(text=f"Mostrando 5 de {len(insurances)} seguros")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error consultando seguros: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando tus seguros",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💰 Precios", style=discord.ButtonStyle.secondary, custom_id="insurance_prices")
    async def show_prices(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar tabla de precios de seguros"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener precios personalizados y recargo PVP
            custom_prices = await get_all_vehicle_prices(str(interaction.guild.id))
            pvp_markup = await get_server_pvp_markup(interaction.guild.id)
            
            embed = discord.Embed(
                title="💰 Tabla de Precios - Seguros Vehiculares",
                description=f"Costos de seguros para **{interaction.guild.name}**",
                color=0xffa500
            )
            
            # Vehículos principales con precios actuales (personalizados o por defecto)
            main_vehicles = ['ranger', 'laika', 'ww', 'moto']
            main_text = ""
            for vehicle in main_vehicles:
                if vehicle in custom_prices:
                    price = custom_prices[vehicle]
                    price_type = "🔧"  # Personalizado
                else:
                    price = calculate_vehicle_insurance_cost(vehicle)
                    price_type = "📋"  # Por defecto
                
                pvp_price = int(price * (1 + pvp_markup / 100))
                vehicle_name = vehicle.replace('ww', 'WW (Willys Wagon)').title()
                main_text += f"• {price_type} **{vehicle_name}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
            
            embed.add_field(
                name="🚗 Vehículos Terrestres",
                value=main_text,
                inline=False
            )
            
            # Vehículos aéreos
            air_vehicles = ['avion', 'helicopter']
            air_text = ""
            for vehicle in air_vehicles:
                if vehicle in custom_prices:
                    price = custom_prices[vehicle]
                    price_type = "🔧"
                else:
                    price = calculate_vehicle_insurance_cost(vehicle)
                    price_type = "📋"
                
                pvp_price = int(price * (1 + pvp_markup / 100))
                vehicle_name = vehicle.replace('avion', 'Avión').replace('helicopter', 'Helicóptero')
                air_text += f"• {price_type} **{vehicle_name}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
            
            embed.add_field(
                name="✈️ Vehículos Aéreos",
                value=air_text,
                inline=False
            )
            
            embed.add_field(
                name="🗺️ Modificador de Zona",
                value=f"• **Zona PVE:** Precio normal\n• **Zona PVP:** +{pvp_markup}% de recargo\n• Configurado por administradores",
                inline=False
            )
            
            # Mostrar leyenda de símbolos
            embed.add_field(
                name="📋 Leyenda",
                value="🔧 = Precio personalizado\n📋 = Precio por defecto\nLos precios incluyen el recargo PVP",
                inline=True
            )
            
            embed.add_field(
                name="💡 Información Adicional",
                value="• El seguro cubre **pérdida parcial** del vehículo\n• **ID único** requerido para cada vehículo\n• **Nombre InGame** debe estar configurado\n• Pago único por vehículo asegurado",
                inline=False
            )
            
            if custom_prices:
                embed.set_footer(text=f"Servidor con {len(custom_prices)} precio(s) personalizado(s)")
            else:
                embed.set_footer(text="Usando precios por defecto del sistema")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando precios: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando los precios",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔧 Panel Mecánico", style=discord.ButtonStyle.danger, custom_id="mechanic_panel")
    async def mechanic_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Panel para mecánicos registrados"""
        
        # Verificar si es mecánico (fuera del try-except principal)
        try:
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
        except Exception as e:
            logger.error(f"Error verificando mecánico: {e}")
            is_mechanic = False
        
        if not is_mechanic:
            embed = discord.Embed(
                title="❌ Acceso Denegado",
                description="Solo los mecánicos registrados pueden acceder a este panel.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 ¿Quieres ser mecánico?",
                value="Contacta a un administrador para que te registre como mecánico",
                inline=False
            )
            try:
                await self._safe_send(interaction, embed=embed, ephemeral=True)
            except Exception as send_error:
                logger.error(f"Error enviando mensaje de acceso denegado: {send_error}")
            return
        
        # Solo el procesamiento de seguros debe estar en el try-except principal
        try:
            # Obtener todos los seguros
            all_insurances = await get_all_insurances(str(interaction.guild.id))
            
            if not all_insurances or all_insurances is None:
                embed = discord.Embed(
                    title="📋 Sin Seguros Registrados",
                    description="No hay seguros de vehículos registrados en este servidor.",
                    color=discord.Color.blue()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear embed con información de seguros
            embed = discord.Embed(
                title="🔧 Panel de Mecánico - Todos los Seguros",
                description=f"Total de seguros registrados: **{len(all_insurances)}**",
                color=0xff8800
            )
            
            # Agrupar por estado
            try:
                active_count = sum(1 for ins in all_insurances if len(ins) > 11 and ins[11] == 'active')  # status column
                pending_count = sum(1 for ins in all_insurances if len(ins) > 11 and ins[11] == 'pending_payment')
            except Exception as count_error:
                logger.error(f"Error contando estados: {count_error}")
                active_count = 0
                pending_count = 0
            
            embed.add_field(
                name="📊 Resumen por Estado",
                value=f"✅ **Activos:** {active_count}\n⏳ **Pendientes de pago:** {pending_count}",
                inline=True
            )
            
            # Mostrar últimos 5 seguros
            embed.add_field(
                name="📝 Últimos Seguros",
                value="*Los 5 más recientes:*",
                inline=False
            )
            
            for i, insurance in enumerate(all_insurances[:5]):
                try:
                    # Verificar campos obligatorios y manejar None
                    status = insurance[11] if len(insurance) > 11 and insurance[11] else 'unknown'
                    status_emoji = "✅" if status == 'active' else "⏳"
                    payment_method = insurance[10] if len(insurance) > 10 and insurance[10] else 'discord'
                    
                    # Campos con manejo seguro de None
                    vehicle_type = insurance[3] if len(insurance) > 3 and insurance[3] else 'N/A'
                    vehicle_id = insurance[2] if len(insurance) > 2 and insurance[2] else 'N/A'
                    owner = insurance[7] if len(insurance) > 7 and insurance[7] else 'N/A'
                    location = insurance[4] if len(insurance) > 4 and insurance[4] else 'N/A'
                    cost = insurance[9] if len(insurance) > 9 and insurance[9] else 0
                    date_field = insurance[12] if len(insurance) > 12 and insurance[12] else None
                    date_str = date_field[:10] if date_field else 'N/A'
                    
                    embed.add_field(
                        name=f"{status_emoji} {vehicle_type} - `{vehicle_id}`",
                        value=f"**Propietario:** {owner}\n**Ubicación:** {location}\n**Costo:** ${cost:,.0f}\n**Pago:** {payment_method.title()}\n**Fecha:** {date_str}",
                        inline=True
                    )
                except Exception as field_error:
                    logger.error(f"Error procesando seguro {i}: {field_error}")
                    # Continuar con el siguiente seguro
                    continue
            
            if len(all_insurances) > 5:
                embed.set_footer(text=f"Mostrando 5 de {len(all_insurances)} seguros • Solo visible para mecánicos")
            else:
                embed.set_footer(text="Solo visible para mecánicos registrados")
            
            await self._safe_send(interaction, embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en panel de mecánico: {e}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando los seguros",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💰 Gestionar Precios", style=discord.ButtonStyle.secondary, custom_id="manage_prices")
    async def manage_prices(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Panel para gestionar precios de vehículos"""
        
        # Verificar si es mecánico o administrador
        is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_mechanic or is_admin):
            embed = discord.Embed(
                title="❌ Acceso Denegado",
                description="Solo mecánicos registrados o administradores pueden gestionar precios.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 ¿Quieres ser mecánico?",
                value="Contacta a un administrador para que te registre como mecánico",
                inline=False
            )
            await self._safe_send(interaction, embed=embed, ephemeral=True)
            return
        
        try:
            # Obtener precios personalizados
            custom_prices = await get_all_vehicle_prices(str(interaction.guild.id))
            
            embed = discord.Embed(
                title="💰 Gestión de Precios Vehiculares",
                description=f"Panel de configuración para **{interaction.guild.name}**",
                color=0xff8800
            )
            
            # Obtener recargo PVP
            pvp_markup = await get_server_pvp_markup(interaction.guild.id)
            
            embed.add_field(
                name="🗺️ Configuración PVP",
                value=f"Recargo en zonas PVP: **+{pvp_markup}%**",
                inline=False
            )
            
            if custom_prices:
                custom_text = ""
                for vehicle_type, price in list(custom_prices.items())[:5]:  # Mostrar máximo 5
                    pvp_price = int(price * (1 + pvp_markup / 100))
                    custom_text += f"• **{vehicle_type.title()}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
                
                embed.add_field(
                    name="🔧 Precios Personalizados",
                    value=custom_text,
                    inline=False
                )
                
                if len(custom_prices) > 5:
                    embed.add_field(
                        name="📋 Información",
                        value=f"Mostrando 5 de {len(custom_prices)} precios personalizados",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📋 Sin Precios Personalizados",
                    value="Actualmente se usan los precios por defecto del sistema",
                    inline=False
                )
            
            # Mostrar algunos precios por defecto
            default_types = ['ranger', 'laika', 'ww', 'avion', 'moto']
            default_text = ""
            
            for vehicle_type in default_types[:3]:  # Solo 3 para no saturar
                if vehicle_type not in custom_prices:
                    default_price = calculate_vehicle_insurance_cost(vehicle_type)
                    pvp_price = int(default_price * (1 + pvp_markup / 100))
                    default_text += f"• **{vehicle_type.title()}:** ${default_price:,.0f} (PVP: ${pvp_price:,.0f})\n"
            
            if default_text:
                embed.add_field(
                    name="📋 Algunos Precios por Defecto",
                    value=default_text,
                    inline=False
                )
            
            embed.add_field(
                name="🛠️ Funciones Disponibles",
                value="• **Establecer Precio** - Configurar precio personalizado para vehículos\n• **Ver Precios** - Lista completa de precios actuales\n• **Configurar PVP** - Ajustar recargo para zonas PVP",
                inline=False
            )
            
            embed.add_field(
                name="💡 Instrucciones",
                value="Usa los botones de abajo para gestionar los precios de seguros de vehículos de forma interactiva.",
                inline=False
            )
            
            embed.set_footer(text=f"Panel accedido por {interaction.user.display_name}")
            
            # Crear vista de gestión de precios con botones interactivos
            price_management_view = PriceManagementView()
            await self._safe_send(interaction, embed=embed, view=price_management_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en panel de gestión de precios: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando los precios",
                color=discord.Color.red()
            )
            await self._safe_send(interaction, embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🚗 Gestionar Mis Vehículos", style=discord.ButtonStyle.primary, custom_id="manage_vehicles")
    async def manage_vehicles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Panel para gestionar vehículos registrados"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para gestionar vehículos necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 ¿Cómo configurar mi nombre?",
                    value="Ve al canal de **welcome** y usa el botón **'🎮 Actualizar Nombre InGame'**",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener vehículos registrados del usuario
            user_vehicles = await get_user_vehicles(str(interaction.user.id), str(interaction.guild.id))
            
            if user_vehicles:
            
            embed = discord.Embed(
                title="🚗 Gestión de Vehículos",
                description=f"Panel de gestión para **{ingame_name}**",
                color=0x00ff88
            )
            
            if user_vehicles:
                vehicles_text = ""
                for vehicle in user_vehicles[:5]:  # Mostrar máximo 5
                    vehicle_id = vehicle[1]  # vehicle_id
                    vehicle_type = vehicle[2]  # vehicle_type
                    registered_at = vehicle[8][:10]  # registered_at (solo fecha)
                    vehicles_text += f"• **{vehicle_type.title()}** - `{vehicle_id}`\n  _{registered_at}_\n"
                
                embed.add_field(
                    name="🚗 Tus Vehículos Registrados",
                    value=vehicles_text,
                    inline=False
                )
                
                if len(user_vehicles) > 5:
                    embed.add_field(
                        name="📋 Información",
                        value=f"Mostrando 5 de {len(user_vehicles)} vehículos registrados",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📋 Sin Vehículos Registrados",
                    value="No tienes vehículos registrados actualmente",
                    inline=False
                )
            
            # Mostrar límites actuales
            limits = await get_vehicle_limits(str(interaction.guild.id))
            limits_text = ""
            for vehicle_type, limit in limits.items():
                if vehicle_type in ['moto', 'ranger', 'laika', 'ww', 'avion']:
                    current_count = len([v for v in user_vehicles if v[2].lower() == vehicle_type])
                    limits_text += f"• **{vehicle_type.title()}:** {current_count}/{limit}\n"
            
            embed.add_field(
                name="📊 Límites de Vehículos",
                value=limits_text,
                inline=True
            )
            
            embed.add_field(
                name="🛠️ Acciones Disponibles",
                value="• **Registrar** nuevo vehículo\n• **Dar de baja** vehículo existente\n• **Ver detalles** de tus vehículos",
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Requisitos para Registro",
                value="• Vehículo **NO** en respawn\n• Todas las **ruedas** funcionales\n• **Asiento de conductor** disponible\n• **ID único** correcto",
                inline=False
            )
            
            embed.set_footer(text="Usa los botones de abajo para gestionar tus vehículos")
            
            # Crear vista con botones de gestión
            view = VehicleManagementView(user_vehicles)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en gestión de vehículos: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando tus vehículos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VehicleManagementView(discord.ui.View):
    """Vista para gestionar vehículos registrados"""
    def __init__(self, user_vehicles: list):
        super().__init__(timeout=300)
        self.user_vehicles = user_vehicles
    
    @discord.ui.button(label="➕ Registrar Vehículo", style=discord.ButtonStyle.success)
    async def register_vehicle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar selector para tipo de vehículo antes del modal"""
        embed = discord.Embed(
            title="🚗 Registrar Nuevo Vehículo",
            description="Selecciona el tipo de vehículo que deseas registrar:",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📝 Proceso",
            value="1. **Selecciona el tipo** de vehículo\n2. **Completa el formulario** con los datos\n3. **Confirma el registro**",
            inline=False
        )
        
        view = VehicleRegistrationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="📋 Ver Mis Vehículos", style=discord.ButtonStyle.primary)
    async def view_vehicles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver lista detallada de vehículos"""
        await interaction.response.defer(ephemeral=True)
        
        if not self.user_vehicles:
            embed = discord.Embed(
                title="📋 Sin Vehículos",
                description="No tienes vehículos registrados",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🚗 Tus Vehículos Registrados",
            description=f"Total: **{len(self.user_vehicles)}** vehículos",
            color=0x00ff88
        )
        
        for i, vehicle in enumerate(self.user_vehicles[:10], 1):  # Máximo 10
            vehicle_id = vehicle[1]
            vehicle_type = vehicle[2] 
            registered_at = vehicle[8][:16]  # fecha y hora
            status = "🟢 Activo" if vehicle[9] == 'active' else "🔴 Inactivo"
            
            embed.add_field(
                name=f"{i}. {vehicle_type.title()} - {status}",
                value=f"**ID:** `{vehicle_id}`\n**Registrado:** {registered_at}",
                inline=True
            )
        
        if len(self.user_vehicles) > 10:
            embed.set_footer(text=f"Mostrando 10 de {len(self.user_vehicles)} vehículos")
        
        # Crear vista con botón de editar
        edit_view = VehicleEditView(self.user_vehicles)
        await interaction.followup.send(embed=embed, view=edit_view, ephemeral=True)
    
    @discord.ui.button(label="❌ Dar de Baja", style=discord.ButtonStyle.danger)
    async def unregister_vehicle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar selector para dar de baja vehículo"""
        if not self.user_vehicles:
            embed = discord.Embed(
                title="❌ Sin Vehículos",
                description="No tienes vehículos registrados para dar de baja",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Crear selector con vehículos del usuario
        options = []
        for vehicle in self.user_vehicles[:25]:  # Discord limita a 25 opciones
            vehicle_id = vehicle[1]
            vehicle_type = vehicle[2]
            options.append(discord.SelectOption(
                label=f"{vehicle_type.title()} - {vehicle_id}",
                description=f"Registrado: {vehicle[8][:10]}",
                value=vehicle_id
            ))
        
        view = VehicleUnregisterView(options)
        
        embed = discord.Embed(
            title="❌ Dar de Baja Vehículo",
            description="**⚠️ ADVERTENCIA:** Dar de baja un vehículo también **eliminará su seguro** si tiene uno.\n\nSelecciona el vehículo que deseas dar de baja:",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Vista previa para seleccionar tipo de vehículo antes del modal
class VehicleRegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_vehicle_type = None
    
    @discord.ui.select(
        placeholder="🚗 Selecciona el tipo de vehículo...",
        options=[
            discord.SelectOption(
                label="🏍️ Moto",
                value="moto",
                description="Motocicleta - Ágil y económica",
                emoji="🏍️"
            ),
            discord.SelectOption(
                label="🚙 Ranger",
                value="ranger", 
                description="Vehículo todoterreno resistente",
                emoji="🚙"
            ),
            discord.SelectOption(
                label="🚗 Laika",
                value="laika",
                description="Automóvil estándar confiable", 
                emoji="🚗"
            ),
            discord.SelectOption(
                label="🚛 WW (Camión)",
                value="ww",
                description="Vehículo pesado de carga",
                emoji="🚛"
            ),
            discord.SelectOption(
                label="✈️ Avión",
                value="avion",
                description="Transporte aéreo rápido",
                emoji="✈️"
            ),
            discord.SelectOption(
                label="🚤 Barca",
                value="barca",
                description="Embarcación acuática",
                emoji="🚤"
            )
        ]
    )
    async def select_vehicle_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_vehicle_type = select.values[0]
        
        # Mostrar modal con el tipo seleccionado
        modal = VehicleRegistrationModal(self.selected_vehicle_type)
        await interaction.response.send_modal(modal)

class VehicleRegistrationModal(discord.ui.Modal, title="🚗 Registrar Nuevo Vehículo"):
    def __init__(self, vehicle_type: str):
        super().__init__()
        self.vehicle_type = vehicle_type
        
        # Actualizar título con el tipo de vehículo
        vehicle_names = {
            "moto": "🏍️ Moto",
            "ranger": "🚙 Ranger", 
            "laika": "🚗 Laika",
            "ww": "🚛 WW",
            "avion": "✈️ Avión",
            "barca": "🚤 Barca"
        }
        self.title = f"Registrar {vehicle_names.get(vehicle_type, vehicle_type.title())}"
    
    vehicle_id = discord.ui.TextInput(
        label="ID del Vehículo",
        placeholder="Ingresa el ID único de tu vehículo (ej: VEH123456)",
        required=True,
        max_length=50
    )
    
    notes = discord.ui.TextInput(
        label="Notas (Opcional)",
        placeholder="Color, estado, modificaciones, etc.",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar datos
            vehicle_id = self.vehicle_id.value.strip()
            vehicle_type = self.vehicle_type  # Ya viene del selector, no del campo de texto
            notes = self.notes.value.strip() if self.notes.value else None
            
            if len(vehicle_id) < 3:
                embed = discord.Embed(
                    title="❌ ID Inválido",
                    description="El ID del vehículo debe tener al menos 3 caracteres",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar usuario registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data or not user_data.get('ingame_name'):
                embed = discord.Embed(
                    title="❌ Error de Usuario",
                    description="Usuario no registrado o sin nombre InGame",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar límites
            can_register, current_count, limit = await check_vehicle_limit(
                str(interaction.user.id), str(interaction.guild.id), vehicle_type
            )
            
            if not can_register:
                # Verificar si el usuario está en un escuadrón para personalizar el mensaje
                user_squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
                
                if user_squadron:
                    embed = discord.Embed(
                        title="❌ Límite de Escuadrón Alcanzado",
                        description=f"Tu escuadrón **{user_squadron['squadron_name']}** ya alcanzó el límite total de vehículos",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="📊 Estado Actual",
                        value=f"**Vehículos registrados:** {current_count}/{limit} (cualquier tipo)\n**Escuadrón:** {user_squadron['squadron_name']}",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="💡 Opciones",
                        value="• **Invita más miembros** al escuadrón para más vehículos\n• Contacta a un admin para **aumentar límites globales**\n• **Da de baja** algún vehículo no usado",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⚙️ Sistema Simplificado",
                        value="El nuevo sistema permite **cualquier tipo** de vehículo hasta el límite total del escuadrón.",
                        inline=False
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Límite Individual Alcanzado",
                        description=f"Ya tienes {current_count}/{limit} vehículos registrados (máximo para usuarios sin escuadrón)",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="🏆 ¡Únete a un Escuadrón!",
                        value="Los escuadrones pueden tener **más vehículos** según el número de miembros. Ve al canal de escuadrones para unirte a uno y aumentar tu límite.",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📋 Límite Individual",
                        value="Usuarios sin escuadrón: **2 vehículos máximo** (cualquier tipo)\nEscuadrones: **2 × miembros** (hasta límite del servidor)",
                        inline=False
                    )
                
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener squadron_id del usuario si pertenece a uno
            user_squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
            squadron_id = user_squadron['id'] if user_squadron else None
            
            # Registrar vehículo
            success = await register_vehicle(
                vehicle_id, vehicle_type, str(interaction.user.id),
                user_data['ingame_name'], str(interaction.guild.id), squadron_id, notes
            )
            
            if success:
                # Obtener emoji del tipo de vehículo
                vehicle_emojis = {
                    "moto": "🏍️",
                    "ranger": "🚙", 
                    "laika": "🚗",
                    "ww": "🚛",
                    "avion": "✈️",
                    "barca": "🚤"
                }
                vehicle_emoji = vehicle_emojis.get(vehicle_type, "🚗")
                
                embed = discord.Embed(
                    title="✅ Vehículo Registrado",
                    description=f"Tu **{vehicle_emoji} {vehicle_type.title()}** ha sido registrado exitosamente",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🚗 Información del Vehículo",
                    value=f"**ID:** `{vehicle_id}`\n**Tipo:** {vehicle_emoji} {vehicle_type.title()}\n**Propietario:** {user_data['ingame_name']}",
                    inline=True
                )
                
                # Mostrar información de límites según contexto
                if user_squadron:
                    embed.add_field(
                        name="📊 Límites del Escuadrón",
                        value=f"**{vehicle_emoji} {vehicle_type.title()}:** {current_count + 1}/{limit}\n**Escuadrón:** {user_squadron['squadron_name']}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="📊 Límites Individuales",
                        value=f"**{vehicle_emoji} {vehicle_type.title()}:** {current_count + 1}/{limit}\n*Sin escuadrón*",
                        inline=True
                    )
                
                if notes:
                    embed.add_field(
                        name="📝 Notas",
                        value=notes,
                        inline=False
                    )
                
                embed.add_field(
                    name="🎯 Siguiente Paso",
                    value="Ahora puedes contratar un seguro para este vehículo usando el botón **'🔧 Solicitar Seguro'**",
                    inline=False
                )
                
                embed.set_footer(text="Vehículo registrado en el sistema")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Vehículo registrado: {vehicle_type} {vehicle_id} por {user_data['ingame_name']} ({interaction.user.id})")
                
            else:
                embed = discord.Embed(
                    title="❌ Error en el Registro",
                    description="No se pudo registrar el vehículo. El ID podría ya estar en uso.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error registrando vehículo: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error registrando el vehículo",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VehicleEditView(BaseView):
    """Vista para editar vehículos"""
    def __init__(self, user_vehicles: list):
        super().__init__(timeout=300)
        self.user_vehicles = user_vehicles
    
    @discord.ui.button(label="✏️ Editar ID", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def edit_vehicle_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abrir selector para editar ID de vehículo"""
        if not self.user_vehicles:
            embed = discord.Embed(
                title="❌ Sin Vehículos",
                description="No tienes vehículos para editar",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Crear opciones para el selector
        options = []
        for vehicle in self.user_vehicles[:25]:  # Límite Discord
            vehicle_id = vehicle[1]
            vehicle_type = vehicle[2]
            status = "🟢" if vehicle[9] == 'active' else "🔴"
            
            options.append(discord.SelectOption(
                label=f"{vehicle_type.title()} - {vehicle_id}",
                description=f"ID actual: {vehicle_id} {status}",
                value=vehicle_id
            ))
        
        view = VehicleEditSelectView(options)
        embed = discord.Embed(
            title="✏️ Editar ID de Vehículo",
            description="Selecciona el vehículo cuyo ID quieres corregir:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class VehicleEditSelectView(BaseView):
    """Vista con selector para elegir qué vehículo editar"""
    def __init__(self, options: list):
        super().__init__(timeout=300)
        self.add_item(VehicleEditSelect(options))

class VehicleEditSelect(discord.ui.Select):
    def __init__(self, options: list):
        super().__init__(
            placeholder="Selecciona el vehículo a editar...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        old_vehicle_id = self.values[0]
        modal = VehicleEditModal(old_vehicle_id)
        await interaction.response.send_modal(modal)

class VehicleEditModal(discord.ui.Modal, title="✏️ Editar ID de Vehículo"):
    def __init__(self, old_vehicle_id: str):
        super().__init__()
        self.old_vehicle_id = old_vehicle_id
        
        self.new_id = discord.ui.TextInput(
            label="Nuevo ID del Vehículo",
            placeholder=f"ID actual: {old_vehicle_id}",
            default=old_vehicle_id,
            max_length=50,
            required=True
        )
        self.add_item(self.new_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        new_vehicle_id = self.new_id.value.strip()
        guild_id = str(interaction.guild.id)
        
        # Validaciones
        if new_vehicle_id == self.old_vehicle_id:
            embed = discord.Embed(
                title="⚠️ Sin Cambios",
                description="El nuevo ID es igual al actual.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if len(new_vehicle_id) < 3:
            embed = discord.Embed(
                title="❌ ID Inválido",
                description="El ID debe tener al menos 3 caracteres.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        try:
            # Verificar si el nuevo ID ya existe
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT vehicle_id FROM registered_vehicles 
                    WHERE vehicle_id = ? AND guild_id = ?
                """, (new_vehicle_id, guild_id))
                existing = await cursor.fetchone()
                
                if existing:
                    embed = discord.Embed(
                        title="❌ ID Ya Existe",
                        description=f"El ID `{new_vehicle_id}` ya está en uso por otro vehículo.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Actualizar el ID del vehículo
                await db.execute("""
                    UPDATE registered_vehicles 
                    SET vehicle_id = ? 
                    WHERE vehicle_id = ? AND guild_id = ?
                """, (new_vehicle_id, self.old_vehicle_id, guild_id))
                
                # Actualizar seguros relacionados
                await db.execute("""
                    UPDATE vehicle_insurance 
                    SET vehicle_id = ? 
                    WHERE vehicle_id = ? AND guild_id = ?
                """, (new_vehicle_id, self.old_vehicle_id, guild_id))
                
                await db.commit()
                
                embed = discord.Embed(
                    title="✅ ID Actualizado",
                    description=f"ID del vehículo cambiado exitosamente:",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Cambio Realizado",
                    value=f"**Anterior:** `{self.old_vehicle_id}`\n**Nuevo:** `{new_vehicle_id}`",
                    inline=False
                )
                embed.add_field(
                    name="🔄 Actualizaciones",
                    value="• ID en registro de vehículos\n• ID en seguros relacionados",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error actualizando ID de vehículo: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error actualizando el ID del vehículo",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VehicleUnregisterView(discord.ui.View):
    """Vista para dar de baja vehículos"""
    def __init__(self, options: list):
        super().__init__(timeout=300)
        self.add_item(VehicleUnregisterSelect(options))

class VehicleUnregisterSelect(discord.ui.Select):
    def __init__(self, options: list):
        super().__init__(
            placeholder="Selecciona el vehículo a dar de baja...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        vehicle_id = self.values[0]
        
        try:
            # Dar de baja el vehículo
            success = await unregister_vehicle(vehicle_id, str(interaction.guild.id))
            
            if success:
                embed = discord.Embed(
                    title="✅ Vehículo Dado de Baja",
                    description=f"El vehículo `{vehicle_id}` ha sido dado de baja exitosamente.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔄 Acciones Realizadas",
                    value="• Vehículo marcado como inactivo\n• Seguro cancelado (si existía)\n• Registro actualizado en la base de datos",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Información",
                    value="Puedes registrar un nuevo vehículo con el mismo ID en el futuro si es necesario.",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Vehículo dado de baja: {vehicle_id} por {interaction.user.display_name} ({interaction.user.id})")
                
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo dar de baja el vehículo",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error dando de baja vehículo: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error dando de baja el vehículo",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

# === SISTEMA DE ESCUADRONES ===

class SquadronSystemView(discord.ui.View):
    """Vista con botones para el sistema de escuadrones"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🏆 Crear Escuadrón", style=discord.ButtonStyle.success, custom_id="create_squadron")
    async def create_squadron_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para crear un nuevo escuadrón"""
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
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para crear un escuadrón necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 ¿Cómo configurar mi nombre?",
                    value="Ve al canal de **welcome** y usa el botón **'🎮 Actualizar Nombre InGame'**",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya pertenece a un escuadrón
            existing_squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
            
            if existing_squadron:
                embed = discord.Embed(
                    title="⚠️ Ya Tienes un Escuadrón",
                    description=f"Ya eres **{existing_squadron['role'].title()}** del escuadrón **{existing_squadron['squadron_name']}** ({existing_squadron['squadron_type']})",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🎯 ¿Qué puedes hacer?",
                    value="• **📋 Mi Escuadrón** - Ver detalles y gestionar tu equipo\n• **🚪 Salir del Escuadrón** - Abandonar tu equipo actual\n• **Contactar Admin** - Para cambiar de escuadrón directamente",
                    inline=False
                )
                
                # Información específica según el rol
                if existing_squadron['role'] == 'leader':
                    embed.add_field(
                        name="👑 Como Líder",
                        value="Puedes transferir el liderazgo a otro miembro desde **'📋 Mi Escuadrón'**",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Mostrar modal para crear escuadrón
            modal = CreateSquadronModal()
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error en creación de escuadrón: {e}")
            if not interaction.response.is_done():
                embed = discord.Embed(
                    title="❌ Error del Sistema",
                    description="Hubo un error procesando tu solicitud",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📋 Mi Escuadrón", style=discord.ButtonStyle.primary, custom_id="my_squadron")
    async def my_squadron_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para ver detalles del escuadrón del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener escuadrón del usuario
            squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
            
            if not squadron:
                embed = discord.Embed(
                    title="🏆 Sin Escuadrón",
                    description="**No perteneces a ningún escuadrón actualmente.**",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎯 ¿Quieres crear uno?",
                    value="Usa el botón **'🏆 Crear Escuadrón'** para formar tu propio equipo",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Mostrar detalles del escuadrón
            embed = discord.Embed(
                title=f"🏆 {squadron['squadron_name']}",
                description=f"**Tipo:** {squadron['squadron_type']} • **Tu Rol:** {squadron['role'].title()}",
                color=0xff6600 if squadron['squadron_type'] == 'PvP' else 0x00aa00
            )
            
            embed.add_field(
                name="👑 Líder",
                value=squadron['leader_ingame_name'],
                inline=True
            )
            
            embed.add_field(
                name="📅 Creado",
                value=squadron['created_at'][:10],
                inline=True
            )
            
            embed.add_field(
                name="📊 Estado",
                value="🟢 Activo" if squadron['status'] == 'active' else "🔴 Inactivo",
                inline=True
            )
            
            # Obtener miembros del escuadrón
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM squadron_members 
                    WHERE squadron_id = ? AND status = 'active'
                """, (squadron['id'],))
                member_count = (await cursor.fetchone())[0]
            
            embed.add_field(
                name="👥 Miembros",
                value=f"{member_count}/{squadron['max_members']}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Beneficios Activos",
                value=f"• Identificación automática como **{squadron['squadron_type']}**\n• Límites de vehículos optimizados\n• Tarifas de seguro grupales",
                inline=False
            )
            
            # Si es líder, mostrar opciones de gestión
            if squadron['role'] == 'leader':
                view = SquadronLeaderManagementView(squadron)
                embed.add_field(
                    name="👑 Opciones de Líder",
                    value="Como líder, puedes gestionar tu escuadrón usando los botones de abajo",
                    inline=False
                )
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error consultando escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando tu escuadrón",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔍 Explorar Escuadrones", style=discord.ButtonStyle.secondary, custom_id="explore_squadrons")
    async def explore_squadrons_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para ver escuadrones disponibles y unirse a ellos"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario ya pertenece a un escuadrón
            existing_squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
            
            if existing_squadron:
                embed = discord.Embed(
                    title="💡 Ya Perteneces a un Escuadrón",
                    description=f"Actualmente eres **{existing_squadron['role'].title()}** del escuadrón **{existing_squadron['squadron_name']}** ({existing_squadron['squadron_type']})",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎯 ¿Qué puedes hacer?",
                    value="• **📋 Mi Escuadrón** - Ver detalles y gestionar tu equipo\n• **🚪 Salir del Escuadrón** - Si quieres cambiar de equipo\n• **Ver info de otros** - Solo disponible sin escuadrón",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 ¿Por qué no puedo explorar?",
                    value="Solo usuarios sin escuadrón pueden explorar y unirse a otros equipos. Debes salir de tu escuadrón actual primero.",
                    inline=False
                )
                
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para unirte a un escuadrón necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 ¿Cómo configurar mi nombre?",
                    value="Ve al canal de **welcome** y usa el botón **'🎮 Actualizar Nombre InGame'**",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener escuadrones activos
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT s.*, COUNT(sm.id) as member_count 
                    FROM squadrons s
                    LEFT JOIN squadron_members sm ON s.id = sm.squadron_id AND sm.status = 'active'
                    WHERE s.guild_id = ? AND s.status = 'active'
                    GROUP BY s.id
                    ORDER BY s.created_at DESC
                    LIMIT 10
                """, (str(interaction.guild.id),))
                
                squadrons = await cursor.fetchall()
            
            if not squadrons:
                embed = discord.Embed(
                    title="🔍 Sin Escuadrones Activos",
                    description="No hay escuadrones activos en este servidor.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎯 ¡Sé el Primero!",
                    value="Usa el botón **'🏆 Crear Escuadrón'** para formar el primer equipo",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear vista con selector de escuadrones para unirse
            join_squadron_view = JoinSquadronSelectView(squadrons, user_data)
            
            embed = discord.Embed(
                title="🔍 Escuadrones Disponibles",
                description=f"**{len(squadrons)}** escuadrón(es) disponible(s) en **{interaction.guild.name}**\n\nSelecciona un escuadrón para unirte:",
                color=0x3498db
            )
            
            # Mostrar información de los primeros 5 escuadrones
            for squadron in squadrons[:5]:
                squadron_name = squadron[2]  # squadron_name
                squadron_type = squadron[3]  # squadron_type
                leader_name = squadron[5]    # leader_ingame_name
                member_count = squadron[9]   # member_count
                max_members = squadron[8]    # max_members
                
                type_emoji = "⚔️" if squadron_type == 'PvP' else "🛡️" if squadron_type == 'PvE' else "⚡"
                
                # Indicar si está lleno
                status = " (LLENO)" if member_count >= max_members else ""
                
                embed.add_field(
                    name=f"{type_emoji} {squadron_name}{status}",
                    value=f"**Tipo:** {squadron_type}\n**Líder:** {leader_name}\n**Miembros:** {member_count}/{max_members}",
                    inline=True
                )
            
            if len(squadrons) > 5:
                embed.add_field(
                    name="📋 Información",
                    value=f"Mostrando 5 de {len(squadrons)} escuadrones",
                    inline=False
                )
            
            embed.set_footer(text="Usa el selector de abajo para unirte a un escuadrón")
            
            await interaction.followup.send(embed=embed, view=join_squadron_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error explorando escuadrones: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando los escuadrones",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🚪 Salir del Escuadrón", style=discord.ButtonStyle.danger, custom_id="leave_squadron")
    async def leave_squadron_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón para salir del escuadrón actual"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario pertenece a un escuadrón
            user_squadron = await get_user_squadron(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_squadron:
                # Mensaje más útil cuando no pertenece a ningún escuadrón
                embed = discord.Embed(
                    title="💡 No Perteneces a Ningún Escuadrón",
                    description="No estás en ningún escuadrón actualmente, por lo que no hay nada de lo que salir.",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🎯 ¿Qué puedes hacer?",
                    value="• **🏆 Crear Escuadrón** - Forma tu propio equipo\n• **🔍 Explorar Escuadrones** - Únete a uno existente",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 ¿Por qué ves este botón?",
                    value="Este botón está disponible para todos los usuarios. Solo funcionará si perteneces a un escuadrón.",
                    inline=False
                )
                
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Si llegamos aquí, el usuario SÍ pertenece a un escuadrón
            # Verificar si es el líder
            if user_squadron['role'] == 'leader':
                embed = discord.Embed(
                    title="❌ Líder No Puede Salir",
                    description="Como líder del escuadrón, no puedes salir voluntariamente.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎯 Opciones Disponibles",
                    value="• **Transfiere el liderazgo** a otro miembro primero\n• Contacta a un **administrador** para disolución\n• Los admins pueden removerte sin restricciones",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar período de enfriamiento
            can_leave, time_remaining, last_squadron = await can_leave_squadron(str(interaction.user.id), str(interaction.guild.id))
            
            if not can_leave:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                
                embed = discord.Embed(
                    title="⏰ Período de Enfriamiento Activo",
                    description=f"Debes esperar **{hours}h {minutes}m** antes de poder salir de otro escuadrón.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="📋 Información",
                    value=f"• **Último escuadrón:** {last_squadron}\n• **Tiempo restante:** {hours}h {minutes}m\n• **Razón:** Prevenir spam de entradas/salidas",
                    inline=False
                )
                embed.add_field(
                    name="🎯 Alternativas",
                    value="• **Administradores** pueden removerte sin restricciones\n• Espera el tiempo restante para salir voluntariamente",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear embed de confirmación
            embed = discord.Embed(
                title="⚠️ Confirmar Salida del Escuadrón",
                description=f"¿Estás seguro de que quieres salir del escuadrón **{user_squadron['squadron_name']}**?",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📋 Información del Escuadrón",
                value=f"• **Nombre:** {user_squadron['squadron_name']}\n• **Tipo:** {user_squadron['squadron_type']}\n• **Tu Rol:** {user_squadron['role'].title()}",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Consecuencias",
                value="• Perderás acceso a los beneficios del escuadrón\n• No podrás unirte a otro escuadrón por **24 horas**\n• Deberás volver a solicitar unión si cambias de opinión",
                inline=False
            )
            
            embed.add_field(
                name="🎯 ¿Continuar?",
                value="Confirma tu decisión usando los botones de abajo",
                inline=False
            )
            
            # Crear vista de confirmación
            confirm_view = LeaveSquadronConfirmView(user_squadron)
            await interaction.followup.send(embed=embed, view=confirm_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en botón de salir del escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando tu solicitud",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class LeaveSquadronConfirmView(discord.ui.View):
    """Vista de confirmación para salir del escuadrón"""
    
    def __init__(self, squadron_data: dict):
        super().__init__(timeout=300)  # 5 minutos
        self.squadron_data = squadron_data
    
    @discord.ui.button(label="✅ Confirmar Salida", style=discord.ButtonStyle.danger)
    async def confirm_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar la salida del escuadrón"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Ejecutar la salida del escuadrón
            success = await leave_squadron(
                str(interaction.user.id), 
                str(interaction.guild.id), 
                reason='voluntary'
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Has Salido del Escuadrón",
                    description=f"Has salido exitosamente del escuadrón **{self.squadron_data['squadron_name']}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📋 Detalles",
                    value=f"• **Escuadrón:** {self.squadron_data['squadron_name']}\n• **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n• **Razón:** Salida voluntaria",
                    inline=False
                )
                
                embed.add_field(
                    name="⏰ Período de Enfriamiento",
                    value="No podrás unirte a otro escuadrón por **24 horas**",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 Próximos Pasos",
                    value="• Puedes crear tu propio escuadrón inmediatamente\n• Para unirte a otro, espera 24 horas\n• Los administradores pueden override este período",
                    inline=False
                )
                
                # Deshabilitar botones
                for child in self.children:
                    child.disabled = True
                
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
                
            else:
                embed = discord.Embed(
                    title="❌ Error al Salir",
                    description="No se pudo procesar tu salida del escuadrón",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error confirmando salida del escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando tu salida",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar la salida del escuadrón"""
        embed = discord.Embed(
            title="❌ Salida Cancelada",
            description=f"Has cancelado la salida del escuadrón **{self.squadron_data['squadron_name']}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎯 Te Quedas en el Equipo",
            value="Sigues siendo parte del escuadrón con todos los beneficios",
            inline=False
        )
        
        # Deshabilitar botones
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class JoinSquadronSelectView(discord.ui.View):
    """Vista para seleccionar y unirse a un escuadrón"""
    
    def __init__(self, squadrons: list, user_data: dict):
        super().__init__(timeout=300)  # 5 minutos
        self.squadrons = squadrons
        self.user_data = user_data
        
        # Crear opciones para el selector (máximo 25 por limitación de Discord)
        options = []
        for squadron in squadrons[:25]:
            squadron_id = squadron[0]
            squadron_name = squadron[2]
            squadron_type = squadron[3]
            member_count = squadron[9] if len(squadron) > 9 else 0
            max_members = squadron[8] if len(squadron) > 8 else 10
            
            type_emoji = "⚔️" if squadron_type == 'PvP' else "🛡️"
            
            # Verificar si está lleno
            is_full = member_count >= max_members
            description = f"{squadron_type} • {member_count}/{max_members} miembros"
            if is_full:
                description += " • LLENO"
            
            options.append(discord.SelectOption(
                label=squadron_name,
                value=str(squadron_id),
                emoji=type_emoji,
                description=description
            ))
        
        # Agregar selector si hay opciones
        if options:
            self.add_item(SquadronJoinSelect(options, self.user_data))

class SquadronJoinSelect(discord.ui.Select):
    """Selector para elegir escuadrón al cual unirse"""
    
    def __init__(self, options: list, user_data: dict):
        self.user_data = user_data
        super().__init__(
            placeholder="Selecciona un escuadrón para unirte...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        squadron_id = int(self.values[0])
        
        try:
            # Obtener información detallada del escuadrón
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT s.*, COUNT(sm.id) as member_count 
                    FROM squadrons s
                    LEFT JOIN squadron_members sm ON s.id = sm.squadron_id AND sm.status = 'active'
                    WHERE s.id = ?
                    GROUP BY s.id
                """, (squadron_id,))
                
                squadron = await cursor.fetchone()
            
            if not squadron:
                embed = discord.Embed(
                    title="❌ Escuadrón No Encontrado",
                    description="El escuadrón seleccionado no existe o no está disponible",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            squadron_name = squadron[2]
            squadron_type = squadron[3]
            member_count = squadron[9]
            max_members = squadron[8]
            
            # Verificar si está lleno
            if member_count >= max_members:
                embed = discord.Embed(
                    title="⚠️ Escuadrón Lleno",
                    description=f"El escuadrón **{squadron_name}** ha alcanzado su límite máximo de miembros ({max_members})",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Mostrar confirmación
            join_confirm_view = JoinSquadronConfirmView(squadron, self.user_data)
            
            type_emoji = "⚔️" if squadron_type == 'PvP' else "🛡️"
            
            embed = discord.Embed(
                title=f"🤝 Confirmar Unión al Escuadrón",
                description=f"¿Deseas unirte al escuadrón **{squadron_name}**?",
                color=0x00ff00
            )
            
            embed.add_field(
                name=f"{type_emoji} Información del Escuadrón",
                value=f"**Nombre:** {squadron_name}\n**Tipo:** {squadron_type}\n**Miembros:** {member_count}/{max_members}",
                inline=True
            )
            
            # Beneficios específicos según tipo
            if squadron_type == "PvP":
                benefits = "• Identificación automática como **PvP** en seguros\n• Tarifas con recargo PvP automático\n• Coordinación para raids y combate"
            else:
                benefits = "• Identificación automática como **PvE** en seguros\n• Tarifas estándar sin recargo\n• Coordinación para exploración y supervivencia"
            
            embed.add_field(
                name="🎯 Beneficios que Obtienes",
                value=benefits,
                inline=True
            )
            
            embed.add_field(
                name="📋 Tu Información",
                value=f"**Discord:** {interaction.user.display_name}\n**InGame:** {self.user_data['ingame_name']}",
                inline=False
            )
            
            embed.set_footer(text="Esta acción no se puede deshacer fácilmente")
            
            await interaction.response.send_message(embed=embed, view=join_confirm_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en selección de escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando tu selección",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class JoinSquadronConfirmView(discord.ui.View):
    """Vista de confirmación para unirse a un escuadrón"""
    
    def __init__(self, squadron: tuple, user_data: dict):
        super().__init__(timeout=120)  # 2 minutos
        self.squadron = squadron
        self.user_data = user_data
    
    @discord.ui.button(label="✅ Confirmar Unión", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar unión al escuadrón"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            squadron_id = self.squadron[0]
            squadron_name = self.squadron[2]
            squadron_type = self.squadron[3]
            
            # Unirse al escuadrón
            success = await join_squadron(
                squadron_id,
                str(interaction.user.id),
                self.user_data['ingame_name']
            )
            
            if success:
                type_emoji = "⚔️" if squadron_type == 'PvP' else "🛡️"
                embed_color = discord.Color.red() if squadron_type == 'PvP' else discord.Color.green()
                
                embed = discord.Embed(
                    title="🎉 ¡Bienvenido al Escuadrón!",
                    description=f"Te has unido exitosamente al escuadrón **{squadron_name}**",
                    color=embed_color
                )
                
                embed.add_field(
                    name=f"{type_emoji} Tu Nuevo Escuadrón",
                    value=f"**Nombre:** {squadron_name}\n**Tipo:** {squadron_type}\n**Tu Rol:** Miembro",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Beneficios Activados",
                    value=f"• **Detección automática** de zona {squadron_type}\n• **Tarifas optimizadas** en seguros\n• **Acceso al sistema** de coordinación",
                    inline=True
                )
                
                embed.add_field(
                    name="📋 Próximos Pasos",
                    value="• Usa **'📋 Mi Escuadrón'** para ver detalles\n• Los seguros detectarán automáticamente tu zona\n• Coordina con tu equipo para actividades",
                    inline=False
                )
                
                embed.set_footer(text=f"¡Ahora eres parte del equipo {squadron_type}!")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"Usuario {self.user_data['ingame_name']} ({interaction.user.id}) se unió al escuadrón {squadron_name}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error al Unirse",
                    description="No se pudo completar la unión al escuadrón. Inténtalo de nuevo.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error confirmando unión a escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando tu unión al escuadrón",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar unión al escuadrón"""
        embed = discord.Embed(
            title="🚫 Unión Cancelada",
            description="Has cancelado la unión al escuadrón",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CreateSquadronModal(discord.ui.Modal, title="🏆 Crear Nuevo Escuadrón"):
    def __init__(self):
        super().__init__()
    
    squadron_name = discord.ui.TextInput(
        label="Nombre del Escuadrón",
        placeholder="Ingresa el nombre de tu escuadrón (ej: Los Supervivientes)",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar nombre
            name = self.squadron_name.value.strip()
            
            if len(name) < 3:
                embed = discord.Embed(
                    title="❌ Nombre Inválido",
                    description="El nombre del escuadrón debe tener al menos 3 caracteres",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar que el nombre no esté en uso
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT id FROM squadrons 
                    WHERE guild_id = ? AND squadron_name = ? AND status = 'active'
                """, (str(interaction.guild.id), name))
                
                existing = await cursor.fetchone()
                if existing:
                    embed = discord.Embed(
                        title="❌ Nombre en Uso",
                        description=f"Ya existe un escuadrón llamado **{name}** en este servidor",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Mostrar selector de tipo de escuadrón
            type_selector_view = SquadronTypeSelectView(name, interaction.user, interaction.guild)
            
            embed = discord.Embed(
                title="⚔️ Seleccionar Tipo de Escuadrón",
                description=f"**Escuadrón:** {name}\n\nElige el tipo de escuadrón que mejor represente tu estilo de juego:",
                color=0xff6600
            )
            
            embed.add_field(
                name="⚔️ PvP (Jugador vs Jugador)",
                value="• Enfoque en combate y raids\n• Tarifas de seguro con recargo PvP\n• Ideal para equipos agresivos",
                inline=True
            )
            
            embed.add_field(
                name="🛡️ PvE (Jugador vs Entorno)",
                value="• Enfoque en supervivencia y exploración\n• Tarifas de seguro estándar\n• Ideal para equipos cooperativos",
                inline=True
            )
            
            embed.add_field(
                name="🎯 ¿Cuál elegir?",
                value="El tipo determina las tarifas de seguro automáticas y beneficios específicos para tu equipo.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=type_selector_view, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error validando escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando el nombre del escuadrón",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class SquadronTypeSelectView(discord.ui.View):
    """Vista para seleccionar el tipo de escuadrón (PvP o PvE)"""
    
    def __init__(self, squadron_name: str, user: discord.User, guild: discord.Guild):
        super().__init__(timeout=300)  # 5 minutos
        self.squadron_name = squadron_name
        self.user = user
        self.guild = guild
    
    @discord.ui.button(label="⚔️ PvP", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def select_pvp(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Seleccionar tipo PvP"""
        await self._create_squadron(interaction, "PvP")
    
    @discord.ui.button(label="🛡️ PvE", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def select_pve(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Seleccionar tipo PvE"""
        await self._create_squadron(interaction, "PvE")
    
    async def _create_squadron(self, interaction: discord.Interaction, squadron_type: str):
        """Crear el escuadrón con el tipo seleccionado"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar usuario registrado
            user_data = await get_user_by_discord_id(str(self.user.id), str(self.guild.id))
            if not user_data or not user_data.get('ingame_name'):
                embed = discord.Embed(
                    title="❌ Error de Usuario",
                    description="Usuario no registrado o sin nombre InGame",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear escuadrón
            squadron_id = await create_squadron(
                str(self.guild.id),
                self.squadron_name,
                squadron_type,
                str(self.user.id),
                user_data['ingame_name']
            )
            
            if squadron_id:
                # Determinar emoji y color según tipo
                type_emoji = "⚔️" if squadron_type == "PvP" else "🛡️"
                embed_color = discord.Color.red() if squadron_type == "PvP" else discord.Color.green()
                
                embed = discord.Embed(
                    title=f"✅ Escuadrón {squadron_type} Creado",
                    description=f"Tu escuadrón **{self.squadron_name}** ha sido creado exitosamente",
                    color=embed_color
                )
                
                embed.add_field(
                    name="🏆 Información del Escuadrón",
                    value=f"**Nombre:** {self.squadron_name}\n**Tipo:** {type_emoji} {squadron_type}\n**Líder:** {user_data['ingame_name']}",
                    inline=True
                )
                
                # Beneficios específicos según tipo
                if squadron_type == "PvP":
                    benefits = "• Identificación automática como **PvP**\n• Seguros con recargo PvP automático\n• Acceso a características de combate\n• Coordinación para raids y ataques"
                else:
                    benefits = "• Identificación automática como **PvE**\n• Seguros a precio estándar\n• Acceso a características cooperativas\n• Coordinación para exploración y construcción"
                
                embed.add_field(
                    name="🎯 Beneficios Activados",
                    value=benefits,
                    inline=True
                )
                
                embed.add_field(
                    name="📋 Siguiente Paso",
                    value="Invita a otros jugadores a unirse a tu escuadrón. Los miembros obtendrán los mismos beneficios automáticamente.",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Detección Automática",
                    value=f"Cuando los miembros soliciten seguros, se detectará automáticamente como zona **{squadron_type}**",
                    inline=False
                )
                
                embed.set_footer(text=f"¡Listo para dominar SCUM en modo {squadron_type}!")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Escuadrón {squadron_type} creado: {self.squadron_name} por {user_data['ingame_name']} ({self.user.id})")
                
            else:
                embed = discord.Embed(
                    title="❌ Error en la Creación",
                    description="No se pudo crear el escuadrón. Inténtalo de nuevo.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error creando escuadrón {squadron_type}: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error creando el escuadrón",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VehicleInsuranceSelectionView(BaseView):
    """Vista para seleccionar vehículo registrado para asegurar"""
    def __init__(self, user_vehicles: list):
        super().__init__(timeout=300)
        self.user_vehicles = user_vehicles
        
        # Crear selector con vehículos del usuario
        options = []
        for vehicle in user_vehicles[:25]:  # Discord limita a 25 opciones
            vehicle_id = vehicle[1]
            vehicle_type = vehicle[2]
            registered_at = vehicle[8][:10]
            notes = vehicle[10] if len(vehicle) > 10 and vehicle[10] else ""
            
            description = f"Registrado: {registered_at}"
            if notes:
                description += f" | {notes[:30]}..."
            
            options.append(discord.SelectOption(
                label=f"{vehicle_type.title()} - {vehicle_id}",
                description=description,
                value=vehicle_id,
                emoji="🚗"
            ))
        
        if options:
            self.add_item(VehicleInsuranceSelect(options, user_vehicles))

class VehicleInsuranceSelect(discord.ui.Select):
    def __init__(self, options: list, user_vehicles: list):
        super().__init__(
            placeholder="🚗 Selecciona el vehículo a asegurar...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.user_vehicles = user_vehicles
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        selected_vehicle_id = self.values[0]
        
        # Buscar el vehículo seleccionado
        selected_vehicle = None
        for vehicle in self.user_vehicles:
            if vehicle[1] == selected_vehicle_id:  # vehicle_id
                selected_vehicle = vehicle
                break
        
        if not selected_vehicle:
            embed = discord.Embed(
                title="❌ Error",
                description="Vehículo no encontrado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Crear vista con selectores para el seguro
        vehicle_id = selected_vehicle[1]
        vehicle_type = selected_vehicle[2]
        description = selected_vehicle[10] if len(selected_vehicle) > 10 and selected_vehicle[10] else ""
        
        view = VehicleInsuranceSelectView(vehicle_id, description, vehicle_type)
        
        embed = discord.Embed(
            title="🚗 Configurar Seguro de Vehículo",
            description=f"**Vehículo Seleccionado:** {vehicle_type.title()} - `{vehicle_id}`\n\nSelecciona las opciones para tu seguro:",
            color=0xff8800
        )
        
        if description:
            embed.add_field(
                name="📝 Descripción del Vehículo",
                value=description,
                inline=False
            )
        
        embed.add_field(
            name="📋 Paso Siguiente",
            value="Completa los selectores de abajo y presiona **'Confirmar Seguro'**",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class InsuranceConfirmationView(BaseView):
    """Vista para confirmar o rechazar solicitudes de seguro en el canal de notificaciones"""
    
    def __init__(self, insurance_data: dict, bot):
        super().__init__(timeout=3600)  # 1 hora para responder
        self.insurance_data = insurance_data
        self.bot = bot
    
    @discord.ui.button(label="✅ Confirmar Seguro", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_insurance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar solicitud de seguro"""
        await interaction.response.defer()
        
        try:
            # Verificar si el usuario es mecánico
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            if not is_mechanic and not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden confirmar seguros",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar si el seguro aún existe y está pendiente
            insurance_id = self.insurance_data['insurance_id']
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT status, confirmed_by FROM vehicle_insurance 
                    WHERE insurance_id = ?
                """, (insurance_id,))
                result = await cursor.fetchone()
                
                if not result:
                    embed = discord.Embed(
                        title="ℹ️ Seguro Ya Procesado",
                        description="Este seguro ya fue procesado o eliminado por otro mecánico/administrador.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="🔄 Estado Actual",
                        value="La solicitud ya no está disponible para procesar.",
                        inline=False
                    )
                    # Deshabilitar botones
                    for item in self.children:
                        item.disabled = True
                    await interaction.edit_original_response(embed=embed, view=self)
                    return
                
                current_status, confirmed_by = result
                if current_status != 'pending_confirmation':
                    # El seguro ya fue procesado
                    status_text = {
                        'active': '✅ Confirmado',
                        'cancelled': '❌ Rechazado',
                        'expired': '⏱️ Expirado'
                    }.get(current_status, current_status)
                    
                    embed = discord.Embed(
                        title="ℹ️ Seguro Ya Procesado",
                        description=f"Este seguro ya fue **{status_text}** por otro mecánico/administrador.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="👤 Procesado Por",
                        value=f"<@{confirmed_by}>" if confirmed_by else "Sistema/Administrador",
                        inline=True
                    )
                    embed.add_field(
                        name="📋 Estado Actual",
                        value=status_text,
                        inline=True
                    )
                    # Deshabilitar botones
                    for item in self.children:
                        item.disabled = True
                    await interaction.edit_original_response(embed=embed, view=self)
                    return
            
            # Procesar el pago si es método Discord
            payment_success = True
            if self.insurance_data['payment_method'] == 'discord':
                # Aquí debería ir la lógica de débito de Discord
                # Por ahora simulamos el éxito
                payment_success = True
            
            if payment_success:
                # Actualizar estado del seguro a activo
                insurance_id = self.insurance_data['insurance_id']
                
                # Actualizar en base de datos
                async with aiosqlite.connect(taxi_db.db_path) as db:
                    await db.execute("""
                        UPDATE vehicle_insurance 
                        SET status = 'active', confirmed_by = ?, confirmed_at = ?
                        WHERE insurance_id = ?
                    """, (str(interaction.user.id), datetime.now().isoformat(), insurance_id))
                    await db.commit()
                
                # Crear embed de confirmación
                embed = discord.Embed(
                    title="✅ Seguro Confirmado",
                    description=f"Seguro confirmado por {interaction.user.mention}",
                    color=discord.Color.green()
                )
                
                # Fallback para owner_ingame_name en caso de datos migrados
                client_name = self.insurance_data.get('owner_ingame_name') or self.insurance_data.get('ingame_name') or 'Cliente'
                
                embed.add_field(
                    name="📋 Detalles",
                    value=f"**ID:** `{insurance_id}`\n**Cliente:** {client_name}\n**Vehículo:** {self.insurance_data['vehicle_type'].title()}\n**Costo:** ${self.insurance_data['cost']:,.0f}",
                    inline=False
                )
                
                # Deshabilitar botones
                for item in self.children:
                    item.disabled = True
                
                await interaction.edit_original_response(embed=embed, view=self)
                
                # Notificar al cliente por DM
                try:
                    user = self.bot.get_user(int(self.insurance_data['owner_discord_id']))
                    if user:
                        client_embed = discord.Embed(
                            title="✅ Seguro Confirmado",
                            description="Tu solicitud de seguro ha sido confirmada por un mecánico",
                            color=discord.Color.green()
                        )
                        client_embed.add_field(
                            name="📋 Detalles",
                            value=f"**ID Seguro:** `{insurance_id}`\n**Vehículo:** {self.insurance_data['vehicle_type'].title()}\n**Estado:** Activo",
                            inline=False
                        )
                        await user.send(embed=client_embed)
                except Exception as e:
                    logger.error(f"Error notificando cliente: {e}")
                
            else:
                # Error en el pago
                embed = discord.Embed(
                    title="❌ Error en el Pago",
                    description="No se pudo procesar el pago del seguro",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error confirmando seguro: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando la confirmación",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Rechazar Seguro", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_insurance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rechazar solicitud de seguro"""
        await interaction.response.defer()
        
        try:
            # Verificar si el usuario es mecánico
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            if not is_mechanic and not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden rechazar seguros",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar si el seguro aún existe y está pendiente
            insurance_id = self.insurance_data['insurance_id']
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT status, confirmed_by FROM vehicle_insurance 
                    WHERE insurance_id = ?
                """, (insurance_id,))
                result = await cursor.fetchone()
                
                if not result:
                    embed = discord.Embed(
                        title="ℹ️ Seguro Ya Procesado",
                        description="Este seguro ya fue procesado o eliminado por otro mecánico/administrador.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="🔄 Estado Actual",
                        value="La solicitud ya no está disponible para procesar.",
                        inline=False
                    )
                    # Deshabilitar botones
                    for item in self.children:
                        item.disabled = True
                    await interaction.edit_original_response(embed=embed, view=self)
                    return
                
                current_status, confirmed_by = result
                if current_status != 'pending_confirmation':
                    # El seguro ya fue procesado
                    status_text = {
                        'active': '✅ Confirmado',
                        'cancelled': '❌ Rechazado',
                        'expired': '⏱️ Expirado'
                    }.get(current_status, current_status)
                    
                    embed = discord.Embed(
                        title="ℹ️ Seguro Ya Procesado",
                        description=f"Este seguro ya fue **{status_text}** por otro mecánico/administrador.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="👤 Procesado Por",
                        value=f"<@{confirmed_by}>" if confirmed_by else "Sistema/Administrador",
                        inline=True
                    )
                    embed.add_field(
                        name="📋 Estado Actual",
                        value=status_text,
                        inline=True
                    )
                    # Deshabilitar botones
                    for item in self.children:
                        item.disabled = True
                    await interaction.edit_original_response(embed=embed, view=self)
                    return
            
            # Eliminar el seguro de la base de datos
            insurance_id = self.insurance_data['insurance_id']
            
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute("""
                    DELETE FROM vehicle_insurance WHERE insurance_id = ?
                """, (insurance_id,))
                await db.commit()
            
            # Crear embed de rechazo
            embed = discord.Embed(
                title="❌ Seguro Rechazado",
                description=f"Seguro rechazado por {interaction.user.mention}",
                color=discord.Color.red()
            )
            
            # Fallback para owner_ingame_name en caso de datos migrados
            client_name = self.insurance_data.get('owner_ingame_name') or self.insurance_data.get('ingame_name') or 'Cliente'
            
            embed.add_field(
                name="📋 Detalles",
                value=f"**ID:** `{insurance_id}`\n**Cliente:** {client_name}\n**Vehículo:** {self.insurance_data['vehicle_type'].title()}",
                inline=False
            )
            
            embed.add_field(
                name="💰 Reembolso",
                value="No se realizó ningún cargo. El cliente no fue debitado.",
                inline=False
            )
            
            # Deshabilitar botones
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Notificar al cliente por DM
            try:
                user = self.bot.get_user(int(self.insurance_data['owner_discord_id']))
                if user:
                    client_embed = discord.Embed(
                        title="❌ Seguro Rechazado",
                        description="Tu solicitud de seguro ha sido rechazada por un mecánico",
                        color=discord.Color.red()
                    )
                    client_embed.add_field(
                        name="💰 Tranquilo",
                        value="No se realizó ningún cargo a tu cuenta de Discord.",
                        inline=False
                    )
                    client_embed.add_field(
                        name="🔄 Próximos pasos",
                        value="Puedes intentar crear un nuevo seguro cuando resuelvas cualquier problema con el vehículo.",
                        inline=False
                    )
                    await user.send(embed=client_embed)
            except Exception as e:
                logger.error(f"Error notificando cliente: {e}")
                
        except Exception as e:
            logger.error(f"Error rechazando seguro: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando el rechazo",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class MechanicSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mechanic_channels = {}  # {guild_id: channel_id}
        self.squadron_channels = {}  # {guild_id: channel_id}
        self.mechanic_notification_channels = {}  # {guild_id: channel_id} - Canal para notificaciones de mecánico
    
    async def cog_load(self):
        """Cargar configuraciones al inicializar el cog"""
        await self.init_database()
        await self.load_channel_configs()
    
    async def init_database(self):
        """Inicializar tablas de seguros de vehículos"""
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS vehicle_insurance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insurance_id TEXT UNIQUE,
                        vehicle_id TEXT NOT NULL,
                        vehicle_type TEXT NOT NULL,
                        vehicle_location TEXT NOT NULL,
                        description TEXT,
                        owner_discord_id TEXT NOT NULL,
                        owner_ingame_name TEXT NOT NULL,
                        guild_id TEXT NOT NULL,
                        cost INTEGER NOT NULL,
                        payment_method TEXT DEFAULT 'discord',
                        status TEXT DEFAULT 'active',
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        UNIQUE(vehicle_id, guild_id)
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS mechanic_services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT UNIQUE,
                        vehicle_insurance_id TEXT,
                        service_type TEXT NOT NULL,
                        description TEXT,
                        cost INTEGER NOT NULL,
                        mechanic_discord_id TEXT,
                        client_discord_id TEXT NOT NULL,
                        guild_id TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        FOREIGN KEY (vehicle_insurance_id) REFERENCES vehicle_insurance(insurance_id)
                    )
                """)
                
                # Tabla de mecánicos registrados
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS registered_mechanics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT NOT NULL,
                        discord_guild_id TEXT NOT NULL,
                        ingame_name TEXT NOT NULL,
                        registered_by TEXT NOT NULL,
                        registered_at TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        UNIQUE(discord_id, discord_guild_id)
                    )
                """)
                
                # Tabla de historial de seguros (para logs y auditoría)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS insurance_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insurance_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        performed_by TEXT,
                        performed_at TEXT NOT NULL,
                        guild_id TEXT NOT NULL
                    )
                """)
                
                # Tabla de preferencias de mecánicos
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS mechanic_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT NOT NULL,
                        discord_guild_id TEXT NOT NULL,
                        receive_notifications BOOLEAN DEFAULT TRUE,
                        notification_types TEXT DEFAULT 'all',
                        updated_at TEXT NOT NULL,
                        UNIQUE(discord_id, discord_guild_id)
                    )
                """)
                
                # Tabla de configuración del servidor (para PVP markup y otros settings)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS server_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(guild_id, config_key)
                    )
                """)
                
                # Tabla de precios de vehículos personalizables por servidor
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS vehicle_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id TEXT NOT NULL,
                        vehicle_type TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        updated_by TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(guild_id, vehicle_type)
                    )
                """)
                
                # Tabla de escuadrones
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS squadrons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id TEXT NOT NULL,
                        squadron_name TEXT NOT NULL,
                        squadron_type TEXT NOT NULL, -- 'PvP' o 'PvE'
                        leader_discord_id TEXT NOT NULL,
                        leader_ingame_name TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        max_members INTEGER DEFAULT 10,
                        UNIQUE(guild_id, squadron_name)
                    )
                """)
                
                # Tabla de miembros de escuadrones
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS squadron_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        squadron_id INTEGER NOT NULL,
                        discord_id TEXT NOT NULL,
                        ingame_name TEXT NOT NULL,
                        joined_at TEXT NOT NULL,
                        role TEXT DEFAULT 'member', -- 'leader', 'officer', 'member'
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (squadron_id) REFERENCES squadrons(id),
                        UNIQUE(discord_id, squadron_id)
                    )
                """)
                
                # Tabla de vehículos registrados
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS registered_vehicles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vehicle_id TEXT NOT NULL,
                        vehicle_type TEXT NOT NULL,
                        owner_discord_id TEXT NOT NULL,
                        owner_ingame_name TEXT NOT NULL,
                        squadron_id INTEGER,
                        guild_id TEXT NOT NULL,
                        registered_at TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        notes TEXT,
                        FOREIGN KEY (squadron_id) REFERENCES squadrons(id),
                        UNIQUE(guild_id, vehicle_id)
                    )
                """)
                
                # Tabla de límites de vehículos por escuadrón
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS squadron_vehicle_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id TEXT NOT NULL,
                        vehicle_type TEXT NOT NULL,
                        limit_per_member INTEGER NOT NULL,
                        updated_by TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(guild_id, vehicle_type)
                    )
                """)
                
                # Tabla de configuración de vehículos por escuadrón
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS squadron_vehicle_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id TEXT NOT NULL UNIQUE,
                        vehicles_per_member INTEGER NOT NULL DEFAULT 2,
                        max_total_vehicles INTEGER NOT NULL DEFAULT 50,
                        updated_by TEXT,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Tabla de historial de salidas de escuadrones
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS squadron_leave_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT NOT NULL,
                        guild_id TEXT NOT NULL,
                        squadron_id INTEGER NOT NULL,
                        squadron_name TEXT NOT NULL,
                        left_at TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        removed_by TEXT,
                        can_rejoin_at TEXT NOT NULL
                    )
                """)
                
                # Migración: Agregar columna payment_method si no existe
                try:
                    # Verificar si la columna payment_method existe
                    cursor = await db.execute("PRAGMA table_info(vehicle_insurance)")
                    columns = await cursor.fetchall()
                    column_names = [column[1] for column in columns]
                    
                    if 'payment_method' not in column_names:
                        await db.execute("ALTER TABLE vehicle_insurance ADD COLUMN payment_method TEXT DEFAULT 'discord'")
                    
                    if 'confirmed_by' not in column_names:
                        await db.execute("ALTER TABLE vehicle_insurance ADD COLUMN confirmed_by TEXT")
                    
                    if 'confirmed_at' not in column_names:
                        await db.execute("ALTER TABLE vehicle_insurance ADD COLUMN confirmed_at TEXT")
                    
                    if 'owner_ingame_name' not in column_names:
                        await db.execute("ALTER TABLE vehicle_insurance ADD COLUMN owner_ingame_name TEXT")
                        
                        # Actualizar registros existentes que no tengan owner_ingame_name
                        await db.execute("""
                            UPDATE vehicle_insurance 
                            SET owner_ingame_name = 'Usuario-' || substr(owner_discord_id, -4)
                            WHERE owner_ingame_name IS NULL OR owner_ingame_name = ''
                        """)
                except Exception as e:
                    logger.error(f"Error en migración de columnas: {e}")
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos de mecánico: {e}")
    
    async def load_channel_configs(self):
        """Cargar configuraciones de canales desde la base de datos"""
        try:
            # Cargar todos los canales de una vez
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                guild_id_int = int(guild_id)
                
                # Cargar canal de mecánico y recrear panel
                if "mechanic" in channels:
                    channel_id = channels["mechanic"]
                    self.mechanic_channels[guild_id_int] = channel_id
                    logger.info(f"Canal de mecánico cargado para guild {guild_id}: {channel_id}")
                    
                    # Recrear panel de mecánico
                    await self._recreate_mechanic_panel(guild_id_int, channel_id)
                
                # Cargar canal de escuadrones y recrear panel
                if "squadron" in channels:
                    channel_id = channels["squadron"]
                    self.squadron_channels[guild_id_int] = channel_id
                    logger.info(f"Canal de escuadrones cargado para guild {guild_id}: {channel_id}")
                    
                    # Recrear panel de escuadrones
                    await self._recreate_squadron_panel(guild_id_int, channel_id)
                
                # Cargar canal de notificaciones de mecánico
                if "mechanic_notifications" in channels:
                    channel_id = channels["mechanic_notifications"]
                    self.mechanic_notification_channels[guild_id_int] = channel_id
                    logger.info(f"Canal de notificaciones de mecánico cargado para guild {guild_id}: {channel_id}")
                    
        except Exception as e:
            logger.error(f"Error cargando configuraciones de mecánico: {e}")
    
    async def cog_load(self):
        """Ejecutar cuando se carga el cog"""
        await self.init_database()
        await self.load_channel_configs()
        
        # Iniciar task de limpieza automática
        self._cleanup_task = asyncio.create_task(self._start_cleanup_loop())
        logger.info("Task de limpieza automática de canales iniciado")
    
    async def cog_unload(self):
        """Ejecutar cuando se descarga el cog"""
        if hasattr(self, '_cleanup_task'):
            self._cleanup_task.cancel()
            logger.info("Task de limpieza automática cancelado")
    
    async def _start_cleanup_loop(self):
        """Loop de limpieza automática cada 30 minutos"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(1800)  # 30 minutos
                await self._auto_cleanup_channels()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de limpieza automática: {e}")
                await asyncio.sleep(300)  # 5 minutos antes de reintentar
    
    async def _auto_cleanup_channels(self):
        """Limpieza automática de canales de mecánico y escuadrones"""
        try:
            logger.info("Iniciando limpieza automática de canales...")
            
            # Limpiar canales de escuadrones
            for guild_id, channel_id in self.squadron_channels.items():
                await self._cleanup_channel_messages(channel_id, "escuadrones")
                await asyncio.sleep(2)  # Pausa entre limpiezas
            
            # Limpiar canales de mecánico  
            for guild_id, channel_id in self.mechanic_channels.items():
                await self._cleanup_channel_messages(channel_id, "mecánico")
                await asyncio.sleep(2)  # Pausa entre limpiezas
                
            logger.info("Limpieza automática de canales completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza automática de canales: {e}")
    
    async def _cleanup_channel_messages(self, channel_id: int, channel_type: str):
        """Limpiar mensajes del bot en un canal específico"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            # Solo limpiar si tenemos permisos
            if not channel.permissions_for(channel.guild.me).manage_messages:
                return
                
            deleted_count = 0
            messages_to_check = 20  # Revisar solo los últimos 20 mensajes
            
            async for message in channel.history(limit=messages_to_check):
                # Eliminar mensajes del bot que:
                # 1. Sean respuestas efímeras que ya no sean útiles
                # 2. Sean mensajes de error o confirmación antiguos
                # 3. Sean más antiguos de 1 hora
                
                if (message.author == self.bot.user and 
                    (datetime.now() - message.created_at).seconds > 3600):  # Más de 1 hora
                    
                    # Solo eliminar ciertos tipos de mensajes
                    if any(keyword in message.content.lower() for keyword in 
                           ['error', 'completado', 'exitoso', 'fallido', 'procesando']):
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.3)
            
            if deleted_count > 0:
                logger.info(f"Auto-limpieza: Eliminados {deleted_count} mensajes antiguos en canal de {channel_type}")
                
        except Exception as e:
            logger.warning(f"Error en auto-limpieza de canal {channel_type}: {e}")
    
    async def _recreate_mechanic_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de mecánico en el canal especificado con limpieza previa"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de mecánico {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Verificar permisos
            if not channel.permissions_for(channel.guild.me).send_messages:
                logger.warning(f"Sin permisos para enviar mensajes en canal de mecánico {channel_id}")
                return
            
            # Limpiar mensajes anteriores del bot
            try:
                logger.info(f"Limpiando mensajes anteriores en canal de mecánico {channel_id}...")
                deleted_count = 0
                async for message in channel.history(limit=50):
                    if message.author == self.bot.user:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.1)  # Evitar rate limits
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot en canal de mecánico")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes anteriores en canal de mecánico: {cleanup_e}")
            
            # Crear embed principal del mecánico
            embed = discord.Embed(
                title="🔧 Taller Mecánico SCUM",
                description="**Protege tus vehículos con nuestro sistema de seguros**\n\nContrata seguros para tus vehículos y mantén tu inversión protegida en el mundo de SCUM.",
                color=0xff8800
            )
            
            embed.add_field(
                name="🚗 Servicios Disponibles",
                value="• **Seguros de Vehículos** - Protección completa\n• **Consulta de Seguros** - Revisar seguros activos\n• **Registro de Propietarios** - Verificación de titularidad\n• **Gestión de Precios** - Configuración personalizada",
                inline=False
            )
            
            # Obtener precios dinámicos del servidor
            try:
                vehicle_types = ["moto", "ranger", "laika", "ww", "avion", "barca"]
                price_lines = []
                for vehicle_type in vehicle_types:
                    price = await get_vehicle_price(str(guild_id), vehicle_type)
                    emoji_map = {
                        "moto": "🏍️", "ranger": "🚗", "laika": "🚙", 
                        "ww": "🚐", "avion": "✈️", "barca": "🛥️"
                    }
                    emoji = emoji_map.get(vehicle_type, "🚗")
                    price_lines.append(f"{emoji} **{vehicle_type.title()}:** ${price:,.0f}")
                
                # Agregar información de PVP
                pvp_markup = await get_server_pvp_markup(guild_id)
                price_lines.append(f"🗺️ **Zona PVP:** +{pvp_markup}%")
                
                price_text = "\n".join(price_lines)
            except Exception as e:
                logger.warning(f"Error obteniendo precios dinámicos: {e}")
                # Fallback a precios estáticos si hay error
                price_text = "🏍️ **Moto:** $500\n🚗 **Ranger:** $1,200\n🚙 **Laika:** $1,500\n🚐 **WW:** $900\n✈️ **Avion:** $3,500\n🛥️ **Barca:** $800\n🗺️ **Zona PVP:** +25%"
            
            embed.add_field(
                name="💰 Costos de Seguros",
                value=price_text,
                inline=True
            )
            
            embed.add_field(
                name="🎯 Detección Automática",
                value="• **Escuadrones PvP:** Zona PvP automática\n• **Escuadrones PvE:** Zona PvE automática\n• **Sin Escuadrón:** Zona PvE por defecto\n• **Override Manual:** Siempre disponible",
                inline=True
            )
            
            embed.add_field(
                name="💡 Instrucciones",
                value="1. **Solicitar Seguro** - Usa el botón de abajo\n2. **Completar Datos** - Selecciona tipo y método de pago\n3. **Confirmar** - El mecánico procesará tu solicitud\n4. **¡Protegido!** - Tu vehículo estará asegurado",
                inline=False
            )
            
            embed.set_footer(text="Sistema de seguros vehiculares • Protección garantizada")
            
            # Crear vista con botones del mecánico
            mechanic_view = MechanicSystemView()
            await channel.send(embed=embed, view=mechanic_view)
            logger.info(f"✅ Panel de mecánico recreado en guild {guild_id}, canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel de mecánico: {e}")
    
    async def _recreate_squadron_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de escuadrones en el canal especificado con limpieza previa"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de escuadrones {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Verificar permisos
            if not channel.permissions_for(channel.guild.me).send_messages:
                logger.warning(f"Sin permisos para enviar mensajes en canal de escuadrones {channel_id}")
                return
            
            # Limpiar mensajes anteriores del bot de manera más agresiva
            try:
                logger.info(f"Limpiando mensajes anteriores en canal de escuadrones {channel_id}...")
                deleted_count = 0
                
                # Limpiar hasta 100 mensajes anteriores del bot para mantener el canal limpio
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.2)  # Rate limit más conservador
                        
                        # También eliminar mensajes muy antiguos (más de 7 días)
                        if (datetime.now() - message.created_at).days > 7:
                            continue
                
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot en canal de escuadrones")
                    
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes anteriores en canal de escuadrones: {cleanup_e}")
            
            # Crear embed del panel de escuadrones
            squadron_embed = discord.Embed(
                title="🏆 Registro de Escuadrones SCUM",
                description="**¡Únete o crea tu escuadrón para dominar SCUM!**\n\nLos escuadrones determinan el tipo de gameplay y beneficios en vehículos.",
                color=0xff6600
            )
            
            squadron_embed.add_field(
                name="⚔️ Tipos de Escuadrones",
                value="• **PvP:** Combate y raids activos\n• **PvE:** Exploración y supervivencia\n\n*Selector visual al crear escuadrón*",
                inline=True
            )
            
            squadron_embed.add_field(
                name="🎯 Beneficios Automáticos",
                value="• **Detección automática** de zona en seguros\n• **Tarifas optimizadas** según tipo\n• **Límites de vehículos** personalizados\n• **Coordinación de equipo** mejorada",
                inline=True
            )
            
            squadron_embed.add_field(
                name="📋 Requisitos",
                value="• Estar registrado en el sistema\n• Tener nombre InGame configurado\n• No pertenecer a otro escuadrón activo",
                inline=False
            )
            
            squadron_embed.add_field(
                name="🚀 ¿Cómo empezar?",
                value="1. **Registrarte** en el sistema usando `/welcome_registro`\n2. **Configurar** tu nombre InGame en el canal de bienvenida\n3. **Crear** o **unirte** a un escuadrón usando los botones de abajo",
                inline=False
            )
            
            squadron_embed.set_footer(text="Los escuadrones mejoran tu experiencia de juego en SCUM")
            
            # Crear vista estática con custom_id persistente
            # Usamos la vista estática original para mantener persistencia
            squadron_view = SquadronSystemView()
            await channel.send(embed=squadron_embed, view=squadron_view)
            logger.info(f"✅ Panel de escuadrones recreado en guild {guild_id}, canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel de escuadrones: {e}")
    
    async def setup_mechanic_channel(self, guild_id: int, channel_id: int):
        """Configurar canal de mecánico con panel interactivo"""
        # Guardar en memoria
        self.mechanic_channels[guild_id] = channel_id
        
        # Guardar en base de datos
        await taxi_db.save_channel_config(str(guild_id), "mechanic", str(channel_id))
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return False
        
        # Limpiar mensajes anteriores del bot
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user:
                    await message.delete()
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"Error limpiando mensajes en canal de mecánico: {e}")
        
        # Crear embed principal
        embed = discord.Embed(
            title="🔧 Taller Mecánico SCUM",
            description="**Protege tus vehículos con nuestro sistema de seguros**\n\nContrata seguros para tus vehículos y mantén tu inversión protegida en el mundo de SCUM.",
            color=0xff8800
        )
        
        embed.add_field(
            name="🚗 Servicios Disponibles",
            value="• **Seguros de Vehículos** - Protección completa\n• **Consulta de Seguros** - Revisar seguros activos\n• **Registro de Propietarios** - Verificación de titularidad",
            inline=False
        )
        
        embed.add_field(
            name="💰 Costos de Seguros",
            value="🏍️ **Moto:** $500\n🚗 **Ranger:** $1,200\n🚙 **Laika:** $1,500\n🚐 **WW:** $900\n✈️ **Avion:** $3,500\n🗺️ **Zona PVP:** +25%",
            inline=True
        )
        
        embed.add_field(
            name="📋 Requisitos",
            value="✅ Usuario registrado\n✅ Nombre InGame configurado\n✅ Fondos suficientes\n✅ ID único del vehículo",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Instrucciones",
            value="1️⃣ Presiona **'Solicitar Seguro'** para contratar\n2️⃣ Completa el formulario con datos del vehículo\n3️⃣ Confirma el pago del seguro\n4️⃣ Usa **'Consultar Seguros'** para ver tus vehículos asegurados",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Mecánico SCUM • Protección vehicular profesional")
        
        # Crear vista con botones
        view = MechanicSystemView()
        
        # Enviar mensaje principal
        await channel.send(embed=embed, view=view)
        
        return True
    
    # === COMANDOS DE USUARIO ===
    
    @rate_limit("seguro_solicitar")
    @app_commands.command(name="seguro_solicitar", description="🔧 Solicitar seguro para tu vehículo")
    async def request_insurance(self, interaction: discord.Interaction):
        """Solicitar seguro de vehículo"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "seguro_solicitar"):
            return
        
        # Verificar si el sistema está habilitado
        if not taxi_config.FEATURE_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Deshabilitado",
                description="El sistema de mecánico está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar si el usuario está registrado y tiene nombre InGame
        try:
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para usar el taller mecánico necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 ¿Cómo configurar mi nombre?",
                    value="1. Ve al canal de **welcome**\n2. Busca el botón **'🎮 Actualizar Nombre InGame'**\n3. Completa el formulario con tu nombre en SCUM\n4. ¡Luego podrás usar el taller!",
                    inline=False
                )
                embed.add_field(
                    name="🔧 ¿Por qué es necesario?",
                    value="Los mecánicos necesitan identificarte en el servidor para procesar tu seguro correctamente.",
                    inline=False
                )
                embed.set_footer(text="Sistema de Mecánico SCUM • Requisito obligatorio")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
        except Exception as e:
            logger.error(f"Error verificando usuario para seguro: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error verificando tu información. Intenta nuevamente.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para solicitar seguro
        modal = VehicleInsuranceModal()
        await interaction.response.send_modal(modal)
    
    @rate_limit("seguro_consultar")
    @app_commands.command(name="seguro_consultar", description="📋 Consultar seguros de tus vehículos")
    async def check_insurance(self, interaction: discord.Interaction):
        """Consultar seguros activos del usuario"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "seguro_consultar"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario está registrado y tiene nombre InGame
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Requerido",
                    description="**Para consultar seguros necesitas tener un nombre InGame configurado.**",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🎮 Configura tu nombre primero",
                    value="Ve al canal de **welcome** y usa el botón **'🎮 Actualizar Nombre InGame'**",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT insurance_id, vehicle_id, vehicle_type, vehicle_location, 
                           description, owner_discord_id, owner_ingame_name, guild_id, 
                           cost, payment_method, status, created_at, confirmed_by, confirmed_at
                    FROM vehicle_insurance 
                    WHERE owner_discord_id = ? AND guild_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                """, (str(interaction.user.id), str(interaction.guild.id)))
                
                insurances = await cursor.fetchall()
                
                if not insurances:
                    embed = discord.Embed(
                        title="📋 Sin Seguros Activos",
                        description="No tienes vehículos asegurados actualmente.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="💡 ¿Quieres asegurar un vehículo?",
                        value="Usa `/seguro_solicitar` para contratar un seguro",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="🚗 Tus Vehículos Asegurados",
                    description=f"Tienes {len(insurances)} vehículo(s) asegurado(s)",
                    color=discord.Color.green()
                )
                
                for insurance in insurances[:5]:  # Mostrar máximo 5
                    embed.add_field(
                        name=f"🚗 {insurance[3]} - `{insurance[2]}`",  # tipo - vehicle_id
                        value=f"**Ubicación:** {insurance[4]}\n**Seguro ID:** `{insurance[1]}`\n**Fecha:** {insurance[11][:10]}\n**Costo:** ${insurance[9]:,.0f}",
                        inline=True
                    )
                
                if len(insurances) > 5:
                    embed.set_footer(text=f"Mostrando 5 de {len(insurances)} seguros")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error consultando seguros: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando tus seguros",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    # === COMANDOS DE ADMINISTRACIÓN ===
    
    @rate_limit("mechanic_admin_register")
    @app_commands.command(name="mechanic_admin_register", description="[ADMIN] Registrar un usuario como mecánico")
    @app_commands.describe(user="Usuario a registrar como mecánico")
    @app_commands.default_permissions(administrator=True)
    async def register_mechanic(self, interaction: discord.Interaction, user: discord.Member):
        """Registrar un usuario como mecánico"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_register"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario está registrado en el sistema
            user_data = await get_user_by_discord_id(str(user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description=f"{user.display_name} debe registrarse primero en el sistema usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            ingame_name = user_data.get('ingame_name')
            if not ingame_name:
                embed = discord.Embed(
                    title="❌ Nombre InGame Faltante",
                    description=f"{user.display_name} necesita configurar su nombre InGame en el canal de welcome",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya es mecánico activo
            is_already_active_mechanic = await is_user_mechanic(str(user.id), str(interaction.guild.id))
            
            if is_already_active_mechanic:
                embed = discord.Embed(
                    title="⚠️ Ya es Mecánico Activo",
                    description=f"{user.display_name} ya está registrado como mecánico activo",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar si existe mecánico inactivo para reactivar
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, status FROM registered_mechanics 
                    WHERE discord_id = ? AND discord_guild_id = ?
                """, (str(user.id), str(interaction.guild.id)))
                existing_mechanic = await cursor.fetchone()
                
                if existing_mechanic:
                    # Mecánico existe pero está inactivo, reactivar
                    await db.execute("""
                        UPDATE registered_mechanics 
                        SET status = 'active', 
                            ingame_name = ?,
                            registered_by = ?, 
                            registered_at = ?
                        WHERE discord_id = ? AND discord_guild_id = ?
                    """, (
                        ingame_name,
                        str(interaction.user.id),
                        datetime.now().isoformat(),
                        str(user.id),
                        str(interaction.guild.id)
                    ))
                    action_text = "reactivado"
                else:
                    # Mecánico no existe, crear nuevo
                    await db.execute("""
                        INSERT INTO registered_mechanics (discord_id, discord_guild_id, ingame_name, registered_by, registered_at, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(user.id),
                        str(interaction.guild.id),
                        ingame_name,
                        str(interaction.user.id),
                        datetime.now().isoformat(),
                        'active'
                    ))
                    action_text = "registrado"
                
                await db.commit()
            
            embed = discord.Embed(
                title=f"✅ Mecánico {'Reactivado' if action_text == 'reactivado' else 'Registrado'}",
                description=f"**{user.display_name}** ha sido {action_text} como mecánico exitosamente",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="👤 Información del Mecánico",
                value=f"**Discord:** {user.display_name}\n**InGame:** `{ingame_name}`\n**ID Usuario:** {user.id}",
                inline=True
            )
            
            embed.add_field(
                name="🔧 Permisos Otorgados",
                value="• Ver panel de mecánico\n• Consultar todos los seguros\n• Acceso a funciones administrativas del taller",
                inline=True
            )
            
            embed.add_field(
                name=f"📋 {'Reactivado' if action_text == 'reactivado' else 'Registrado'} por",
                value=f"{interaction.user.display_name}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
            
            embed.set_footer(text="Sistema de Mecánico SCUM • Registro administrativo")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error registrando mecánico: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error registrando el mecánico",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_remove")
    @app_commands.command(name="mechanic_admin_remove", description="[ADMIN] Eliminar un mecánico registrado")
    @app_commands.describe(user="Mecánico a eliminar del registro")
    @app_commands.default_permissions(administrator=True)
    async def remove_mechanic(self, interaction: discord.Interaction, user: discord.Member):
        """Eliminar un mecánico del registro"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_remove"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico
            is_mechanic = await is_user_mechanic(str(user.id), str(interaction.guild.id))
            
            if not is_mechanic:
                embed = discord.Embed(
                    title="❌ No es Mecánico",
                    description=f"{user.display_name} no está registrado como mecánico",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Eliminar mecánico (cambiar status a 'inactive')
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute("""
                    UPDATE registered_mechanics 
                    SET status = 'inactive'
                    WHERE discord_id = ? AND discord_guild_id = ?
                """, (str(user.id), str(interaction.guild.id)))
                await db.commit()
            
            embed = discord.Embed(
                title="✅ Mecánico Eliminado",
                description=f"**{user.display_name}** ha sido eliminado del registro de mecánicos",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="👤 Usuario Afectado",
                value=f"**Discord:** {user.display_name}\n**ID:** {user.id}",
                inline=True
            )
            
            embed.add_field(
                name="🚫 Permisos Revocados",
                value="• Panel de mecánico\n• Consulta de seguros\n• Funciones administrativas",
                inline=True
            )
            
            embed.add_field(
                name="📋 Eliminado por",
                value=f"{interaction.user.display_name}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
            
            embed.set_footer(text="El usuario puede ser registrado nuevamente en el futuro")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Mecánico eliminado: {user.display_name} ({user.id}) por {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error eliminando mecánico: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error eliminando el mecánico",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_list")
    @app_commands.command(name="mechanic_admin_list", description="[ADMIN] Listar todos los mecánicos registrados")
    @app_commands.default_permissions(administrator=True)
    async def list_mechanics(self, interaction: discord.Interaction):
        """Listar todos los mecánicos registrados"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_list"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT discord_id, ingame_name, registered_by, registered_at, status
                    FROM registered_mechanics 
                    WHERE discord_guild_id = ?
                    ORDER BY registered_at DESC
                """, (str(interaction.guild.id),))
                
                mechanics = await cursor.fetchall()
            
            if not mechanics:
                embed = discord.Embed(
                    title="📋 Sin Mecánicos Registrados",
                    description="No hay mecánicos registrados en este servidor",
                    color=discord.Color.blue()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🔧 Lista de Mecánicos Registrados",
                description=f"Total: **{len(mechanics)}** mecánicos",
                color=0xff8800
            )
            
            active_mechanics = [m for m in mechanics if m[4] == 'active']
            inactive_mechanics = [m for m in mechanics if m[4] == 'inactive']
            
            embed.add_field(
                name="📊 Resumen",
                value=f"✅ **Activos:** {len(active_mechanics)}\n🚫 **Inactivos:** {len(inactive_mechanics)}",
                inline=True
            )
            
            # Mostrar mecánicos activos
            if active_mechanics:
                mechanics_text = ""
                for mechanic in active_mechanics[:10]:  # Máximo 10
                    discord_user = interaction.guild.get_member(int(mechanic[0]))
                    discord_name = discord_user.display_name if discord_user else "Usuario no encontrado"
                    mechanics_text += f"• **{mechanic[1]}** ({discord_name})\n"
                
                embed.add_field(
                    name="✅ Mecánicos Activos",
                    value=mechanics_text if mechanics_text else "Ninguno",
                    inline=False
                )
            
            # Mostrar mecánicos inactivos si los hay
            if inactive_mechanics:
                inactive_text = ""
                for mechanic in inactive_mechanics[:5]:  # Máximo 5
                    discord_user = interaction.guild.get_member(int(mechanic[0]))
                    discord_name = discord_user.display_name if discord_user else "Usuario no encontrado"
                    inactive_text += f"• **{mechanic[1]}** ({discord_name})\n"
                
                embed.add_field(
                    name="🚫 Mecánicos Inactivos",
                    value=inactive_text if inactive_text else "Ninguno",
                    inline=False
                )
            
            embed.set_footer(text=f"Comando ejecutado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listando mecánicos: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error obteniendo la lista de mecánicos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_notifications")
    @app_commands.command(name="mechanic_notifications", description="🔔 Configurar notificaciones de mecánico")
    @app_commands.describe(enabled="Recibir notificaciones por DM cuando hay nuevos seguros")
    async def configure_notifications(self, interaction: discord.Interaction, enabled: bool):
        """Configurar preferencias de notificaciones para mecánicos"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_notifications"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            
            if not is_mechanic:
                embed = discord.Embed(
                    title="❌ Solo para Mecánicos",
                    description="Este comando es solo para mecánicos registrados",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Guardar preferencia
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO mechanic_preferences 
                    (discord_id, discord_guild_id, receive_notifications, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    str(interaction.user.id),
                    str(interaction.guild.id), 
                    enabled,
                    datetime.now().isoformat()
                ))
                await db.commit()
            
            status_text = "activadas" if enabled else "desactivadas"
            status_emoji = "🔔" if enabled else "🔕"
            
            embed = discord.Embed(
                title=f"{status_emoji} Notificaciones {status_text.title()}",
                description=f"Has **{status_text}** las notificaciones de seguros por DM",
                color=discord.Color.green() if enabled else discord.Color.orange()
            )
            
            if enabled:
                embed.add_field(
                    name="📩 Recibirás notificaciones por:",
                    value="• Nuevas solicitudes de seguro\n• Pagos pendientes InGame\n• Información detallada del cliente y vehículo",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ No recibirás:",
                    value="• Notificaciones DM de nuevos seguros\n• Alertas de pagos pendientes\n• Solo podrás ver seguros en el panel del canal",
                    inline=False
                )
            
            embed.add_field(
                name="💡 Cambiar preferencias",
                value="Usa este comando nuevamente para cambiar tu configuración",
                inline=False
            )
            
            embed.set_footer(text=f"Configuración actualizada • Mecánico: {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Preferencias de notificación actualizadas: {interaction.user.display_name} ({interaction.user.id}) - Habilitado: {enabled}")
            
        except Exception as e:
            logger.error(f"Error configurando notificaciones de mecánico: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error configurando las notificaciones",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_config_pvp")
    @app_commands.command(name="mechanic_admin_config_pvp", description="[ADMIN] Configurar recargo PVP para seguros")
    @app_commands.describe(percentage="Porcentaje de recargo para zonas PVP (ej: 25 para 25% más caro)")
    @app_commands.default_permissions(administrator=True)
    async def config_pvp_markup(self, interaction: discord.Interaction, percentage: float):
        """Configurar porcentaje de recargo PVP para seguros"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_config_pvp"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            if percentage < 0 or percentage > 100:
                embed = discord.Embed(
                    title="❌ Porcentaje Inválido",
                    description="El porcentaje debe estar entre 0 y 100",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Guardar configuración en la base de datos
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO server_config 
                    (guild_id, config_key, config_value, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    str(interaction.guild.id),
                    'pvp_insurance_markup',
                    str(percentage),
                    datetime.now().isoformat()
                ))
                await db.commit()
            
            embed = discord.Embed(
                title="✅ Configuración PVP Actualizada",
                description=f"Recargo PVP configurado a **{percentage}%**",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Ejemplo de Precios",
                value=f"• **Moto en PVE:** $500\\n• **Moto en PVP:** ${int(500 * (1 + percentage/100)):,.0f}\\n• **Ranger en PVE:** $1,200\\n• **Ranger en PVP:** ${int(1200 * (1 + percentage/100)):,.0f}",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Aplicación",
                value="• Los nuevos seguros usarán este porcentaje inmediatamente\\n• Los seguros existentes no se ven afectados\\n• El recargo solo aplica a zonas PVP seleccionadas por el usuario",
                inline=False
            )
            
            embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Recargo PVP configurado: {percentage}% en {interaction.guild.name} por {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error configurando recargo PVP: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error configurando el recargo PVP",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_set_price")
    @app_commands.command(name="mechanic_admin_set_price", description="[ADMIN] Establecer precio personalizado para un tipo de vehículo")
    @app_commands.describe(
        vehicle_type="Tipo de vehículo (ranger, laika, ww, avion, moto)",
        price="Precio del seguro en dólares del juego"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_vehicle_price_command(self, interaction: discord.Interaction, vehicle_type: str, price: int):
        """Establecer precio personalizado para un tipo de vehículo"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_set_price"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico o administrador
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            is_admin = interaction.user.guild_permissions.administrator
            
            if not (is_mechanic or is_admin):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden cambiar precios",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            if price <= 0:
                embed = discord.Embed(
                    title="❌ Precio Inválido",
                    description="El precio debe ser mayor a 0",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Validar tipo de vehículo
            valid_types = ['ranger', 'laika', 'ww', 'avion', 'moto', 'motocicleta', 'automovil', 'auto', 'car', 'truck', 'helicopter', 'helicoptero', 'airplane', 'plane']
            vehicle_type_clean = vehicle_type.lower()
            
            if vehicle_type_clean not in valid_types:
                embed = discord.Embed(
                    title="❌ Tipo de Vehículo Inválido",
                    description=f"Tipos válidos: {', '.join(valid_types[:5])}...",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Establecer precio personalizado
            success = await set_vehicle_price(
                str(interaction.guild.id),
                vehicle_type_clean,
                price,
                str(interaction.user.id)
            )
            
            if success:
                # Obtener precio anterior para comparación
                old_price = calculate_vehicle_insurance_cost(vehicle_type_clean)
                
                embed = discord.Embed(
                    title="✅ Precio Actualizado",
                    description=f"Precio personalizado establecido para **{vehicle_type_clean.title()}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="💰 Información de Precios",
                    value=f"**Precio Anterior:** ${old_price:,.0f}\n**Precio Nuevo:** ${price:,.0f}\n**Diferencia:** ${price - old_price:+,.0f}",
                    inline=True
                )
                
                # Calcular ejemplos con recargo PVP
                pvp_markup = await get_server_pvp_markup(interaction.guild.id)
                pvp_price = int(price * (1 + pvp_markup / 100))
                
                embed.add_field(
                    name="🗺️ Precios por Zona",
                    value=f"**PVE:** ${price:,.0f}\n**PVP:** ${pvp_price:,.0f} (+{pvp_markup}%)",
                    inline=True
                )
                
                embed.add_field(
                    name="⚙️ Aplicación",
                    value="• Los nuevos seguros usarán este precio inmediatamente\n• Los seguros existentes no se ven afectados\n• El precio se aplica solo a este servidor",
                    inline=False
                )
                
                embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"Precio de vehículo actualizado: {vehicle_type_clean} = ${price} en {interaction.guild.name} por {interaction.user.display_name}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error del Sistema",
                    description="No se pudo establecer el precio personalizado",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error estableciendo precio de vehículo: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error estableciendo el precio personalizado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_list_prices")
    @app_commands.command(name="mechanic_admin_list_prices", description="[ADMIN] Ver todos los precios personalizados")
    async def list_vehicle_prices(self, interaction: discord.Interaction):
        """Listar todos los precios personalizados de vehículos"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_list_prices"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico o administrador
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            is_admin = interaction.user.guild_permissions.administrator
            
            if not (is_mechanic or is_admin):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden ver precios",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener precios personalizados
            custom_prices = await get_all_vehicle_prices(str(interaction.guild.id))
            
            embed = discord.Embed(
                title="💰 Precios de Seguros Vehiculares",
                description=f"Configuración actual para **{interaction.guild.name}**",
                color=0xff8800
            )
            
            # Obtener recargo PVP
            pvp_markup = await get_server_pvp_markup(interaction.guild.id)
            
            embed.add_field(
                name="🗺️ Configuración PVP",
                value=f"Recargo en zonas PVP: **+{pvp_markup}%**",
                inline=False
            )
            
            if custom_prices:
                custom_text = ""
                for vehicle_type, price in custom_prices.items():
                    pvp_price = int(price * (1 + pvp_markup / 100))
                    custom_text += f"• **{vehicle_type.title()}:** ${price:,.0f} (PVP: ${pvp_price:,.0f})\n"
                
                embed.add_field(
                    name="🔧 Precios Personalizados",
                    value=custom_text,
                    inline=False
                )
            
            # Mostrar precios por defecto
            default_types = ['ranger', 'laika', 'ww', 'avion', 'moto']
            default_text = ""
            
            for vehicle_type in default_types:
                if vehicle_type not in custom_prices:
                    default_price = calculate_vehicle_insurance_cost(vehicle_type)
                    pvp_price = int(default_price * (1 + pvp_markup / 100))
                    default_text += f"• **{vehicle_type.title()}:** ${default_price:,.0f} (PVP: ${pvp_price:,.0f})\n"
            
            if default_text:
                embed.add_field(
                    name="📋 Precios por Defecto",
                    value=default_text,
                    inline=False
                )
            
            embed.add_field(
                name="🛠️ Comandos Útiles",
                value="• `/mechanic_admin_set_price` - Establecer precio personalizado\n• `/mechanic_admin_config_pvp` - Configurar recargo PVP",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listando precios de vehículos: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error obteniendo los precios de vehículos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_set_limit")
    @app_commands.command(name="mechanic_admin_set_limit", description="[ADMIN] Establecer límite de vehículos por miembro")
    @app_commands.describe(
        vehicle_type="Tipo de vehículo (moto, ranger, laika, ww, avion, etc.)",
        limit_per_member="Cantidad máxima por miembro (ej: 2 para permitir 2 motos por persona)"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_vehicle_limit_command(self, interaction: discord.Interaction, vehicle_type: str, limit_per_member: int):
        """Establecer límite de vehículos por miembro"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_set_limit"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico o administrador
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            is_admin = interaction.user.guild_permissions.administrator
            
            if not (is_mechanic or is_admin):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden cambiar límites",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            if limit_per_member < 0 or limit_per_member > 10:
                embed = discord.Embed(
                    title="❌ Límite Inválido",
                    description="El límite debe estar entre 0 y 10 vehículos por miembro",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Validar tipo de vehículo
            valid_types = ['moto', 'ranger', 'laika', 'ww', 'avion', 'barca']
            vehicle_type_clean = vehicle_type.lower()
            
            if vehicle_type_clean not in valid_types:
                embed = discord.Embed(
                    title="❌ Tipo de Vehículo Inválido",
                    description=f"Tipos válidos: {', '.join(valid_types)}",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Establecer límite
            success = await set_vehicle_limit(
                str(interaction.guild.id),
                vehicle_type_clean,
                limit_per_member,
                str(interaction.user.id)
            )
            
            if success:
                # Obtener límite anterior
                old_limits = await get_vehicle_limits(str(interaction.guild.id))
                old_limit = old_limits.get(vehicle_type_clean, 1)
                
                embed = discord.Embed(
                    title="✅ Límite Actualizado",
                    description=f"Límite establecido para **{vehicle_type_clean.title()}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📊 Información de Límites",
                    value=f"**Límite Anterior:** {old_limit} por miembro\n**Límite Nuevo:** {limit_per_member} por miembro\n**Diferencia:** {limit_per_member - old_limit:+}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Aplicación",
                    value="• Los nuevos registros usarán este límite inmediatamente\n• Los vehículos existentes no se ven afectados\n• El límite se aplica solo a este servidor",
                    inline=True
                )
                
                # Mostrar ejemplos
                if limit_per_member == 0:
                    embed.add_field(
                        name="⚠️ Límite Cero",
                        value=f"Los usuarios **NO** podrán registrar nuevos vehículos de tipo **{vehicle_type_clean.title()}**",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="💡 Ejemplo",
                        value=f"Cada miembro podrá tener hasta **{limit_per_member}** vehículos de tipo **{vehicle_type_clean.title()}**",
                        inline=False
                    )
                
                embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"Límite de vehículo actualizado: {vehicle_type_clean} = {limit_per_member} en {interaction.guild.name} por {interaction.user.display_name}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error del Sistema",
                    description="No se pudo establecer el límite de vehículos",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error estableciendo límite de vehículos: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error estableciendo el límite de vehículos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @rate_limit("mechanic_admin_list_limits")
    @app_commands.command(name="mechanic_admin_list_limits", description="[ADMIN] Ver todos los límites de vehículos")
    async def list_vehicle_limits(self, interaction: discord.Interaction):
        """Listar todos los límites de vehículos configurados"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "mechanic_admin_list_limits"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si es mecánico o administrador
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            is_admin = interaction.user.guild_permissions.administrator
            
            if not (is_mechanic or is_admin):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo mecánicos registrados o administradores pueden ver límites",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener límites configurados
            limits = await get_vehicle_limits(str(interaction.guild.id))
            
            embed = discord.Embed(
                title="📊 Límites de Vehículos por Miembro",
                description=f"Configuración actual para **{interaction.guild.name}**",
                color=0xff8800
            )
            
            # Agrupar por categorías
            terrestrial = ['moto', 'ranger', 'laika', 'ww']
            aerial = ['avion']
            naval = ['barca']
            
            terrestrial_text = ""
            for vehicle_type in terrestrial:
                limit = limits.get(vehicle_type, 1)
                terrestrial_text += f"• **{vehicle_type.title()}:** {limit} por miembro\n"
            
            aerial_text = ""
            for vehicle_type in aerial:
                limit = limits.get(vehicle_type, 1)
                aerial_text += f"• **{vehicle_type.title()}:** {limit} por miembro\n"
            
            naval_text = ""
            for vehicle_type in naval:
                limit = limits.get(vehicle_type, 1)
                naval_text += f"• **{vehicle_type.title()}:** {limit} por miembro\n"
            
            embed.add_field(
                name="🚗 Vehículos Terrestres",
                value=terrestrial_text,
                inline=True
            )
            
            embed.add_field(
                name="✈️ Vehículos Aéreos",
                value=aerial_text,
                inline=True
            )
            
            embed.add_field(
                name="🚢 Vehículos Navales",
                value=naval_text,
                inline=True
            )
            
            # Obtener estadísticas de uso actual
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT vehicle_type, COUNT(*) as count 
                    FROM registered_vehicles 
                    WHERE guild_id = ? AND status = 'active'
                    GROUP BY vehicle_type
                """, (str(interaction.guild.id),))
                
                usage_stats = await cursor.fetchall()
                
                if usage_stats:
                    stats_text = ""
                    for vehicle_type, count in usage_stats:
                        stats_text += f"• **{vehicle_type.title()}:** {count} registrados\n"
                    
                    embed.add_field(
                        name="📈 Uso Actual",
                        value=stats_text,
                        inline=False
                    )
            
            embed.add_field(
                name="🛠️ Comandos Útiles",
                value="• `/mechanic_admin_set_limit` - Cambiar límite específico\n• `/mechanic_admin_list_limits` - Ver límites configurados\n• `/mechanic_admin_list_prices` - Ver precios de seguros",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listando límites de vehículos: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error obteniendo los límites de vehículos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @rate_limit("squadron_admin_config_limits")
    @app_commands.command(name="squadron_admin_config_limits", description="[ADMIN] Configurar límites globales de vehículos por escuadrón")
    @app_commands.describe(
        vehicles_per_member="Vehículos permitidos por miembro del escuadrón (default: 2)",
        max_total_vehicles="Límite máximo total de vehículos por escuadrón (default: 50)"
    )
    async def squadron_admin_config_limits(self, interaction: discord.Interaction, vehicles_per_member: int, max_total_vehicles: int):
        """Configurar límites globales de vehículos por escuadrón"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "squadron_admin_config_limits"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos de administrador
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden configurar límites de escuadrones",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Validar valores
            if vehicles_per_member < 1 or vehicles_per_member > 10:
                await interaction.followup.send("❌ Vehículos por miembro debe estar entre 1 y 10", ephemeral=True)
                return
                
            if max_total_vehicles < 5 or max_total_vehicles > 200:
                await interaction.followup.send("❌ Límite máximo debe estar entre 5 y 200", ephemeral=True)
                return
            
            # Actualizar configuración
            success = await update_squadron_vehicle_config(
                str(interaction.guild.id), 
                vehicles_per_member, 
                max_total_vehicles, 
                str(interaction.user.id)
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Configuración Actualizada",
                    description="Los límites de vehículos por escuadrón han sido configurados",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="⚙️ Nueva Configuración",
                    value=f"• **Vehículos por miembro:** {vehicles_per_member}\n• **Límite máximo total:** {max_total_vehicles}",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Ejemplos de Límites",
                    value=f"• Escuadrón de 1 miembro: {vehicles_per_member} vehículos\n• Escuadrón de 5 miembros: {min(vehicles_per_member * 5, max_total_vehicles)} vehículos\n• Escuadrón de 10 miembros: {min(vehicles_per_member * 10, max_total_vehicles)} vehículos",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Cómo Funciona",
                    value="El sistema usa la fórmula: `min(miembros × vehículos_por_miembro, límite_máximo)`\nEsto evita escuadrones con demasiados vehículos.",
                    inline=False
                )
                
                embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Error al actualizar la configuración", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error configurando límites de escuadrón: {e}")
            await interaction.followup.send("❌ Error interno del sistema", ephemeral=True)

    @rate_limit("squadron_admin_view_config")
    @app_commands.command(name="squadron_admin_view_config", description="[ADMIN] Ver configuración actual de límites de escuadrones")
    async def squadron_admin_view_config(self, interaction: discord.Interaction):
        """Ver configuración actual de límites de escuadrones"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "squadron_admin_view_config"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos
            is_admin = interaction.user.guild_permissions.administrator
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            
            if not (is_admin or is_mechanic):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores o mecánicos pueden ver esta configuración",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener configuración actual
            config = await get_squadron_vehicle_config(str(interaction.guild.id))
            vehicles_per_member = config['vehicles_per_member']
            max_total_vehicles = config['max_total_vehicles']
            
            embed = discord.Embed(
                title="⚙️ Configuración de Límites de Escuadrones",
                description=f"Configuración actual para **{interaction.guild.name}**",
                color=0xff8800
            )
            
            embed.add_field(
                name="🎯 Límites Configurados",
                value=f"• **Vehículos por miembro:** {vehicles_per_member}\n• **Límite máximo total:** {max_total_vehicles}",
                inline=False
            )
            
            # Obtener estadísticas de escuadrones actuales
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT s.squadron_name, COUNT(sm.id) as members,
                           COUNT(rv.id) as vehicles
                    FROM squadrons s
                    LEFT JOIN squadron_members sm ON s.id = sm.squadron_id AND sm.status = 'active'
                    LEFT JOIN registered_vehicles rv ON sm.discord_id = rv.owner_discord_id 
                        AND rv.guild_id = s.guild_id AND rv.status = 'active'
                    WHERE s.guild_id = ? AND s.status = 'active'
                    GROUP BY s.id, s.squadron_name
                    ORDER BY vehicles DESC
                """, (str(interaction.guild.id),))
                
                squadron_stats = await cursor.fetchall()
                
                if squadron_stats:
                    stats_text = ""
                    for squadron_name, members, vehicles in squadron_stats[:5]:  # Top 5
                        calculated_limit = min(vehicles_per_member * members, max_total_vehicles)
                        usage_percent = (vehicles / calculated_limit * 100) if calculated_limit > 0 else 0
                        stats_text += f"• **{squadron_name}:** {vehicles}/{calculated_limit} vehículos ({usage_percent:.0f}%)\n"
                    
                    embed.add_field(
                        name="📊 Estado Actual de Escuadrones",
                        value=stats_text,
                        inline=False
                    )
            
            embed.add_field(
                name="📋 Ejemplos de Límites",
                value=f"• 1 miembro: {vehicles_per_member} vehículos\n• 3 miembros: {min(vehicles_per_member * 3, max_total_vehicles)} vehículos\n• 5 miembros: {min(vehicles_per_member * 5, max_total_vehicles)} vehículos\n• 10 miembros: {min(vehicles_per_member * 10, max_total_vehicles)} vehículos",
                inline=False
            )
            
            embed.add_field(
                name="🛠️ Comandos Útiles",
                value="• `/squadron_admin_config_limits` - Cambiar configuración\n• `/squadron_admin_view_config` - Ver configuración actual",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error consultando configuración de escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando la configuración",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @rate_limit("squadron_admin_remove_member")
    @app_commands.command(name="squadron_admin_remove_member", description="[ADMIN] Remover un miembro de su escuadrón")
    @app_commands.describe(
        user="Usuario a remover del escuadrón",
        reason="Razón de la remoción (opcional)"
    )
    async def squadron_admin_remove_member(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Removido por administrador"):
        """Comando admin para remover un miembro de su escuadrón"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "squadron_admin_remove_member"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos de administrador
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden remover miembros de escuadrones",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Verificar si el usuario está en un escuadrón
            user_squadron = await get_user_squadron(str(user.id), str(interaction.guild.id))
            
            if not user_squadron:
                embed = discord.Embed(
                    title="❌ Usuario Sin Escuadrón",
                    description=f"**{user.display_name}** no pertenece a ningún escuadrón",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Ejecutar remoción (sin restricciones de tiempo para admins)
            success = await leave_squadron(
                str(user.id), 
                str(interaction.guild.id), 
                reason='admin_removed', 
                removed_by=str(interaction.user.id)
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Miembro Removido",
                    description=f"**{user.display_name}** ha sido removido del escuadrón **{user_squadron['squadron_name']}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📋 Detalles de la Remoción",
                    value=f"• **Usuario:** {user.display_name} ({user.mention})\n• **Escuadrón:** {user_squadron['squadron_name']}\n• **Razón:** {reason}\n• **Removido por:** {interaction.user.display_name}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 Efectos",
                    value="• **Sin período de enfriamiento** - Puede unirse inmediatamente a otro escuadrón\n• Pierde acceso a beneficios del escuadrón anterior\n• Puede crear un nuevo escuadrón sin restricciones",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Notificar al usuario removido (opcional)
                try:
                    dm_embed = discord.Embed(
                        title="📢 Has Sido Removido de tu Escuadrón",
                        description=f"Has sido removido del escuadrón **{user_squadron['squadron_name']}** en **{interaction.guild.name}**",
                        color=discord.Color.orange()
                    )
                    
                    dm_embed.add_field(
                        name="📋 Información",
                        value=f"• **Razón:** {reason}\n• **Removido por:** Administrador\n• **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        inline=False
                    )
                    
                    dm_embed.add_field(
                        name="🎯 Puedes:",
                        value="• Unirte a otro escuadrón inmediatamente\n• Crear tu propio escuadrón\n• Contactar administradores si tienes dudas",
                        inline=False
                    )
                    
                    await user.send(embed=dm_embed)
                    
                except discord.Forbidden:
                    logger.info(f"No se pudo enviar DM a {user.id} (DMs cerrados)")
                    
            else:
                embed = discord.Embed(
                    title="❌ Error en la Remoción",
                    description="No se pudo remover al usuario del escuadrón",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error removiendo miembro de escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error procesando la remoción",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @rate_limit("squadron_admin_view_member")
    @app_commands.command(name="squadron_admin_view_member", description="[ADMIN] Ver información detallada de un miembro de escuadrón")
    @app_commands.describe(user="Usuario a consultar")
    async def squadron_admin_view_member(self, interaction: discord.Interaction, user: discord.Member):
        """Ver información detallada de un miembro de escuadrón"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "squadron_admin_view_member"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos
            is_admin = interaction.user.guild_permissions.administrator
            is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            
            if not (is_admin or is_mechanic):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores o mecánicos pueden ver información de miembros",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Obtener información del escuadrón
            user_squadron = await get_user_squadron(str(user.id), str(interaction.guild.id))
            
            embed = discord.Embed(
                title=f"👤 Información de {user.display_name}",
                description="Detalles del usuario en el sistema de escuadrones",
                color=0x3498db
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            if user_squadron:
                embed.add_field(
                    name="🏆 Escuadrón Actual",
                    value=f"• **Nombre:** {user_squadron['squadron_name']}\n• **Tipo:** {user_squadron['squadron_type']}\n• **Rol:** {user_squadron['role'].title()}\n• **Fecha de unión:** {user_squadron['joined_at'][:10]}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🏆 Escuadrón Actual",
                    value="❌ No pertenece a ningún escuadrón",
                    inline=False
                )
            
            # Verificar historial de salidas
            can_leave, time_remaining, last_squadron = await can_leave_squadron(str(user.id), str(interaction.guild.id))
            
            if can_leave:
                cooldown_status = "✅ Sin restricciones"
            else:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                cooldown_status = f"⏰ {hours}h {minutes}m restantes"
            
            embed.add_field(
                name="⏰ Estado de Enfriamiento",
                value=cooldown_status,
                inline=True
            )
            
            # Obtener historial de salidas (últimas 3)
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT squadron_name, left_at, reason 
                    FROM squadron_leave_history 
                    WHERE discord_id = ? AND guild_id = ? 
                    ORDER BY left_at DESC 
                    LIMIT 3
                """, (str(user.id), str(interaction.guild.id)))
                
                history = await cursor.fetchall()
            
            if history:
                history_text = ""
                for squadron_name, left_at, reason in history:
                    date = left_at[:10]
                    reason_emoji = "👤" if reason == 'voluntary' else "👮" if reason == 'admin_removed' else "⚠️"
                    history_text += f"• {reason_emoji} **{squadron_name}** - {date}\n"
                
                embed.add_field(
                    name="📋 Historial Reciente",
                    value=history_text,
                    inline=False
                )
            
            # Obtener vehículos registrados
            user_vehicles = await get_user_vehicles(str(user.id), str(interaction.guild.id))
            
            embed.add_field(
                name="🚗 Vehículos Registrados",
                value=f"**{len(user_vehicles)}** vehículo(s) registrado(s)",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Acciones Disponibles",
                value="• `/squadron_admin_remove_member` - Remover del escuadrón\n• Sin restricciones de tiempo para admins",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error consultando información de miembro: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando la información",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @rate_limit("squadron_admin_cleanup")
    @app_commands.command(name="squadron_admin_cleanup", description="[ADMIN] Limpiar mensajes del bot en canales de escuadrones y mecánico")
    @app_commands.describe(
        channel_type="Tipo de canal a limpiar (ambos por defecto)",
        limit="Número máximo de mensajes a revisar (default: 50)"
    )
    async def squadron_admin_cleanup(self, interaction: discord.Interaction, 
                                   channel_type: typing.Literal["squadron", "mechanic", "both"] = "both",
                                   limit: int = 50):
        """Limpiar mensajes del bot en canales del sistema"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "squadron_admin_cleanup"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden ejecutar la limpieza manual",
                    color=discord.Color.red()
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Validar límite
            if limit < 10 or limit > 100:
                await interaction.followup.send("❌ El límite debe estar entre 10 y 100 mensajes", ephemeral=True)
                return
            
            total_deleted = 0
            cleaned_channels = []
            
            # Limpiar canales según el tipo especificado
            if channel_type in ["squadron", "both"]:
                if interaction.guild.id in self.squadron_channels:
                    channel_id = self.squadron_channels[interaction.guild.id]
                    deleted = await self._manual_cleanup_channel(channel_id, "escuadrones", limit)
                    if deleted > 0:
                        total_deleted += deleted
                        cleaned_channels.append(f"🏆 Escuadrones: {deleted} mensajes")
            
            if channel_type in ["mechanic", "both"]:
                if interaction.guild.id in self.mechanic_channels:
                    channel_id = self.mechanic_channels[interaction.guild.id]
                    deleted = await self._manual_cleanup_channel(channel_id, "mecánico", limit)
                    if deleted > 0:
                        total_deleted += deleted
                        cleaned_channels.append(f"🔧 Mecánico: {deleted} mensajes")
            
            # Crear embed de resultado
            if total_deleted > 0:
                embed = discord.Embed(
                    title="✅ Limpieza Completada",
                    description=f"Se han eliminado **{total_deleted} mensajes** del bot exitosamente",
                    color=discord.Color.green()
                )
                
                if cleaned_channels:
                    embed.add_field(
                        name="📊 Canales Limpiados",
                        value="\n".join(cleaned_channels),
                        inline=False
                    )
                
                embed.add_field(
                    name="⚙️ Configuración",
                    value=f"• **Tipo de canal:** {channel_type}\n• **Mensajes revisados:** {limit}",
                    inline=True
                )
                
                embed.add_field(
                    name="🕒 Próxima Limpieza Automática",
                    value="Cada 30 minutos el bot limpia automáticamente mensajes antiguos",
                    inline=True
                )
                
            else:
                embed = discord.Embed(
                    title="💡 Sin Cambios",
                    description="No se encontraron mensajes del bot para eliminar",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="ℹ️ Información",
                    value="Esto puede significar que:\n• Los canales ya están limpios\n• No hay mensajes del bot en el rango especificado\n• Los canales no están configurados",
                    inline=False
                )
            
            embed.set_footer(text=f"Limpieza ejecutada por {interaction.user.display_name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en limpieza manual: {e}")
            embed = discord.Embed(
                title="❌ Error en Limpieza",
                description="Hubo un error durante el proceso de limpieza",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _manual_cleanup_channel(self, channel_id: int, channel_type: str, limit: int) -> int:
        """Limpiar mensajes del bot en un canal específico manualmente"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal {channel_id} no encontrado para limpieza manual")
                return 0
            
            # Verificar permisos
            if not channel.permissions_for(channel.guild.me).manage_messages:
                logger.warning(f"Sin permisos para gestionar mensajes en canal {channel_id}")
                return 0
                
            deleted_count = 0
            
            async for message in channel.history(limit=limit):
                if message.author == self.bot.user:
                    # Eliminar todos los mensajes del bot (no solo los antiguos)
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.3)  # Rate limit
                    except discord.NotFound:
                        # El mensaje ya fue eliminado
                        pass
                    except discord.Forbidden:
                        # Sin permisos para eliminar este mensaje específico
                        logger.warning(f"Sin permisos para eliminar mensaje {message.id}")
                        break
            
            if deleted_count > 0:
                logger.info(f"Limpieza manual: Eliminados {deleted_count} mensajes en canal de {channel_type}")
            
            return deleted_count
                
        except Exception as e:
            logger.error(f"Error en limpieza manual de canal {channel_type}: {e}")
            return 0

# === FUNCIONES AUXILIARES PARA VEHÍCULOS ===

async def register_vehicle(vehicle_id: str, vehicle_type: str, owner_discord_id: str, 
                          owner_ingame_name: str, guild_id: str, squadron_id: int = None, notes: str = None) -> bool:
    """Registrar un vehículo"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            await db.execute("""
                INSERT INTO registered_vehicles 
                (vehicle_id, vehicle_type, owner_discord_id, owner_ingame_name, squadron_id, guild_id, registered_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (vehicle_id, vehicle_type, owner_discord_id, owner_ingame_name, squadron_id, guild_id, 
                  datetime.now().isoformat(), notes))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error registrando vehículo: {e}")
        return False

async def get_user_vehicles(discord_id: str, guild_id: str) -> list:
    """Obtener vehículos registrados por un usuario"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar si la tabla existe
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='registered_vehicles'
            """)
            table_exists = await cursor.fetchone()
            
            if not table_exists:
                logger.warning("La tabla 'registered_vehicles' no existe")
                return []
            
            # Verificar el total de registros en la tabla
            cursor = await db.execute("SELECT COUNT(*) FROM registered_vehicles")
            total_count = (await cursor.fetchone())[0]
            logger.info(f"Total de vehículos en la tabla: {total_count}")
            
            # Consultar vehículos del usuario
            cursor = await db.execute("""
                SELECT * FROM registered_vehicles 
                WHERE owner_discord_id = ? AND guild_id = ? AND status = 'active'
                ORDER BY registered_at DESC
            """, (discord_id, guild_id))
            
            results = await cursor.fetchall()
            logger.info(f"Consultando vehículos para discord_id={discord_id}, guild_id={guild_id}, encontrados: {len(results)}")
            
            return results
    except Exception as e:
        logger.error(f"Error obteniendo vehículos del usuario: {e}")
        return []

async def unregister_vehicle(vehicle_id: str, guild_id: str) -> bool:
    """Dar de baja un vehículo (y eliminar su seguro si existe)"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Eliminar seguro si existe
            await db.execute("""
                UPDATE vehicle_insurance 
                SET status = 'cancelled' 
                WHERE vehicle_id = ? AND guild_id = ?
            """, (vehicle_id, guild_id))
            
            # Dar de baja el vehículo
            await db.execute("""
                UPDATE registered_vehicles 
                SET status = 'inactive' 
                WHERE vehicle_id = ? AND guild_id = ?
            """, (vehicle_id, guild_id))
            
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error dando de baja vehículo: {e}")
        return False

async def get_vehicle_limits(guild_id: str) -> dict:
    """Obtener límites de vehículos por tipo"""
    default_limits = {
        'moto': 2,
        'ranger': 1,
        'laika': 1,
        'ww': 1,
        'avion': 1,
        'barca': 1
    }
    
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT vehicle_type, limit_per_member FROM squadron_vehicle_limits 
                WHERE guild_id = ?
            """, (guild_id,))
            
            custom_limits = {}
            rows = await cursor.fetchall()
            for row in rows:
                custom_limits[row[0]] = row[1]
            
            # Combinar límites por defecto con personalizados
            for vehicle_type, default_limit in default_limits.items():
                if vehicle_type not in custom_limits:
                    custom_limits[vehicle_type] = default_limit
                    
            return custom_limits
    except Exception as e:
        logger.error(f"Error obteniendo límites de vehículos: {e}")
        return default_limits

async def set_vehicle_limit(guild_id: str, vehicle_type: str, limit_per_member: int, updated_by: str) -> bool:
    """Establecer límite de vehículos por miembro"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO squadron_vehicle_limits 
                (guild_id, vehicle_type, limit_per_member, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, vehicle_type, limit_per_member, updated_by, datetime.now().isoformat()))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error estableciendo límite de vehículos: {e}")
        return False

async def check_vehicle_limit(discord_id: str, guild_id: str, vehicle_type: str) -> tuple:
    """Verificar si el usuario puede registrar más vehículos basado en límites generales del escuadrón"""
    try:
        # Verificar si el usuario pertenece a un escuadrón
        user_squadron = await get_user_squadron(discord_id, guild_id)
        
        if user_squadron:
            squadron_id = user_squadron['id']
            
            # Obtener configuración de límites del escuadrón
            squadron_config = await get_squadron_vehicle_config(guild_id)
            vehicles_per_member = squadron_config.get('vehicles_per_member', 2)  # Default: 2 por miembro
            max_total_vehicles = squadron_config.get('max_total_vehicles', 50)  # Default: límite máximo de 50
            
            async with aiosqlite.connect(taxi_db.db_path) as db:
                # Contar miembros activos del escuadrón
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM squadron_members 
                    WHERE squadron_id = ? AND status = 'active'
                """, (squadron_id,))
                active_members = (await cursor.fetchone())[0]
                
                # Calcular límite total del escuadrón (el menor entre los dos límites)
                squadron_member_limit = vehicles_per_member * active_members
                squadron_total_limit = min(squadron_member_limit, max_total_vehicles)
                
                # Contar TODOS los vehículos actuales del escuadrón (cualquier tipo)
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM registered_vehicles rv
                    JOIN squadron_members sm ON rv.owner_discord_id = sm.discord_id
                    WHERE sm.squadron_id = ? AND rv.guild_id = ? 
                    AND rv.status = 'active' AND sm.status = 'active'
                """, (squadron_id, guild_id))
                squadron_current_count = (await cursor.fetchone())[0]
                
                # Verificar si el escuadrón puede registrar más vehículos
                can_register = squadron_current_count < squadron_total_limit
                
                logger.info(f"Límite de escuadrón - Miembros: {active_members}, "
                           f"Límite calculado: {squadron_member_limit}, "
                           f"Límite máximo: {max_total_vehicles}, "
                           f"Límite efectivo: {squadron_total_limit}, "
                           f"Actual: {squadron_current_count}")
                
                return can_register, squadron_current_count, squadron_total_limit
        else:
            # Usuario sin escuadrón - límite individual más restrictivo
            individual_limit = 2  # Solo 2 vehículos total sin escuadrón
            
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM registered_vehicles 
                    WHERE owner_discord_id = ? AND guild_id = ? AND status = 'active'
                """, (discord_id, guild_id))
                current_count = (await cursor.fetchone())[0]
                
            can_register = current_count < individual_limit
            
            logger.info(f"Límite individual - Usuario sin escuadrón: "
                       f"Límite: {individual_limit}, Actual: {current_count}")
            
            return can_register, current_count, individual_limit
        
    except Exception as e:
        logger.error(f"Error verificando límite de vehículos: {e}")
        return False, 0, 1

async def get_squadron_vehicle_config(guild_id: str) -> dict:
    """Obtener configuración de límites de vehículos para escuadrones"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT vehicles_per_member, max_total_vehicles 
                FROM squadron_vehicle_config 
                WHERE guild_id = ?
            """, (guild_id,))
            
            config = await cursor.fetchone()
            if config:
                return {
                    'vehicles_per_member': config[0],
                    'max_total_vehicles': config[1]
                }
            else:
                # Configuración por defecto si no existe
                return {
                    'vehicles_per_member': 2,  # 2 vehículos por miembro
                    'max_total_vehicles': 50   # Máximo 50 vehículos por escuadrón
                }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de escuadrones: {e}")
        return {
            'vehicles_per_member': 2,
            'max_total_vehicles': 50
        }

async def update_squadron_vehicle_config(guild_id: str, vehicles_per_member: int = None, max_total_vehicles: int = None) -> bool:
    """Actualizar configuración de límites de vehículos para escuadrones"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar si existe configuración
            cursor = await db.execute("""
                SELECT id FROM squadron_vehicle_config WHERE guild_id = ?
            """, (guild_id,))
            
            exists = await cursor.fetchone()
            
            if exists:
                # Actualizar configuración existente
                updates = []
                params = []
                
                if vehicles_per_member is not None:
                    updates.append("vehicles_per_member = ?")
                    params.append(vehicles_per_member)
                
                if max_total_vehicles is not None:
                    updates.append("max_total_vehicles = ?")
                    params.append(max_total_vehicles)
                
                if updates:
                    params.append(guild_id)
                    await db.execute(f"""
                        UPDATE squadron_vehicle_config 
                        SET {', '.join(updates)}
                        WHERE guild_id = ?
                    """, params)
            else:
                # Crear nueva configuración
                vpm = vehicles_per_member if vehicles_per_member is not None else 2
                mtv = max_total_vehicles if max_total_vehicles is not None else 50
                
                await db.execute("""
                    INSERT INTO squadron_vehicle_config 
                    (guild_id, vehicles_per_member, max_total_vehicles, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (guild_id, vpm, mtv, datetime.now().isoformat()))
            
            await db.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error actualizando configuración de escuadrones: {e}")
        return False

# === FUNCIONES AUXILIARES PARA ESCUADRONES ===

async def create_squadron(guild_id: str, squadron_name: str, squadron_type: str, 
                         leader_discord_id: str, leader_ingame_name: str) -> int:
    """Crear un nuevo escuadrón"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO squadrons 
                (guild_id, squadron_name, squadron_type, leader_discord_id, leader_ingame_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, squadron_name, squadron_type, leader_discord_id, leader_ingame_name, datetime.now().isoformat()))
            
            squadron_id = cursor.lastrowid
            
            # Agregar el líder como miembro
            await db.execute("""
                INSERT INTO squadron_members 
                (squadron_id, discord_id, ingame_name, joined_at, role)
                VALUES (?, ?, ?, ?, 'leader')
            """, (squadron_id, leader_discord_id, leader_ingame_name, datetime.now().isoformat()))
            
            await db.commit()
            return squadron_id
    except Exception as e:
        logger.error(f"Error creando escuadrón: {e}")
        return None

async def join_squadron(squadron_id: int, discord_id: str, ingame_name: str) -> bool:
    """Unirse a un escuadrón existente"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar que el escuadrón existe y está activo
            cursor = await db.execute("""
                SELECT id, squadron_name, max_members,
                       (SELECT COUNT(*) FROM squadron_members 
                        WHERE squadron_id = ? AND status = 'active') as current_members
                FROM squadrons 
                WHERE id = ? AND status = 'active'
            """, (squadron_id, squadron_id))
            
            squadron_info = await cursor.fetchone()
            if not squadron_info:
                logger.warning(f"Intento de unirse a escuadrón inexistente: {squadron_id}")
                return False
            
            current_members = squadron_info[3]
            max_members = squadron_info[2]
            
            # Verificar que no esté lleno
            if current_members >= max_members:
                logger.warning(f"Intento de unirse a escuadrón lleno: {squadron_id}")
                return False
            
            # Verificar que el usuario no esté ya en el escuadrón
            cursor = await db.execute("""
                SELECT id FROM squadron_members 
                WHERE squadron_id = ? AND discord_id = ? AND status = 'active'
            """, (squadron_id, discord_id))
            
            if await cursor.fetchone():
                logger.warning(f"Usuario {discord_id} ya está en el escuadrón {squadron_id}")
                return False
            
            # Agregar el usuario al escuadrón
            await db.execute("""
                INSERT INTO squadron_members 
                (squadron_id, discord_id, ingame_name, joined_at, role, status)
                VALUES (?, ?, ?, ?, 'member', 'active')
            """, (squadron_id, discord_id, ingame_name, datetime.now().isoformat()))
            
            await db.commit()
            logger.info(f"Usuario {ingame_name} ({discord_id}) se unió al escuadrón {squadron_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error uniendo usuario al escuadrón: {e}")
        return False

async def get_user_squadron(discord_id: str, guild_id: str) -> dict:
    """Obtener escuadrón del usuario"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT s.*, sm.role FROM squadrons s
                JOIN squadron_members sm ON s.id = sm.squadron_id
                WHERE sm.discord_id = ? AND s.guild_id = ? AND sm.status = 'active' AND s.status = 'active'
            """, (discord_id, guild_id))
            
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        logger.error(f"Error obteniendo escuadrón del usuario: {e}")
        return None

async def get_users_without_squadron(guild_id: str) -> list:
    """Obtener usuarios registrados sin escuadrón"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT discord_id, ingame_name FROM users 
                WHERE guild_id = ? AND ingame_name IS NOT NULL 
                AND discord_id NOT IN (
                    SELECT sm.discord_id FROM squadron_members sm 
                    JOIN squadrons s ON sm.squadron_id = s.id 
                    WHERE s.guild_id = ? AND sm.status = 'active' AND s.status = 'active'
                )
            """, (guild_id, guild_id))
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo usuarios sin escuadrón: {e}")
        return []

async def can_leave_squadron(discord_id: str, guild_id: str) -> tuple:
    """Verificar si un usuario puede salir del escuadrón (24h enfriamiento)"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar si la tabla existe
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='squadron_leave_history'
            """)
            table_exists = await cursor.fetchone()
            
            if not table_exists:
                logger.info("Tabla squadron_leave_history no existe, permitiendo salida")
                return True, None, None  # Si no hay tabla de historial, permitir salida
            
            # Buscar la última salida del usuario en cualquier escuadrón del servidor
            cursor = await db.execute("""
                SELECT left_at, can_rejoin_at, squadron_name 
                FROM squadron_leave_history 
                WHERE discord_id = ? AND guild_id = ? 
                ORDER BY left_at DESC 
                LIMIT 1
            """, (discord_id, guild_id))
            
            last_leave = await cursor.fetchone()
            
            if not last_leave:
                return True, None, None  # Primera vez, puede salir
            
            left_at, can_rejoin_at, last_squadron = last_leave
            can_rejoin_timestamp = datetime.fromisoformat(can_rejoin_at)
            now = datetime.now()
            
            if now >= can_rejoin_timestamp:
                return True, None, None  # Período de enfriamiento terminado
            else:
                time_remaining = can_rejoin_timestamp - now
                return False, time_remaining, last_squadron
                
    except Exception as e:
        logger.error(f"Error verificando enfriamiento de salida: {e}")
        return True, None, None  # En caso de error, permitir salida

async def leave_squadron(discord_id: str, guild_id: str, reason: str = 'voluntary', removed_by: str = None) -> bool:
    """Hacer que un usuario salga del escuadrón y registrar el historial"""
    try:
        logger.info(f"Iniciando proceso de salida de escuadrón para usuario {discord_id}, razón: {reason}")
        
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar que las tablas existen
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('squadron_members', 'squadrons', 'squadron_leave_history')
            """)
            existing_tables = [row[0] for row in await cursor.fetchall()]
            logger.info(f"Tablas encontradas: {existing_tables}")
            
            if 'squadron_members' not in existing_tables or 'squadrons' not in existing_tables:
                logger.error("Tablas requeridas no existen")
                return False
            
            # Obtener información del escuadrón actual
            cursor = await db.execute("""
                SELECT s.id, s.squadron_name, sm.role 
                FROM squadron_members sm
                JOIN squadrons s ON sm.squadron_id = s.id
                WHERE sm.discord_id = ? AND s.guild_id = ? AND sm.status = 'active'
            """, (discord_id, guild_id))
            
            squadron_info = await cursor.fetchone()
            logger.info(f"Información del escuadrón obtenida: {squadron_info}")
            
            if not squadron_info:
                logger.warning(f"Usuario {discord_id} no está en ningún escuadrón activo")
                return False  # Usuario no está en ningún escuadrón
                
            squadron_id, squadron_name, role = squadron_info
            
            # Verificar si es el líder (los líderes no pueden salir a menos que sean removidos por admin)
            if role == 'leader' and reason == 'voluntary':
                logger.warning(f"Líder {discord_id} intentó salir voluntariamente del escuadrón {squadron_name}")
                return False  # Los líderes no pueden salir voluntariamente
            
            # Marcar como inactivo en squadron_members
            await db.execute("""
                UPDATE squadron_members 
                SET status = 'left'
                WHERE discord_id = ? AND squadron_id = ?
            """, (discord_id, squadron_id))
            logger.info(f"Marcado como 'left' en squadron_members")
            
            # Registrar en historial solo si la tabla existe
            if 'squadron_leave_history' in existing_tables:
                left_at = datetime.now().isoformat()
                
                # Calcular cuándo puede volver a unirse
                if reason == 'admin_removed':
                    # Admin removió: puede unirse inmediatamente
                    can_rejoin_at = left_at
                else:
                    # Salida voluntaria: 24 horas de enfriamiento
                    can_rejoin_timestamp = datetime.now() + timedelta(hours=24)
                    can_rejoin_at = can_rejoin_timestamp.isoformat()
                
                try:
                    await db.execute("""
                        INSERT INTO squadron_leave_history 
                        (discord_id, guild_id, squadron_id, squadron_name, left_at, reason, removed_by, can_rejoin_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (discord_id, guild_id, squadron_id, squadron_name, left_at, reason, removed_by, can_rejoin_at))
                    logger.info(f"Historial de salida registrado")
                except Exception as history_error:
                    logger.warning(f"Error registrando historial (no crítico): {history_error}")
                    # No hacer que la función falle por esto
            else:
                logger.warning("Tabla squadron_leave_history no existe, omitiendo historial")
            
            await db.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Error al salir del escuadrón: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return False

async def get_squadron_vehicle_config(guild_id: str) -> dict:
    """Obtener configuración de vehículos por escuadrón"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            cursor = await db.execute("""
                SELECT vehicles_per_member, max_total_vehicles 
                FROM squadron_vehicle_config 
                WHERE guild_id = ?
            """, (guild_id,))
            result = await cursor.fetchone()
            
            if result:
                return {
                    'vehicles_per_member': result[0],
                    'max_total_vehicles': result[1]
                }
            else:
                # Configuración por defecto si no existe
                return {
                    'vehicles_per_member': 2,
                    'max_total_vehicles': 50
                }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de vehículos: {e}")
        return {'vehicles_per_member': 2, 'max_total_vehicles': 50}

async def update_squadron_vehicle_config(guild_id: str, vehicles_per_member: int, max_total_vehicles: int, updated_by: str) -> bool:
    """Actualizar configuración de vehículos por escuadrón"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO squadron_vehicle_config 
                (guild_id, vehicles_per_member, max_total_vehicles, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, vehicles_per_member, max_total_vehicles, updated_by, datetime.now().isoformat()))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error actualizando configuración de vehículos: {e}")
        return False


class SquadronLeaderManagementView(discord.ui.View):
    """Vista de gestión para líderes de escuadrón"""
    
    def __init__(self, squadron_data: dict):
        super().__init__(timeout=300)
        self.squadron_data = squadron_data
    
    @discord.ui.button(label="👑 Transferir Liderazgo", style=discord.ButtonStyle.primary, emoji="👑")
    async def transfer_leadership(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Transferir liderazgo a otro miembro del escuadrón"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener miembros del escuadrón (excepto el líder actual)
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT sm.discord_id, sm.ingame_name, sm.role
                    FROM squadron_members sm
                    WHERE sm.squadron_id = ? 
                    AND sm.status = 'active' 
                    AND sm.role != 'leader'
                    ORDER BY sm.joined_at ASC
                """, (self.squadron_data['id'],))
                
                members = await cursor.fetchall()
            
            if not members:
                embed = discord.Embed(
                    title="❌ Sin Miembros Disponibles",
                    description="No hay otros miembros en tu escuadrón para transferir el liderazgo.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Sugerencia",
                    value="Invita a otros usuarios a tu escuadrón primero antes de transferir el liderazgo.",
                    inline=False
                )
                await self._safe_send(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear embed informativo
            embed = discord.Embed(
                title="👑 Transferir Liderazgo",
                description=f"Selecciona a quién transferir el liderazgo del escuadrón **{self.squadron_data['squadron_name']}**",
                color=0xffd700
            )
            
            embed.add_field(
                name="⚠️ Importante",
                value="• Una vez transferido, **NO podrás recuperar** el liderazgo automáticamente\n"
                      "• El nuevo líder tendrá control total del escuadrón\n"
                      "• Tu rol cambiará a 'miembro'",
                inline=False
            )
            
            embed.add_field(
                name="👥 Miembros Disponibles",
                value=f"**{len(members)}** miembros pueden recibir el liderazgo",
                inline=True
            )
            
            # Crear vista con selector de miembros
            view = LeadershipTransferView(self.squadron_data, members)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en transferencia de liderazgo: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error al preparar la transferencia de liderazgo.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📋 Gestionar Miembros", style=discord.ButtonStyle.secondary, emoji="📋")
    async def manage_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver y gestionar miembros del escuadrón"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener todos los miembros del escuadrón
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT sm.discord_id, sm.ingame_name, sm.role, sm.joined_at, sm.status
                    FROM squadron_members sm
                    WHERE sm.squadron_id = ?
                    ORDER BY 
                        CASE sm.role 
                            WHEN 'leader' THEN 1 
                            WHEN 'officer' THEN 2 
                            ELSE 3 
                        END,
                        sm.joined_at ASC
                """, (self.squadron_data['id'],))
                
                members = await cursor.fetchall()
            
            embed = discord.Embed(
                title=f"👥 Miembros de {self.squadron_data['squadron_name']}",
                description=f"Total de miembros: **{len(members)}**/{self.squadron_data['max_members']}",
                color=0x00aa88
            )
            
            # Mostrar miembros por rol
            leaders = [m for m in members if m[2] == 'leader']
            officers = [m for m in members if m[2] == 'officer']
            regular_members = [m for m in members if m[2] == 'member']
            
            if leaders:
                leader_text = ""
                for member in leaders:
                    discord_id, ingame_name, role, joined_at, status = member
                    status_emoji = "🟢" if status == 'active' else "🔴"
                    leader_text += f"{status_emoji} **{ingame_name}** (`{discord_id}`)\n"
                
                embed.add_field(
                    name="👑 Líder",
                    value=leader_text,
                    inline=False
                )
            
            if officers:
                officer_text = ""
                for member in officers[:5]:  # Máximo 5 oficiales
                    discord_id, ingame_name, role, joined_at, status = member
                    status_emoji = "🟢" if status == 'active' else "🔴"
                    officer_text += f"{status_emoji} **{ingame_name}**\n"
                
                if len(officers) > 5:
                    officer_text += f"... y {len(officers) - 5} más"
                
                embed.add_field(
                    name="⭐ Oficiales",
                    value=officer_text,
                    inline=True
                )
            
            if regular_members:
                member_text = ""
                for member in regular_members[:8]:  # Máximo 8 miembros
                    discord_id, ingame_name, role, joined_at, status = member
                    status_emoji = "🟢" if status == 'active' else "🔴"
                    member_text += f"{status_emoji} {ingame_name}\n"
                
                if len(regular_members) > 8:
                    member_text += f"... y {len(regular_members) - 8} más"
                
                embed.add_field(
                    name="👤 Miembros",
                    value=member_text if member_text else "Sin miembros regulares",
                    inline=True
                )
            
            embed.add_field(
                name="ℹ️ Información",
                value="🟢 = Activo • 🔴 = Inactivo\nComo líder, puedes gestionar roles y permisos.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error gestionando miembros: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error al obtener la lista de miembros.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class LeadershipTransferView(discord.ui.View):
    """Vista para seleccionar nuevo líder del escuadrón"""
    
    def __init__(self, squadron_data: dict, members: list):
        super().__init__(timeout=300)
        self.squadron_data = squadron_data
        self.members = members
        
        # Crear selector con miembros disponibles
        if members:
            options = []
            for member in members[:25]:  # Discord limit
                discord_id, ingame_name, role = member
                
                role_emoji = "⭐" if role == "officer" else "👤"
                
                options.append(discord.SelectOption(
                    label=f"{ingame_name}",
                    description=f"{role_emoji} {role.title()} • ID: {discord_id}",
                    value=discord_id,
                    emoji="👑"
                ))
            
            self.add_item(LeadershipTransferSelect(options, self.squadron_data))
    
    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def cancel_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar transferencia de liderazgo"""
        embed = discord.Embed(
            title="❌ Transferencia Cancelada",
            description="La transferencia de liderazgo ha sido cancelada.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class LeadershipTransferSelect(discord.ui.Select):
    """Selector para elegir nuevo líder"""
    
    def __init__(self, options: list, squadron_data: dict):
        super().__init__(
            placeholder="👑 Selecciona el nuevo líder...",
            options=options
        )
        self.squadron_data = squadron_data
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            new_leader_discord_id = self.values[0]
            current_leader_discord_id = str(interaction.user.id)
            
            # Buscar información del nuevo líder
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT ingame_name FROM squadron_members
                    WHERE squadron_id = ? AND discord_id = ? AND status = 'active'
                """, (self.squadron_data['id'], new_leader_discord_id))
                
                new_leader_data = await cursor.fetchone()
                
                if not new_leader_data:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="El miembro seleccionado no se encuentra en el escuadrón.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                new_leader_ingame_name = new_leader_data[0]
            
            # Crear vista de confirmación
            embed = discord.Embed(
                title="⚠️ Confirmar Transferencia de Liderazgo",
                description=f"¿Estás seguro de que quieres transferir el liderazgo del escuadrón **{self.squadron_data['squadron_name']}** a **{new_leader_ingame_name}**?",
                color=0xff9900
            )
            
            embed.add_field(
                name="📋 Cambios que ocurrirán",
                value=f"• **{new_leader_ingame_name}** se convertirá en el líder\n"
                      f"• Tu rol cambiará a 'miembro'\n"
                      f"• **NO podrás** recuperar el liderazgo automáticamente",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Esta acción es irreversible",
                value="Solo el nuevo líder podrá transferir el liderazgo de vuelta.",
                inline=False
            )
            
            view = LeadershipTransferConfirmView(
                self.squadron_data, 
                current_leader_discord_id, 
                new_leader_discord_id, 
                new_leader_ingame_name
            )
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en callback de transferencia: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error al procesar la selección.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class LeadershipTransferConfirmView(discord.ui.View):
    """Vista de confirmación final para transferencia de liderazgo"""
    
    def __init__(self, squadron_data: dict, current_leader_id: str, new_leader_id: str, new_leader_name: str):
        super().__init__(timeout=300)
        self.squadron_data = squadron_data
        self.current_leader_id = current_leader_id
        self.new_leader_id = new_leader_id
        self.new_leader_name = new_leader_name
    
    @discord.ui.button(
        label="✅ Confirmar Transferencia",
        style=discord.ButtonStyle.success,
        emoji="👑"
    )
    async def confirm_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar y ejecutar transferencia de liderazgo"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = await transfer_squadron_leadership(
                self.squadron_data['id'],
                self.current_leader_id,
                self.new_leader_id,
                str(interaction.guild.id)
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Liderazgo Transferido",
                    description=f"El liderazgo del escuadrón **{self.squadron_data['squadron_name']}** ha sido transferido exitosamente a **{self.new_leader_name}**.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🎉 ¡Transferencia Completada!",
                    value=f"• **{self.new_leader_name}** es ahora el líder\n"
                          f"• Tu rol ha cambiado a 'miembro'\n"
                          f"• El nuevo líder ha sido notificado",
                    inline=False
                )
                
                # Notificar al nuevo líder
                try:
                    guild = interaction.guild
                    new_leader_member = guild.get_member(int(self.new_leader_id))
                    
                    if new_leader_member:
                        leader_embed = discord.Embed(
                            title="👑 ¡Felicidades! Eres el nuevo líder",
                            description=f"Has sido promovido a líder del escuadrón **{self.squadron_data['squadron_name']}**",
                            color=discord.Color.gold()
                        )
                        
                        leader_embed.add_field(
                            name="📋 Tus nuevas responsabilidades",
                            value="• Gestionar miembros del escuadrón\n"
                                  "• Transferir liderazgo si es necesario\n"
                                  "• Representar al escuadrón",
                            inline=False
                        )
                        
                        try:
                            await new_leader_member.send(embed=leader_embed)
                        except:
                            pass  # Si no se puede enviar DM, no es crítico
                
                except Exception as notify_error:
                    logger.warning(f"No se pudo notificar al nuevo líder: {notify_error}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error en Transferencia",
                    description="No se pudo completar la transferencia de liderazgo. Inténtalo nuevamente.",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error confirmando transferencia: {e}")
            embed = discord.Embed(
                title="❌ Error Inesperado",
                description="Hubo un error al procesar la transferencia de liderazgo.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def cancel_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar transferencia de liderazgo"""
        embed = discord.Embed(
            title="❌ Transferencia Cancelada",
            description="La transferencia de liderazgo ha sido cancelada.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def transfer_squadron_leadership(squadron_id: int, current_leader_id: str, new_leader_id: str, guild_id: str) -> bool:
    """Transferir liderazgo de escuadrón a otro miembro"""
    try:
        async with aiosqlite.connect(taxi_db.db_path) as db:
            # Verificar que ambos usuarios están en el escuadrón
            cursor = await db.execute("""
                SELECT discord_id, role FROM squadron_members
                WHERE squadron_id = ? AND discord_id IN (?, ?) AND status = 'active'
            """, (squadron_id, current_leader_id, new_leader_id))
            
            members = await cursor.fetchall()
            
            if len(members) != 2:
                logger.warning(f"No se encontraron ambos miembros para transferencia: {members}")
                return False
            
            # Verificar que el usuario actual es realmente el líder
            current_is_leader = any(member[0] == current_leader_id and member[1] == 'leader' for member in members)
            new_is_member = any(member[0] == new_leader_id for member in members)
            
            if not current_is_leader or not new_is_member:
                logger.warning(f"Verificación de roles falló - current_is_leader: {current_is_leader}, new_is_member: {new_is_member}")
                return False
            
            # Obtener nombre del nuevo líder
            cursor = await db.execute("""
                SELECT ingame_name FROM squadron_members
                WHERE squadron_id = ? AND discord_id = ? AND status = 'active'
            """, (squadron_id, new_leader_id))
            
            new_leader_data = await cursor.fetchone()
            if not new_leader_data:
                return False
            
            new_leader_ingame_name = new_leader_data[0]
            
            # Actualizar el registro del escuadrón con el nuevo líder
            await db.execute("""
                UPDATE squadrons 
                SET leader_discord_id = ?, leader_ingame_name = ?
                WHERE id = ?
            """, (new_leader_id, new_leader_ingame_name, squadron_id))
            
            # Cambiar rol del líder actual a miembro
            await db.execute("""
                UPDATE squadron_members 
                SET role = 'member'
                WHERE squadron_id = ? AND discord_id = ?
            """, (squadron_id, current_leader_id))
            
            # Cambiar rol del nuevo líder
            await db.execute("""
                UPDATE squadron_members 
                SET role = 'leader'
                WHERE squadron_id = ? AND discord_id = ?
            """, (squadron_id, new_leader_id))
            
            await db.commit()
            
            logger.info(f"Liderazgo de escuadrón {squadron_id} transferido de {current_leader_id} a {new_leader_id} ({new_leader_ingame_name})")
            return True
            
    except Exception as e:
        logger.error(f"Error transfiriendo liderazgo de escuadrón: {e}")
        return False


async def setup(bot):
    await bot.add_cog(MechanicSystem(bot))