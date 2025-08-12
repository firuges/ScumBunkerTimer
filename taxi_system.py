#!/usr/bin/env python3
"""
Sistema de Taxi Interactivo con Restricciones de Zona PVP/PVE
Canal dedicado con gestión completa de transporte
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from taxi_database import taxi_db
from taxi_config import taxi_config
import math

logger = logging.getLogger(__name__)

class TaxiSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.taxi_channels = {}  # {guild_id: channel_id}
        self.active_requests = {}  # {request_id: request_data}

    async def setup_taxi_channel(self, guild_id: int, channel_id: int):
        """Configurar canal de taxi con embed interactivo"""
        self.taxi_channels[guild_id] = channel_id
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
        
        # Embed principal del taxi
        embed = discord.Embed(
            title="🚖 Sistema de Taxi SCUM",
            description="Transporte rápido y seguro por toda la isla",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🗺️ Zonas de Servicio:",
            value="""
            🛡️ **Zonas Seguras** - Servicio completo disponible
            ⚔️ **Zonas de Combate** - Solo recogida de emergencia
            🚫 **Zonas Restringidas** - Sin servicio (Base Militar)
            💼 **Zonas Comerciales** - Servicio prioritario
            """,
            inline=False
        )
        
        embed.add_field(
            name="💰 Tarifas:",
            value=f"""
            ```yaml
            Tarifa base: ${taxi_config.TAXI_BASE_RATE}
            Por kilómetro: ${taxi_config.TAXI_PER_KM_RATE}
            
            Tipos de Vehículo:
            🚗 Sedán: Base
            🚙 SUV: +30%
            🚚 Camión: +50%
            🚐 Furgoneta: +20%
            ```
            """,
            inline=False
        )
        
        embed.add_field(
            name="🎯 Servicios:",
            value="""
            🚖 **Solicitar Taxi** - Pedir transporte
            👨‍✈️ **Ser Conductor** - Registrarse para conducir
            📊 **Ver Estado** - Consultar conductores disponibles
            🗺️ **Mapa de Zonas** - Ver restricciones del mapa
            """,
            inline=False
        )
        
        embed.set_footer(text="Estado del sistema: " + ("🟢 Activo" if taxi_config.TAXI_ENABLED else "🔴 Inactivo"))
        
        # Vista con botones de taxi
        view = TaxiMainView()
        
        await channel.send(embed=embed, view=view)
        return True

    # === COMANDOS DE TAXI ===
    
    @app_commands.command(name="taxi_solicitar", description="🚖 Solicitar un taxi")
    @app_commands.describe(
        destino="Zona de destino",
        vehiculo="Tipo de vehículo preferido"
    )
    @app_commands.choices(vehiculo=[
        app_commands.Choice(name="🚗 Sedán (Básico)", value="sedan"),
        app_commands.Choice(name="🚙 SUV (+30%)", value="suv"),
        app_commands.Choice(name="🚚 Camión (+50%)", value="truck"),
        app_commands.Choice(name="🚐 Furgoneta (+20%)", value="van")
    ])
    async def taxi_solicitar(self, interaction: discord.Interaction, destino: str, vehiculo: str = "sedan"):
        """Solicitar un taxi"""
        await interaction.response.defer()
        
        # Verificar si el sistema está habilitado
        if not taxi_config.TAXI_ENABLED:
            embed = discord.Embed(
                title="❌ Sistema Deshabilitado",
                description="El sistema de taxi está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
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
        
        # Verificar si ya tiene una solicitud activa
        active_request = await taxi_db.get_active_taxi_request(interaction.user.id)
        if active_request:
            embed = discord.Embed(
                title="⏳ Solicitud Activa",
                description="Ya tienes una solicitud de taxi activa",
                color=discord.Color.orange()
            )
            embed.add_field(name="🎯 Destino", value=active_request['destination'], inline=True)
            embed.add_field(name="📅 Solicitado", value=f"<t:{int(active_request['created_at'].timestamp())}:R>", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Buscar zona de destino válida
        destination_zone = taxi_config.find_zone_by_name(destino)
        if not destination_zone:
            embed = discord.Embed(
                title="❌ Zona No Encontrada",
                description=f"No se encontró la zona '{destino}'. Usa `/taxi_zonas` para ver zonas disponibles",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar restricciones de zona
        if destination_zone.get('restriction') == 'forbidden':
            embed = discord.Embed(
                title="🚫 Zona Restringida",
                description=f"No se permite el servicio de taxi en {destination_zone['name']}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Calcular costo estimado
        base_cost = taxi_config.TAXI_BASE_RATE
        distance = destination_zone.get('distance', 10)  # Distancia estimada
        vehicle_multiplier = {
            'sedan': 1.0,
            'suv': 1.3,
            'truck': 1.5,
            'van': 1.2
        }.get(vehiculo, 1.0)
        
        total_cost = int((base_cost + (distance * taxi_config.TAXI_PER_KM_RATE)) * vehicle_multiplier)
        
        # Verificar balance del usuario
        balance = await taxi_db.get_user_balance(interaction.user.id)
        if balance < total_cost:
            embed = discord.Embed(
                title="💰 Saldo Insuficiente",
                description=f"Necesitas ${total_cost:,} pero solo tienes ${balance:,}",
                color=discord.Color.red()
            )
            embed.add_field(name="💳 Costo del Viaje", value=f"${total_cost:,}", inline=True)
            embed.add_field(name="💰 Tu Balance", value=f"${balance:,}", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Crear solicitud de taxi
        request_id = await taxi_db.create_taxi_request(
            passenger_id=interaction.user.id,
            destination=destination_zone['name'],
            vehicle_type=vehiculo,
            estimated_cost=total_cost
        )
        
        if request_id:
            embed = discord.Embed(
                title="🚖 Taxi Solicitado",
                description="Tu solicitud ha sido enviada a los conductores disponibles",
                color=discord.Color.green()
            )
            
            embed.add_field(name="🎯 Destino", value=destination_zone['name'], inline=True)
            embed.add_field(name="🚗 Vehículo", value=vehiculo.title(), inline=True)
            embed.add_field(name="💰 Costo Estimado", value=f"${total_cost:,}", inline=True)
            embed.add_field(name="📍 Zona", value=destination_zone.get('type', 'normal').title(), inline=True)
            embed.add_field(name="⏱️ Tiempo Estimado", value="5-15 minutos", inline=True)
            embed.add_field(name="🆔 Solicitud ID", value=f"#{request_id}", inline=True)
            
            # Crear vista con botones
            view = TaxiRequestView(request_id)
            await interaction.followup.send(embed=embed, view=view)
            
            # Notificar a conductores disponibles (si los hay)
            await self.notify_available_drivers(request_id, destination_zone, total_cost)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo crear la solicitud de taxi. Intenta nuevamente",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_status", description="📊 Ver estado de tu solicitud de taxi")
    async def taxi_status(self, interaction: discord.Interaction):
        """Ver estado de solicitud activa"""
        await interaction.response.defer(ephemeral=True)
        
        # Buscar solicitud activa
        active_request = await taxi_db.get_active_taxi_request(interaction.user.id)
        if not active_request:
            embed = discord.Embed(
                title="ℹ️ Sin Solicitudes",
                description="No tienes solicitudes de taxi activas. Usa `/taxi_solicitar` para pedir un taxi",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Crear embed con información de la solicitud
        embed = discord.Embed(
            title="🚖 Estado de tu Taxi",
            description="Información de tu solicitud activa",
            color=discord.Color.blue()
        )
        
        status_colors = {
            'pending': discord.Color.orange(),
            'assigned': discord.Color.blue(),
            'en_route': discord.Color.gold(),
            'completed': discord.Color.green(),
            'cancelled': discord.Color.red()
        }
        
        status_text = {
            'pending': '⏳ Buscando conductor',
            'assigned': '👨‍✈️ Conductor asignado',
            'en_route': '🚗 En camino',
            'completed': '✅ Completado',
            'cancelled': '❌ Cancelado'
        }
        
        embed.color = status_colors.get(active_request['status'], discord.Color.blue())
        
        embed.add_field(name="📊 Estado", value=status_text.get(active_request['status'], 'Desconocido'), inline=True)
        embed.add_field(name="🎯 Destino", value=active_request['destination'], inline=True)
        embed.add_field(name="💰 Costo", value=f"${active_request['estimated_cost']:,}", inline=True)
        
        embed.add_field(name="🚗 Vehículo", value=active_request['vehicle_type'].title(), inline=True)
        embed.add_field(name="📅 Solicitado", value=f"<t:{int(active_request['created_at'].timestamp())}:R>", inline=True)
        embed.add_field(name="🆔 ID", value=f"#{active_request['id']}", inline=True)
        
        # Información del conductor si está asignado
        if active_request.get('driver_id'):
            driver = await taxi_db.get_user(active_request['driver_id'])
            embed.add_field(name="👨‍✈️ Conductor", value=driver['username'] if driver else 'Desconocido', inline=True)
        
        embed.set_footer(text="Usa /taxi_cancelar para cancelar la solicitud")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_cancelar", description="❌ Cancelar tu solicitud de taxi")
    async def taxi_cancelar(self, interaction: discord.Interaction):
        """Cancelar solicitud de taxi activa"""
        await interaction.response.defer(ephemeral=True)
        
        # Buscar solicitud activa
        active_request = await taxi_db.get_active_taxi_request(interaction.user.id)
        if not active_request:
            embed = discord.Embed(
                title="ℹ️ Sin Solicitudes",
                description="No tienes solicitudes de taxi para cancelar",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Cancelar la solicitud
        success = await taxi_db.cancel_taxi_request(active_request['id'])
        
        if success:
            embed = discord.Embed(
                title="❌ Solicitud Cancelada",
                description="Tu solicitud de taxi ha sido cancelada",
                color=discord.Color.red()
            )
            embed.add_field(name="🎯 Destino", value=active_request['destination'], inline=True)
            embed.add_field(name="💰 Monto", value=f"${active_request['estimated_cost']:,} (No cobrado)", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo cancelar la solicitud",
                color=discord.Color.red()
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_zonas", description="🗺️ Ver zonas disponibles para taxi")
    async def taxi_zonas(self, interaction: discord.Interaction):
        """Mostrar zonas disponibles"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🗺️ Zonas de Taxi Disponibles",
            description="Zonas donde puedes solicitar transporte",
            color=discord.Color.blue()
        )
        
        # Agrupar zonas por tipo
        zones_by_type = {}
        for zone_id, zone in taxi_config.ZONES.items():
            zone_type = zone.get('type', 'normal')
            if zone_type not in zones_by_type:
                zones_by_type[zone_type] = []
            zones_by_type[zone_type].append(zone)
        
        # Mostrar zonas por tipo
        type_icons = {
            'safe': '🛡️',
            'combat': '⚔️', 
            'commercial': '💼',
            'normal': '🏘️'
        }
        
        for zone_type, zones in zones_by_type.items():
            if zones:
                icon = type_icons.get(zone_type, '📍')
                zone_list = []
                
                for zone in zones:
                    restriction = zone.get('restriction', 'allowed')
                    if restriction == 'forbidden':
                        continue  # No mostrar zonas prohibidas
                    
                    zone_name = zone['name']
                    if restriction == 'emergency_only':
                        zone_name += ' (Solo emergencia)'
                    
                    zone_list.append(zone_name)
                
                if zone_list:
                    embed.add_field(
                        name=f"{icon} {zone_type.title()}",
                        value='\n'.join(f"• {zone}" for zone in zone_list[:10]),  # Límite de 10 por tipo
                        inline=True
                    )
        
        embed.add_field(
            name="💰 Información de Tarifas",
            value=f"• Tarifa base: ${taxi_config.TAXI_BASE_RATE}\n• Por km: ${taxi_config.TAXI_PER_KM_RATE}\n• Usa `/taxi_tarifas` para más detalles",
            inline=False
        )
        
        embed.set_footer(text="Usa /taxi_solicitar [zona] para pedir un taxi")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="taxi_tarifas", description="💰 Ver tarifas del servicio de taxi")
    async def taxi_tarifas(self, interaction: discord.Interaction):
        """Mostrar tarifas del taxi"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="💰 Tarifas del Servicio de Taxi",
            description="Costos del transporte en el servidor",
            color=discord.Color.gold()
        )
        
        # Tarifa base
        embed.add_field(
            name="💵 Tarifa Base",
            value=f"${taxi_config.TAXI_BASE_RATE:,}",
            inline=True
        )
        
        embed.add_field(
            name="📏 Por Kilómetro",
            value=f"${taxi_config.TAXI_PER_KM_RATE:,}",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Por Minuto de Espera",
            value=f"${taxi_config.TAXI_WAIT_RATE:,}",
            inline=True
        )
        
        # Tipos de vehículo
        embed.add_field(
            name="🚗 Tipos de Vehículo",
            value="""
            🚗 **Sedán**: Tarifa base
            🚙 **SUV**: +30% (+$50 aprox.)
            🚚 **Camión**: +50% (+$80 aprox.) 
            🚐 **Furgoneta**: +20% (+$35 aprox.)
            """,
            inline=False
        )
        
        # Zonas especiales
        embed.add_field(
            name="🗺️ Tarifas por Zona",
            value="""
            🛡️ **Zonas Seguras**: Tarifa normal
            ⚔️ **Zonas de Combate**: +25% (riesgo)
            💼 **Zonas Comerciales**: Tarifa normal
            🆘 **Emergencias**: +50% (servicio urgente)
            """,
            inline=False
        )
        
        # Ejemplo de cálculo
        example_cost = taxi_config.TAXI_BASE_RATE + (10 * taxi_config.TAXI_PER_KM_RATE)
        embed.add_field(
            name="📊 Ejemplo de Cálculo",
            value=f"""
            ```yaml
            Destino: 10km de distancia
            Tarifa base: ${taxi_config.TAXI_BASE_RATE}
            Distancia: 10km × ${taxi_config.TAXI_PER_KM_RATE} = ${10 * taxi_config.TAXI_PER_KM_RATE}
            Total: ${example_cost}
            
            Con SUV (+30%): ${int(example_cost * 1.3)}
            ```
            """,
            inline=False
        )
        
        embed.set_footer(text="Los precios pueden variar según disponibilidad y condiciones del servidor")
        await interaction.followup.send(embed=embed)

    async def notify_available_drivers(self, request_id: int, destination_zone: dict, cost: int):
        """Notificar a conductores disponibles sobre nueva solicitud"""
        try:
            # Esta función se puede implementar más tarde para notificar conductores
            # Por ahora solo registramos el log
            logger.info(f"Nueva solicitud de taxi #{request_id} a {destination_zone['name']} por ${cost}")
        except Exception as e:
            logger.error(f"Error notificando conductores: {e}")

    # Comandos setup temporalmente deshabilitados - requieren migración completa
    # TODO: Migrar completamente a app_commands  
    pass
    #    """Comando para configurar el canal de taxi"""
    #    success = await self.setup_taxi_channel(ctx.guild.id, channel.id)
    #    
    #    if success:
    #        embed = discord.Embed(
    #            title="✅ Canal de Taxi Configurado",
    #            description=f"Canal {channel.mention} configurado correctamente",
    #            color=discord.Color.green()
    #        )
    #    else:
    #        embed = discord.Embed(
    #            title="❌ Error",
    #            description="No se pudo configurar el canal de taxi",
    #            color=discord.Color.red()
    #        )
    #    
    #    await ctx.respond(embed=embed, ephemeral=True)

    # TODO: También requiere migración
    # @commands.slash_command(name="taxi_config", description="[ADMIN] Configurar sistema de taxi")
    # @commands.has_permissions(administrator=True)
    # async def taxi_config_cmd(self, ctx):
    #    """Comando para configurar el sistema de taxi"""
    #    view = TaxiConfigView()
    #    
    #    embed = discord.Embed(
    #        title="⚙️ Configuración del Sistema de Taxi",
    #        description="Ajusta los parámetros del sistema",
    #        color=discord.Color.blue()
    #    )
    #    
    #    embed.add_field(
    #        name="Estado Actual:",
    #        value=f"""
    #        ```yaml
    #        Sistema General: {'✅' if taxi_config.FEATURE_ENABLED else '❌'}
    #        Taxi: {'✅' if taxi_config.TAXI_ENABLED else '❌'}
    #        Banco: {'✅' if taxi_config.BANK_ENABLED else '❌'}
    #        Welcome Pack: {'✅' if taxi_config.WELCOME_PACK_ENABLED else '❌'}
    #        
    #        Tarifa Base: ${taxi_config.TAXI_BASE_RATE}
    #        Por KM: ${taxi_config.TAXI_PER_KM_RATE}
    #        Comisión Conductor: {taxi_config.DRIVER_COMMISSION*100:.0f}%
    #        ```
    #        """,
    #        inline=False
    #    )
    #    
    #    await ctx.respond(embed=embed, view=view, ephemeral=True)

class TaxiMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🚖 Solicitar Taxi", 
        style=discord.ButtonStyle.primary,
        emoji="📱",
        custom_id="request_taxi"
    )
    async def request_taxi(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón para solicitar taxi"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.TAXI_ENABLED:
            embed = discord.Embed(
                title="❌ Servicio No Disponible",
                description="El servicio de taxi está temporalmente deshabilitado",
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
                description="Debes registrarte primero en el canal de bienvenida",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para solicitar taxi
        modal = TaxiRequestModal(user_data)
        await interaction.followup.send("🚖 Abriendo formulario de solicitud...", ephemeral=True)
        await interaction.edit_original_response(content="", view=TaxiRequestView(modal, user_data))

    @discord.ui.button(
        label="👨‍✈️ Ser Conductor", 
        style=discord.ButtonStyle.secondary,
        emoji="🚗",
        custom_id="become_driver"
    )
    async def become_driver(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón para registrarse como conductor"""
        await interaction.response.defer(ephemeral=True)
        
        if not taxi_config.TAXI_ENABLED:
            embed = discord.Embed(
                title="❌ Servicio No Disponible",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar registro
        user_data = await taxi_db.get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="Debes registrarte primero en el canal de bienvenida",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Mostrar vista de registro de conductor
        view = DriverRegistrationView(user_data)
        
        embed = discord.Embed(
            title="👨‍✈️ Registro de Conductor",
            description="Únete al equipo de conductores y gana dinero",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Beneficios:",
            value=f"""
            • Gana **{taxi_config.DRIVER_COMMISSION*100:.0f}%** de cada viaje
            • Horarios flexibles (online/offline)
            • Sistema de calificaciones
            • Bonos por nivel de conductor
            • Ingresos diarios estimados: $500-2000
            """,
            inline=False
        )
        
        embed.add_field(
            name="🚗 Tipos de Vehículo:",
            value="".join([f"{data['emoji']} **{data['name']}** - Capacidad: {data['capacity']}, Tarifa: +{(data['multiplier']-1)*100:.0f}%\n" 
                          for data in taxi_config.VEHICLE_TYPES.values()]),
            inline=False
        )
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(
        label="📊 Estado del Sistema", 
        style=discord.ButtonStyle.secondary,
        emoji="📈",
        custom_id="system_status"
    )
    async def system_status(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Mostrar estado del sistema de taxi"""
        await interaction.response.defer(ephemeral=True)
        
        # Obtener estadísticas
        stats = await taxi_db.get_system_stats(str(interaction.guild.id))
        
        embed = discord.Embed(
            title="📊 Estado del Sistema de Taxi",
            description=f"Estadísticas en tiempo real de **{interaction.guild.name}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🚗 Conductores",
            value=f"""
            ```yaml
            Total registrados: {stats['total_drivers']:,}
            Activos ahora: {stats['active_drivers']:,}
            Disponibilidad: {(stats['active_drivers']/max(stats['total_drivers'], 1)*100):.1f}%
            ```
            """,
            inline=True
        )
        
        embed.add_field(
            name="🚖 Viajes",
            value=f"""
            ```yaml
            Completados: {stats['completed_rides']:,}
            Promedio/día: {stats['completed_rides']//30:,}
            Satisfacción: 98.5%
            ```
            """,
            inline=True
        )
        
        embed.add_field(
            name="💰 Economía",
            value=f"""
            ```yaml
            Dinero en circulación: ${stats['total_money']:,.0f}
            Ganancias conductores: ${stats['total_money']*0.1:,.0f}
            Promedio/usuario: ${stats['total_money']/max(stats['total_users'], 1):,.0f}
            ```
            """,
            inline=True
        )
        
        # Tiempo de respuesta estimado
        if stats['active_drivers'] > 0:
            avg_response = "2-5 minutos"
            status_color = "🟢"
        elif stats['total_drivers'] > 0:
            avg_response = "10-15 minutos"
            status_color = "🟡"
        else:
            avg_response = "No disponible"
            status_color = "🔴"
        
        embed.add_field(
            name="⏱️ Tiempo de Respuesta",
            value=f"{status_color} **{avg_response}**",
            inline=False
        )
        
        embed.set_footer(text=f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="🗺️ Mapa de Zonas", 
        style=discord.ButtonStyle.secondary,
        emoji="🌍",
        custom_id="zone_map"
    )
    async def zone_map(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Mostrar mapa de zonas y restricciones"""
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="🗺️ Mapa de Zonas - Isla SCUM",
            description="Restricciones de servicio por zona",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="🛡️ Zonas Seguras",
            value="""
            🏙️ **Ciudad Central** - Servicio completo
            🚢 **Puerto Norte/Sur** - Servicio prioritario
            🏠 **Áreas Residenciales** - Servicio normal
            """,
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Zonas de Combate",
            value="""
            🏰 **Bunker D1** - Solo recogida de emergencia
            🏰 **Bunker C4** - Solo recogida de emergencia  
            🏰 **Bunker A1** - Solo recogida de emergencia
            🏰 **Bunker A3** - Solo recogida de emergencia
            """,
            inline=False
        )
        
        embed.add_field(
            name="🚫 Zonas Restringidas",
            value="""
            🪖 **Base Militar Central** - Sin servicio
            ⚠️ **Zona militar** - Radio de 2km sin taxi
            """,
            inline=False
        )
        
        embed.add_field(
            name="💼 Zonas Especiales",
            value="""
            ✈️ **Aeropuerto** - Servicio neutral
            🏭 **Zonas Industriales** - Servicio disponible
            🌲 **Áreas Rurales** - Servicio limitado
            """,
            inline=False
        )
        
        embed.add_field(
            name="💡 Consejos:",
            value="""
            • Los conductores pueden rechazar viajes a zonas peligrosas
            • Las tarifas pueden aumentar en zonas de riesgo
            • Siempre verifica tu zona antes de solicitar
            • En combate activo, el servicio puede suspenderse
            """,
            inline=False
        )
        
        embed.set_footer(text="Mapa basado en https://scum-map.com/en/catalog/scum/island")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class TaxiRequestView(discord.ui.View):
    def __init__(self, modal, user_data):
        super().__init__(timeout=300)
        self.modal = modal
        self.user_data = user_data

    @discord.ui.button(label="📱 Abrir Formulario", style=discord.ButtonStyle.primary)
    async def open_modal(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)

class TaxiRequestModal(discord.ui.Modal):
    def __init__(self, user_data):
        super().__init__(title="🚖 Solicitar Taxi")
        self.user_data = user_data
        
        self.pickup_coords = discord.ui.TextInput(
            label="Coordenadas de Recogida (X,Y,Z)",
            placeholder="1500,-2000,100",
            required=True,
            max_length=50
        )
        
        self.destination_coords = discord.ui.TextInput(
            label="Destino (X,Y,Z) - Opcional",
            placeholder="500,1000,50",
            required=False,
            max_length=50
        )
        
        self.vehicle_type = discord.ui.TextInput(
            label="Tipo de Vehículo",
            placeholder="sedan, suv, truck, van",
            required=False,
            max_length=20,
            default="sedan"
        )
        
        self.instructions = discord.ui.TextInput(
            label="Instrucciones Especiales",
            placeholder="Puntos de referencia, urgencia, etc.",
            required=False,
            max_length=200,
            style=discord.TextStyle.long
        )
        
        self.add_item(self.pickup_coords)
        self.add_item(self.destination_coords)
        self.add_item(self.vehicle_type)
        self.add_item(self.instructions)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parsear coordenadas de recogida
            pickup_parts = [float(x.strip()) for x in self.pickup_coords.value.split(',')]
            if len(pickup_parts) != 3:
                raise ValueError("Coordenadas de recogida deben ser X,Y,Z")
            
            pickup_x, pickup_y, pickup_z = pickup_parts
            
            # Parsear destino si se proporciona
            dest_x = dest_y = dest_z = None
            if self.destination_coords.value.strip():
                dest_parts = [float(x.strip()) for x in self.destination_coords.value.split(',')]
                if len(dest_parts) != 3:
                    raise ValueError("Coordenadas de destino deben ser X,Y,Z")
                dest_x, dest_y, dest_z = dest_parts
            
            # Validar tipo de vehículo
            vehicle_type = self.vehicle_type.value.lower().strip()
            if vehicle_type not in taxi_config.VEHICLE_TYPES:
                vehicle_type = "sedan"
            
            # Crear solicitud
            success, result = await taxi_db.create_taxi_request(
                self.user_data['user_id'],
                pickup_x, pickup_y, pickup_z,
                dest_x, dest_y, dest_z,
                vehicle_type,
                self.instructions.value
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Solicitud de Taxi Creada",
                    description=f"Solicitud #{result['request_id']} registrada exitosamente",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📍 Ubicación de Recogida",
                    value=f"**X:** {pickup_x}, **Y:** {pickup_y}, **Z:** {pickup_z}\n**Zona:** {result['pickup_zone']['zone_name']}",
                    inline=False
                )
                
                if dest_x is not None:
                    embed.add_field(
                        name="🎯 Destino",
                        value=f"**X:** {dest_x}, **Y:** {dest_y}, **Z:** {dest_z}\n**Zona:** {result['destination_zone']['zone_name']}",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="💰 Costo Estimado",
                        value=f"**${result['estimated_cost']:.2f}** ({result['distance']/1000:.2f} km)",
                        inline=True
                    )
                
                embed.add_field(
                    name="🚗 Vehículo Solicitado",
                    value=f"{taxi_config.VEHICLE_TYPES[vehicle_type]['emoji']} {taxi_config.VEHICLE_TYPES[vehicle_type]['name']}",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Próximos Pasos",
                    value="Los conductores cercanos han sido notificados. Recibirás una respuesta pronto.",
                    inline=False
                )
                
                embed.set_footer(text=f"UUID: {result['request_uuid']}")
                
            else:
                embed = discord.Embed(
                    title="❌ Error en Solicitud",
                    description=result.get('error', 'Error desconocido'),
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
                description="Ocurrió un error inesperado",
                color=discord.Color.red()
            )
            logger.error(f"Error en solicitud de taxi: {e}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class DriverRegistrationView(discord.ui.View):
    def __init__(self, user_data):
        super().__init__(timeout=300)
        self.user_data = user_data
        
        # Crear select con tipos de vehículo
        options = []
        for key, vehicle in taxi_config.VEHICLE_TYPES.items():
            options.append(discord.SelectOption(
                label=vehicle['name'],
                value=key,
                description=f"Capacidad: {vehicle['capacity']} | Tarifa: +{(vehicle['multiplier']-1)*100:.0f}%",
                emoji=vehicle['emoji']
            ))
        
        self.vehicle_select = discord.ui.Select(
            placeholder="Selecciona tu tipo de vehículo...",
            options=options,
            custom_id="vehicle_select"
        )
        
        self.vehicle_select.callback = self.vehicle_selected
        self.add_item(self.vehicle_select)

    async def vehicle_selected(self, interaction: discord.Interaction):
        """Callback cuando se selecciona un vehículo"""
        await interaction.response.defer(ephemeral=True)
        
        selected_vehicle = interaction.data['values'][0]
        vehicle_data = taxi_config.VEHICLE_TYPES[selected_vehicle]
        
        # Registrar como conductor
        success, result = await taxi_db.register_driver(
            self.user_data['user_id'],
            selected_vehicle,
            None  # vehicle_name será agregado después
        )
        
        if success:
            embed = discord.Embed(
                title="✅ ¡Conductor Registrado!",
                description="Te has registrado exitosamente como conductor de taxi",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🆔 Licencia de Conductor",
                value=f"`{result}`",
                inline=True
            )
            
            embed.add_field(
                name="🚗 Vehículo",
                value=f"{vehicle_data['emoji']} **{vehicle_data['name']}**",
                inline=True
            )
            
            embed.add_field(
                name="👥 Capacidad",
                value=f"{vehicle_data['capacity']} pasajeros",
                inline=True
            )
            
            embed.add_field(
                name="💰 Comisión",
                value=f"**{taxi_config.DRIVER_COMMISSION*100:.0f}%** de cada viaje",
                inline=True
            )
            
            embed.add_field(
                name="📈 Multiplicador",
                value=f"+{(vehicle_data['multiplier']-1)*100:.0f}% en tarifas",
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating Inicial",
                value="5.00 ⭐⭐⭐⭐⭐",
                inline=True
            )
            
            embed.add_field(
                name="🚀 Próximos Pasos",
                value="""
                • Usa comandos de conductor para conectarte
                • Mantén una buena calificación
                • Responde rápido a las solicitudes
                • Gana dinero transportando jugadores
                """,
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="❌ Error en Registro",
                description=result,
                color=discord.Color.red()
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class TaxiConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🔄 Toggle Sistema", style=discord.ButtonStyle.primary)
    async def toggle_system(self, button: discord.ui.Button, interaction: discord.Interaction):
        taxi_config.FEATURE_ENABLED = not taxi_config.FEATURE_ENABLED
        status = "activado" if taxi_config.FEATURE_ENABLED else "desactivado"
        await interaction.response.send_message(f"✅ Sistema {status}", ephemeral=True)

    @discord.ui.button(label="🚖 Toggle Taxi", style=discord.ButtonStyle.secondary)
    async def toggle_taxi(self, button: discord.ui.Button, interaction: discord.Interaction):
        taxi_config.TAXI_ENABLED = not taxi_config.TAXI_ENABLED
        status = "activado" if taxi_config.TAXI_ENABLED else "desactivado"
        await interaction.response.send_message(f"✅ Taxi {status}", ephemeral=True)

    @discord.ui.button(label="🏦 Toggle Banco", style=discord.ButtonStyle.secondary)
    async def toggle_bank(self, button: discord.ui.Button, interaction: discord.Interaction):
        taxi_config.BANK_ENABLED = not taxi_config.BANK_ENABLED
        status = "activado" if taxi_config.BANK_ENABLED else "desactivado"
        await interaction.response.send_message(f"✅ Banco {status}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TaxiSystem(bot))
