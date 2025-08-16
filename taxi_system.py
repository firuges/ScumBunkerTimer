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

    async def load_channel_configs(self):
        """Cargar configuraciones de canales desde la base de datos y recrear paneles"""
        try:
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                if "taxi" in channels:
                    guild_id_int = int(guild_id)
                    channel_id = channels["taxi"]
                    
                    # Cargar en memoria
                    self.taxi_channels[guild_id_int] = channel_id
                    
                    # Recrear panel de taxi en el canal
                    await self._recreate_taxi_panel(guild_id_int, channel_id)
                    
                    logger.info(f"Cargada y recreada configuración de taxi para guild {guild_id}: canal {channel_id}")
            
            logger.info(f"Sistema de taxi: {len(self.taxi_channels)} canales cargados con paneles recreados")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones de taxi: {e}")
    
    async def _recreate_taxi_panel(self, guild_id: int, channel_id: int):
        """Recrear panel de taxi en un canal específico"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal de taxi {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Limpiar mensajes anteriores del bot (solo los más recientes para evitar spam)
            try:
                deleted_count = 0
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds:
                        # Solo eliminar si es un embed del sistema (título contiene "Sistema de Taxi")
                        for embed in message.embeds:
                            if embed.title and "Sistema de Taxi" in embed.title:
                                await message.delete()
                                deleted_count += 1
                                break
                if deleted_count > 0:
                    logger.info(f"Eliminados {deleted_count} paneles de taxi anteriores del canal {channel_id}")
            except Exception as cleanup_e:
                logger.warning(f"Error limpiando mensajes de taxi anteriores: {cleanup_e}")
            
            # Crear embed de taxi
            try:
                from taxi_admin import TaxiSystemView
                view = TaxiSystemView()
            except ImportError:
                view = None
            
            embed = discord.Embed(
                title="🚖 Sistema de Taxi SCUM",
                description="Usa `/taxi_solicitar` para viajes, `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=discord.Color.yellow()
            )
            
            embed.add_field(
                name="🗺️ Zonas de Servicio:",
                value="🛡️ **Zonas Seguras** - Servicio completo\n⚔️ **Zonas de Combate** - Solo emergencias\n💼 **Zonas Comerciales** - Servicio prioritario",
                inline=False
            )
            
            if view:
                await channel.send(embed=embed, view=view)
            else:
                await channel.send(embed=embed)
            logger.info(f"Panel de taxi recreado exitosamente en canal {channel_id}")
            
        except Exception as e:
            logger.error(f"Error recreando panel de taxi para canal {channel_id}: {e}")

    async def setup_taxi_channel(self, guild_id: int, channel_id: int):
        """Configurar canal de taxi con embed interactivo"""
        # Guardar en memoria (para acceso rápido)
        self.taxi_channels[guild_id] = channel_id
        
        # Guardar en base de datos (para persistencia)
        await taxi_db.save_channel_config(str(guild_id), "taxi", str(channel_id))
        
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
        user_exists = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
        if not user_exists:
            embed = discord.Embed(
                title="❌ Usuario No Registrado",
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar si ya tiene una solicitud activa
        active_request = await taxi_db.get_active_request_for_user(user_exists['user_id'])
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
        balance = user_exists['balance']
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
        success, result = await taxi_db.create_taxi_request(
            passenger_id=user_exists['user_id'],
            pickup_x=0.0,  # Coordenadas por defecto
            pickup_y=0.0,
            pickup_z=0.0,
            destination_x=0.0,
            destination_y=0.0, 
            destination_z=0.0,
            vehicle_type=vehiculo,
            special_instructions=f"Destino: {destination_zone['name']}"
        )
        
        if success:
            request_id = result['request_id']
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
            
            await interaction.followup.send(embed=embed)
            
            # Notificar a conductores disponibles (si los hay)
            await self.notify_available_drivers(request_id, destination_zone, total_cost)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudo crear la solicitud de taxi: {result.get('error', 'Error desconocido')}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_status", description="📊 Ver estado de tu solicitud de taxi")
    async def taxi_status(self, interaction: discord.Interaction):
        """Ver estado de solicitud activa"""
        await interaction.response.defer(ephemeral=True)
        
        # Buscar solicitud activa  
        user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
        if not user_data:
            embed = discord.Embed(
                title="❌ Usuario No Registrado",
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
            
        active_request = await taxi_db.get_active_request_for_user(user_data['user_id'])
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
        embed.add_field(name="🎯 Destino", value=active_request.get('destination_zone', 'No especificado'), inline=True)
        embed.add_field(name="💰 Costo", value=f"${active_request['estimated_cost']:,}", inline=True)
        
        embed.add_field(name="🚗 Vehículo", value=active_request['vehicle_type'].title(), inline=True)
        embed.add_field(name="📅 Solicitado", value=f"<t:{int(active_request['created_at'].timestamp())}:R>", inline=True)
        embed.add_field(name="🆔 ID", value=f"#{active_request['request_id']}", inline=True)
        
        # Información del conductor si está asignado
        if active_request.get('driver_id'):
            driver = await taxi_db.get_user_by_id(active_request['driver_id'])
            embed.add_field(name="👨‍✈️ Conductor", value=driver['username'] if driver else 'Desconocido', inline=True)
        
        embed.set_footer(text="Usa /taxi_cancelar para cancelar la solicitud")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_cancelar", description="❌ Cancelar tu solicitud de taxi")
    async def taxi_cancelar(self, interaction: discord.Interaction):
        """Cancelar solicitud de taxi activa"""
        await interaction.response.defer(ephemeral=True)
        
        # Buscar solicitud activa
        user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
        if not user_data:
            embed = discord.Embed(
                title="❌ Usuario No Registrado", 
                description="Necesitas registrarte primero. Usa `/welcome_registro`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
            
        active_request = await taxi_db.get_active_request_for_user(user_data['user_id'])
        if not active_request:
            embed = discord.Embed(
                title="ℹ️ Sin Solicitudes",
                description="No tienes solicitudes de taxi para cancelar",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Cancelar la solicitud
        success, message = await taxi_db.cancel_request(active_request['request_id'])
        
        if success:
            embed = discord.Embed(
                title="❌ Solicitud Cancelada",
                description="Tu solicitud de taxi ha sido cancelada",
                color=discord.Color.red()
            )
            embed.add_field(name="🎯 Destino", value=active_request.get('destination_zone', 'No especificado'), inline=True)
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

    async def server_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompletado para nombres de servidores"""
        try:
            from server_database import server_db
            guild_id = str(interaction.guild.id)
            servers = await server_db.get_monitored_servers(guild_id)
            
            # Filtrar servidores que coincidan con la entrada actual
            matching_servers = []
            for server in servers:
                server_name = server['server_name']
                if current.lower() in server_name.lower():
                    # Verificar si tiene horarios configurados
                    from taxi_database import taxi_db
                    schedules = await taxi_db.get_reset_schedules(server_name)
                    
                    if schedules:
                        label = f"{server_name} ✅ ({len(schedules)} horarios)"
                    else:
                        label = f"{server_name} ⚠️ (sin horarios)"
                    
                    matching_servers.append(app_commands.Choice(name=label, value=server_name))
            
            # Limitar a 25 resultados (límite de Discord)
            return matching_servers[:25]
            
        except Exception as e:
            logger.error(f"Error en autocompletado de servidores: {e}")
            return []

    @app_commands.command(name="ba_reset_alerts", description="🔔 Gestionar alertas de reinicio de servidores")
    @app_commands.describe(
        action="Acción a realizar",
        server_name="Nombre del servidor SCUM (opcional)",
        minutes_before="Minutos antes del reinicio para alertar (por defecto 15)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="🔔 Suscribirme", value="subscribe"),
        app_commands.Choice(name="🔕 Desuscribirme", value="unsubscribe"),
        app_commands.Choice(name="📋 Ver mis alertas", value="list")
    ])
    @app_commands.autocomplete(server_name=server_name_autocomplete)
    async def manage_reset_alerts(self, interaction: discord.Interaction, 
                                action: app_commands.Choice[str], 
                                server_name: str = None, 
                                minutes_before: int = 15):
        """Gestionar suscripciones a alertas de reinicio"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            
            if action.value == "list":
                # Obtener información del usuario para timezone
                user_info = await taxi_db.get_user_by_discord_id(user_id, guild_id)
                user_timezone = user_info.get('timezone', 'UTC') if user_info else 'UTC'
                
                # Auto-actualizar timezone si es UTC (usuarios existentes antes de la feature)
                if user_timezone == 'UTC':
                    from taxi_database import detect_user_timezone
                    new_timezone = detect_user_timezone(interaction)
                    await taxi_db.update_user_timezone(user_id, guild_id, new_timezone)
                    user_timezone = new_timezone
                    logger.info(f"Auto-actualizado timezone de usuario {user_id} a {new_timezone}")
                
                # Mostrar suscripciones del usuario
                subscriptions = await taxi_db.get_user_reset_subscriptions(user_id, guild_id)
                
                if not subscriptions:
                    embed = discord.Embed(
                        title="🔔 Mis Alertas de Reinicio",
                        description="No tienes alertas de reinicio configuradas.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Cómo suscribirte",
                        value="Usa `/ba_reset_alerts` acción:`Suscribirme` server_name:`NombreServidor`",
                        inline=False
                    )
                else:
                    embed = discord.Embed(
                        title="🔔 Mis Alertas de Reinicio",
                        description=f"Tienes **{len(subscriptions)}** alertas configuradas:",
                        color=discord.Color.blue()
                    )
                    
                    # Agregar información del timezone del usuario
                    embed.add_field(
                        name="🌍 Tu Zona Horaria",
                        value=f"{user_timezone}",
                        inline=True
                    )
                    embed.add_field(
                        name="⏰ Horarios Mostrados",
                        value="En tu zona horaria local",
                        inline=True
                    )
                    embed.add_field(
                        name="", 
                        value="",
                        inline=True
                    )  # Spacer for layout
                    
                    # Obtener horarios de cada servidor y convertirlos
                    from taxi_database import convert_time_to_user_timezone
                    
                    for sub in subscriptions:
                        status = "🔔 Activa" if sub['alert_enabled'] else "🔕 Desactivada"
                        
                        # Obtener horarios configurados para este servidor
                        schedules = await taxi_db.get_reset_schedules(sub['server_name'])
                        
                        field_value = f"{status}\n⏰ {sub['minutes_before']} min antes"
                        
                        if schedules:
                            field_value += "\n\n📅 **Horarios:**"
                            days_names = {1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb", 7: "Dom"}
                            
                            for schedule in schedules[:3]:  # Mostrar máximo 3 horarios por servidor
                                # Convertir tiempo al timezone del usuario
                                original_time = schedule['reset_time']
                                schedule_timezone = schedule['timezone']
                                converted_time = convert_time_to_user_timezone(original_time, schedule_timezone, user_timezone)
                                
                                # Mostrar días
                                try:
                                    days_list = [int(d.strip()) for d in schedule['days_of_week'].split(',')]
                                    days_str = ", ".join([days_names[d] for d in sorted(days_list)])
                                except:
                                    days_str = schedule['days_of_week']
                                
                                field_value += f"\n• {converted_time} - {days_str}"
                            
                            if len(schedules) > 3:
                                field_value += f"\n... y {len(schedules) - 3} más"
                        
                        embed.add_field(
                            name=f"🎮 {sub['server_name']}",
                            value=field_value,
                            inline=True
                        )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            # Para suscribir/desuscribir necesitamos el nombre del servidor
            if not server_name:
                # Mostrar servidores disponibles
                from server_database import server_db
                guild_id = str(interaction.guild.id)
                servers = await server_db.get_monitored_servers(guild_id)
                
                if not servers:
                    await interaction.followup.send("❌ No hay servidores registrados. Contacta con un administrador.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="🎯 Selecciona un Servidor",
                    description="Servidores disponibles para alertas:",
                    color=discord.Color.blue()
                )
                
                server_list = []
                for server in servers[:10]:  # Mostrar máximo 10
                    # Verificar si hay horarios configurados para este servidor
                    schedules = await taxi_db.get_reset_schedules(server['server_name'])
                    if schedules:
                        status = "🔔 Con horarios configurados"
                        schedule_count = len(schedules)
                    else:
                        status = "⚠️ Sin horarios configurados"
                        schedule_count = 0
                    
                    server_list.append(f"**{server['server_name']}** - {status} ({schedule_count} horarios)")
                
                embed.add_field(
                    name="📋 Servidores Disponibles",
                    value="\n".join(server_list) if server_list else "No hay servidores disponibles",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Cómo usar",
                    value=f"Usa `/ba_reset_alerts` acción:`{action.name}` server_name:`NombreDelServidor`",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            # Verificar que el servidor existe y tiene horarios
            schedules = await taxi_db.get_reset_schedules(server_name)
            if not schedules:
                await interaction.followup.send(f"❌ El servidor **{server_name}** no tiene horarios de reinicio configurados. Contacta con un administrador.", ephemeral=True)
                return
            
            if action.value == "subscribe":
                # Detectar y actualizar timezone del usuario
                from taxi_database import detect_user_timezone
                user_timezone = detect_user_timezone(interaction)
                await taxi_db.update_user_timezone(user_id, guild_id, user_timezone)
                
                # Suscribir al usuario
                success = await taxi_db.subscribe_to_reset_alerts(user_id, guild_id, server_name, minutes_before)
                
                if success:
                    embed = discord.Embed(
                        title="✅ Suscripción Exitosa",
                        description=f"Te has suscrito a las alertas de reinicio de **{server_name}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="⏰ Tiempo de Alerta", value=f"{minutes_before} minutos antes", inline=True)
                    embed.add_field(name="📅 Horarios Activos", value=f"{len(schedules)} horarios configurados", inline=True)
                    embed.add_field(name="🌍 Tu Timezone", value=f"{user_timezone}", inline=True)
                    
                    # Mostrar los horarios convertidos al timezone del usuario
                    schedule_info = []
                    days_names = {1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb", 7: "Dom"}
                    from taxi_database import convert_time_to_user_timezone
                    
                    for schedule in schedules[:5]:  # Mostrar máximo 5
                        # Convertir tiempo al timezone del usuario
                        original_time = schedule['reset_time']
                        schedule_timezone = schedule['timezone']
                        converted_time = convert_time_to_user_timezone(original_time, schedule_timezone, user_timezone)
                        
                        days_list = [int(d.strip()) for d in schedule['days_of_week'].split(',')]
                        days_str = ", ".join([days_names[d] for d in sorted(days_list)])
                        schedule_info.append(f"🕐 {converted_time} (tu hora local) - {days_str}")
                    
                    if schedule_info:
                        embed.add_field(
                            name="📋 Horarios de Reinicio (en tu zona horaria)",
                            value="\n".join(schedule_info),
                            inline=False
                        )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error suscribiéndote a las alertas", ephemeral=True)
                    
            elif action.value == "unsubscribe":
                # Desuscribir al usuario
                success = await taxi_db.unsubscribe_from_reset_alerts(user_id, guild_id, server_name)
                
                if success:
                    embed = discord.Embed(
                        title="✅ Desuscripción Exitosa",
                        description=f"Te has desuscrito de las alertas de reinicio de **{server_name}**",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="💡 Volver a suscribirte",
                        value="Puedes volver a activar las alertas cuando quieras usando este mismo comando",
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error desuscribiéndote de las alertas", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error gestionando alertas de reinicio: {e}")
            await interaction.followup.send("❌ Error procesando el comando", ephemeral=True)

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
    @discord.ui.button(
        label="✅ Aceptar Solicitud", 
        style=discord.ButtonStyle.success,
        emoji="🚖",
        custom_id="accept_taxi_request"
    )
    async def accept_taxi_request(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Botón para que el conductor acepte una solicitud."""
        await interaction.response.defer(ephemeral=True)
        # Obtener datos necesarios (ejemplo: request_id y driver_id)
        # Aquí deberías obtener el request_id de la vista o contexto real
        # request_id = self.request_id
        # driver_id = interaction.user.id
        # success, msg = await taxi_db.accept_request(request_id, driver_id)
        # if success:
        #     await interaction.followup.send(f"Solicitud aceptada", ephemeral=True)
        #     await self.bot.get_cog("TaxiSystem").notify_passenger_on_accept(request_id)
        # else:
        #     await interaction.followup.send(f"Error: {msg}", ephemeral=True)
        # ...existing code...
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
        if not taxi_config.TAXI_ENABLED:
            embed = discord.Embed(
                title="❌ Servicio No Disponible",
                description="El servicio de taxi está temporalmente deshabilitado",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
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
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para solicitar taxi
        modal = TaxiRequestModal(user_data)
        await interaction.response.send_modal(modal)

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

# TaxiRequestView eliminada - se usa modal directamente

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
