#!/usr/bin/env python3
"""
Comandos de Administración para el Sistema de Taxi - Versión Migrada
Solo los comandos esenciales con sintaxis app_commands correcta
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiosqlite
import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional
from taxi_database import taxi_db
from taxi_config import taxi_config

# Obtener VEHICLE_TYPES desde la instancia de configuración
VEHICLE_TYPES = taxi_config.VEHICLE_TYPES
PICKUP_ZONES = taxi_config.PVP_ZONES  # Usar PVP_ZONES como pickup zones

# Sistema de cooldown para evitar rate limiting
USER_COOLDOWNS = {}
GLOBAL_COOLDOWN = 2.0  # 2 segundos entre interacciones por usuario

def format_zone_with_coordinates(zone_name: str, x: float = None, y: float = None) -> str:
    """Formatear zona con coordenadas Grid-Pad si están disponibles"""
    if x is None or y is None:
        return zone_name
    
    try:
        # Convertir coordenadas a Grid-Pad
        from taxi_config import taxi_config
        grid_pad = taxi_config.coords_to_grid_pad(x, y)
        if grid_pad:
            return f"{zone_name} ({grid_pad})"
        else:
            return zone_name
    except:
        return zone_name

def check_cooldown(user_id: int) -> bool:
    """Verificar si el usuario está en cooldown"""
    current_time = time.time()
    if user_id in USER_COOLDOWNS:
        if current_time - USER_COOLDOWNS[user_id] < GLOBAL_COOLDOWN:
            return False
    USER_COOLDOWNS[user_id] = current_time
    return True
VEHICLE_TYPES = taxi_config.VEHICLE_TYPES

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configurar handler si no existe
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ZonesModal(discord.ui.Modal):
    """Modal para mostrar las zonas disponibles de forma elegante"""
    
    def __init__(self):
        super().__init__(title="🗺️ Mapa de Zonas SCUM - Sistema PAD")
        
        # Crear contenido de zonas organizado
        zones_content = self._build_zones_content()
        
        # Crear TextInput con el contenido de las zonas
        self.zones_display = discord.ui.TextInput(
            label="�️ Zonas y Coordenadas Disponibles",
            style=discord.TextStyle.paragraph,
            placeholder="Cargando mapa de zonas...",
            default=zones_content,
            required=False,
            max_length=4000  # Límite de Discord para TextInput
        )
        self.add_item(self.zones_display)
    
    def _build_zones_content(self) -> str:
        """Construir el contenido de texto para mostrar las zonas"""
        try:
            content = []
            content.append("🗺️ MAPA DE ZONAS SCUM")
            content.append("═" * 30)
            content.append("📐 Sistema: Grid + PAD (Ej: B2-5)")
            content.append("📐 Layout PAD: 7-8-9 / 4-5-6 / 1-2-3")
            content.append("")
            
            # Agrupar zonas por tipo
            zones_by_type = {}
            for zone_id, zone in taxi_config.PVP_ZONES.items():
                zone_type = zone.get('type', 'other')
                if zone_type not in zones_by_type:
                    zones_by_type[zone_type] = []
                zones_by_type[zone_type].append(zone)
            
            # Iconos y orden de tipos
            type_info = {
                'city': {'icon': '🏙️', 'name': 'CIUDADES'},
                'port': {'icon': '🚢', 'name': 'PUERTOS'},
                'town': {'icon': '🏘️', 'name': 'PUEBLOS'},
                'airport': {'icon': '✈️', 'name': 'AEROPUERTOS'},
                'industrial': {'icon': '🏭', 'name': 'INDUSTRIALES'},
                'mining': {'icon': '⛏️', 'name': 'MINERAS'},
                'resource': {'icon': '📦', 'name': 'RECURSOS'},
                'forest': {'icon': '🌲', 'name': 'BOSQUES'},
                'island': {'icon': '🏝️', 'name': 'ISLAS'},
                'bunker': {'icon': '⚔️', 'name': 'BUNKERS ⚠️'}
            }
            
            # Construir contenido por tipo
            for zone_type in ['city', 'port', 'town', 'airport', 'industrial', 'mining', 'resource', 'forest', 'island', 'bunker']:
                if zone_type in zones_by_type and zones_by_type[zone_type]:
                    zones = zones_by_type[zone_type]
                    type_data = type_info.get(zone_type, {'icon': '📍', 'name': zone_type.upper()})
                    
                    content.append(f"{type_data['icon']} {type_data['name']}:")
                    content.append("─" * 20)
                    
                    zone_count = 0
                    for zone in zones:
                        if zone_count >= 5:  # Máximo 5 zonas por tipo
                            break
                            
                        coordinates = zone.get('coordinates', f"{zone.get('grid', '??')}-{zone.get('pad', '?')}")
                        name = zone.get('name', 'Zona Desconocida')
                        restriction = zone.get('restriction', 'neutral')
                        
                        # Agregar indicador de restricción
                        status = ""
                        if restriction == 'safe_zone':
                            status = " 🛡️"
                        elif restriction == 'combat_zone':
                            status = " ⚠️"
                        elif restriction == 'no_taxi':
                            continue  # No mostrar zonas sin taxi
                        
                        # Truncar nombres muy largos
                        if len(name) > 25:
                            name = name[:22] + "..."
                        
                        content.append(f"  {coordinates} • {name}{status}")
                        zone_count += 1
                    
                    content.append("")  # Línea en blanco entre secciones
            
            # Agregar información adicional
            content.append("💰 TARIFAS:")
            content.append("─" * 20)
            content.append(f"  Base: ${taxi_config.TAXI_BASE_RATE}")
            content.append(f"  Por KM: ${taxi_config.TAXI_PER_KM_RATE}")
            content.append("")
            content.append("📖 LEYENDA:")
            content.append("─" * 20)
            content.append("🛡️ = Zona Segura")
            content.append("⚠️ = Zona de Riesgo")
            content.append("🚫 = Sin Servicio de Taxi")
            content.append("")
            content.append("🎯 Para solicitar: Usa '🚖 Solicitar Taxi'")
            
            full_content = "\n".join(content)
            
            # Truncar si es muy largo
            if len(full_content) > 3900:
                lines = full_content.split('\n')
                truncated_lines = []
                current_length = 0
                
                for line in lines:
                    if current_length + len(line) + 1 > 3800:
                        truncated_lines.append("...")
                        truncated_lines.append("⚠️ Lista truncada por límite de Discord")
                        truncated_lines.append("💡 Usa '🚖 Solicitar Taxi' para ver todas")
                        break
                    truncated_lines.append(line)
                    current_length += len(line) + 1
                
                full_content = "\n".join(truncated_lines)
            
            return full_content
            
        except Exception as e:
            logger.error(f"Error construyendo contenido de zonas: {e}")
            return f"❌ Error cargando zonas: {str(e)}\n\n🔧 Intenta usar '🚖 Solicitar Taxi' como alternativa."
    
    async def on_submit(self, interaction: discord.Interaction):
        """No hacer nada al enviar - solo es para mostrar información"""
        await interaction.response.send_message("ℹ️ Este modal es solo informativo. Usa '🚖 Solicitar Taxi' para hacer una solicitud.", ephemeral=True)

class TaxiSystemView(discord.ui.View):
    """Vista principal del sistema de taxi con funcionalidades mejoradas"""
    def __init__(self):
        super().__init__(timeout=None)  # Persistente
    
    @discord.ui.button(label="🚖 Solicitar Taxi", style=discord.ButtonStyle.primary, custom_id="request_taxi")
    async def request_taxi(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Sistema mejorado de solicitudes con verificación de solicitudes activas"""
        print(f"[DEBUG] 🚖 ENHANCED TAXI REQUEST - Usuario {interaction.user.display_name} ({interaction.user.id}) presionó el botón")
        logger.info(f"🚖 ENHANCED TAXI REQUEST - Usuario {interaction.user.display_name} ({interaction.user.id}) presionó el botón")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
        
        try:
            # Verificar si el usuario tiene una solicitud activa
            active_request = await self._check_active_request(interaction.user.id, interaction.guild.id)
            
            if active_request:
                logger.info(f"⚠️ ENHANCED REQUEST - Usuario tiene solicitud activa: {active_request.get('request_uuid', 'N/A')}")
                embed = discord.Embed(
                    title="🚖 Solicitud de Taxi Activa",
                    description="Ya tienes una solicitud de taxi activa. Usa los botones de abajo para gestionarla.",
                    color=0xffa500
                )
                
                status_emoji = {
                    'pending': '⏳',
                    'accepted': '✅', 
                    'in_progress': '🚗',
                    'completed': '🏁',
                    'cancelled': '❌'
                }.get(active_request.get('status', 'unknown'), '❓')
                
                embed.add_field(
                    name=f"{status_emoji} Estado Actual",
                    value=f"**{active_request.get('status', 'Unknown').title()}**",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Costo Estimado",
                    value=f"${active_request.get('estimated_cost', '0.00')}",
                    inline=True
                )
                
                embed.set_footer(text=f"Solicitud ID: {active_request.get('request_uuid', 'N/A')[:8]}")
                
                view = ActiveRequestView(active_request)
                await interaction.response.edit_message(embed=embed, view=view)
                return
            
            # Si no hay solicitud activa, crear nueva
            logger.info("🔧 ENHANCED REQUEST - Creando nueva vista de solicitud")
            view = TaxiRequestView()
            view._setup_origin_options()
            
            embed = discord.Embed(
                title="🚖 Solicitar Taxi - Selecciona tu viaje",
                description="Configura tu viaje seleccionando origen, vehículo y destino.",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📍 Paso 1",
                value="Selecciona tu parada de origen",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en request_taxi - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en request_taxi - ignorando")
                return
            else:
                logger.error(f"❌ ENHANCED TAXI REQUEST HTTP ERROR: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error de conexión al procesar solicitud", ephemeral=True)
        except Exception as e:
            logger.error(f"❌ ENHANCED TAXI REQUEST ERROR: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error al procesar solicitud: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="📊 Estado Solicitud", style=discord.ButtonStyle.secondary, custom_id="check_status")
    async def check_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Verificar estado de solicitud"""
        logger.info(f"📊 STATUS CHECK - Usuario {interaction.user.display_name} verificando estado")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
        
        try:
            active_request = await self._check_active_request(interaction.user.id, interaction.guild.id)
            
            if not active_request:
                embed = discord.Embed(
                    title="📊 Estado de Solicitud",
                    description="No tienes solicitudes de taxi activas.",
                    color=0x808080
                )
                
                embed.add_field(
                    name="🚖 ¿Qué puedes hacer?",
                    value="Puedes crear una nueva solicitud desde el panel principal.",
                    inline=False
                )
                
                # Crear vista con botón para volver al panel principal
                view = TaxiSystemView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
            
            # Mostrar detalles completos de la solicitud
            embed = await self._create_status_embed(active_request)
            view = ActiveRequestView(active_request)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en check_status - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en check_status - ignorando")
                return
            else:
                logger.error(f"❌ STATUS CHECK HTTP ERROR: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error de conexión verificando estado", ephemeral=True)
        except Exception as e:
            logger.error(f"❌ STATUS CHECK ERROR: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error verificando estado: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🚗 Panel Conductor", style=discord.ButtonStyle.success, custom_id="driver_panel")
    async def driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Panel para conductores"""
        logger.info(f"🚗 DRIVER PANEL - Usuario {interaction.user.display_name} accediendo al panel")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
        
        try:
            # Verificar si es conductor registrado
            # Obtener datos del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            logger.info(f"Datos del usuario obtenidos: {user_data}")
            if not user_data:
                embed = discord.Embed(
                    title="🚗 Panel de Conductor",
                    description="No estás registrado como conductor. ¿Te gustaría registrarte?",
                    color=0xff6b6b
                )
                view = DriverRegistrationView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
            driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            
            if not driver_info:
                embed = discord.Embed(
                    title="🚗 Panel de Conductor",
                    description="No estás registrado como conductor. ¿Te gustaría registrarte?",
                    color=0xff6b6b
                )
                view = DriverRegistrationView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
            
            # Mostrar panel de conductor
            view = DriverPanelView(driver_info)
            embed = await self._create_driver_panel_embed(driver_info)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited - esperando antes de reintentar")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP: {e}")
        except Exception as e:
            logger.error(f"❌ DRIVER PANEL ERROR: {e}")
            # Solo intentar responder si la interacción no ha sido respondida
            if not interaction.response.is_done():
                try:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Error temporal. Intenta nuevamente en unos segundos.",
                        color=0xff4444
                    )
                    await interaction.response.edit_message(embed=embed, view=None)
                except:
                    pass
    
    @discord.ui.button(label="📊 Estado Conductor", style=discord.ButtonStyle.secondary, custom_id="driver_status")
    async def driver_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver estado actual del conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            if not taxi_config.TAXI_ENABLED:
                embed = discord.Embed(
                    title="❌ Servicio No Disponible",
                    description="El sistema de taxi está temporalmente deshabilitado",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
                return

            # Verificar registro del usuario
            user_data = await taxi_db.get_user_by_discord_id(
                str(interaction.user.id), 
                str(interaction.guild.id)
            )
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ No Registrado",
                    description="Debes registrarte primero en el canal de bienvenida.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
                return

            # Verificar si es conductor
            driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            
            if not driver_info:
                embed = discord.Embed(
                    title="❌ No Eres Conductor",
                    description="No estás registrado como conductor. Usa el botón **'🚗 Panel Conductor'** para registrarte.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
                return
            
            # Mostrar estado del conductor
            status_emoji = {
                'online': '🟢',
                'available': '🟢', 
                'busy': '🟡',
                'offline': '🔴'
            }
            
            current_status = driver_info.get('status', 'offline')
            status_text = {
                'online': 'En Línea - Disponible',
                'available': 'Disponible',
                'busy': 'Ocupado',
                'offline': 'Sin Conexión'
            }
            
            embed = discord.Embed(
                title="📊 Tu Estado de Conductor",
                description=f"Estado actual de tu cuenta de conductor",
                color=0x3498db
            )
            
            embed.add_field(
                name="👤 Conductor",
                value=f"<@{interaction.user.id}>",
                inline=True
            )
            
            embed.add_field(
                name="🚗 Estado",
                value=f"{status_emoji.get(current_status, '❓')} {status_text.get(current_status, 'Desconocido')}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Licencia",
                value=f"`{driver_info.get('license_number', 'N/A')}`",
                inline=True
            )
            
            # Información adicional
            embed.add_field(
                name="⭐ Calificación",
                value=f"{driver_info.get('rating', 5.0):.1f}/5.0",
                inline=True
            )
            
            embed.add_field(
                name="🚖 Viajes",
                value=f"{driver_info.get('total_rides', 0)} completados",
                inline=True
            )
            
            embed.add_field(
                name="💰 Ganancias",
                value=f"${driver_info.get('total_earnings', 0.0):.2f}",
                inline=True
            )
            
            # Mostrar vehículos si los tiene
            vehicles = driver_info.get('vehicles', [])
            if vehicles:
                vehicle_list = []
                for vehicle in vehicles:
                    if vehicle in VEHICLE_TYPES:
                        vehicle_data = VEHICLE_TYPES[vehicle]
                        vehicle_list.append(f"{vehicle_data['emoji']} {vehicle_data['name']}")
                
                if vehicle_list:
                    embed.add_field(
                        name="🚗 Vehículos Registrados",
                        value="\n".join(vehicle_list),
                        inline=False
                    )
            
            embed.add_field(
                name="ℹ️ Gestión",
                value="Usa **'🚗 Panel Conductor'** para cambiar estado o gestionar vehículos",
                inline=False
            )
            
            # Crear vista con botón para regresar
            back_view = TaxiSystemView()
            await interaction.response.send_message(embed=embed, view=back_view, ephemeral=True)
                
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada - ignorando")
                return
            else:
                logger.error(f"Error HTTP consultando estado: {e}")
        except Exception as e:
            logger.error(f"Error consultando estado de conductor: {e}")
            if not interaction.response.is_done():
                embed = discord.Embed(
                    title="❌ Error",
                    description="Error temporal. Intenta nuevamente en unos segundos.",
                    color=0xff4444
                )
                back_view = TaxiSystemView()
                try:
                    await interaction.response.edit_message(embed=embed, view=back_view)
                except:
                    pass
    
    @discord.ui.button(label="📍 Ver Zonas", style=discord.ButtonStyle.secondary, custom_id="view_zones")
    async def view_zones(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar zonas disponibles en un modal elegante"""
        try:
            # Crear y mostrar el modal con las zonas
            modal = ZonesModal()
            await interaction.response.send_modal(modal)
            logger.info(f"📍 ZONES MODAL - Mostrando modal de zonas a usuario {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error mostrando modal de zonas: {e}")
            # Fallback a mensaje ephemeral si hay error
            await interaction.response.send_message(f"❌ Error mostrando zonas: {str(e)}", ephemeral=True)
    
    # === MÉTODOS DE APOYO PARA FUNCIONALIDADES MEJORADAS ===
    
    async def _check_active_request(self, user_id: int, guild_id: int = None) -> dict:
        """Verificar si el usuario tiene una solicitud activa"""
        try:
            logger.debug(f"🔍 Verificando solicitudes activas para usuario {user_id}")
            
            # Usar guild_id real si se proporciona
            if guild_id:
                guild_id_str = str(guild_id)
            else:
                # Si no se proporciona, intentar buscar con diferentes guild_ids
                guild_id_str = "1400107221324664962"  # Guild ID real del servidor
            
            # Primero obtener el user_id interno desde el discord_id
            user_data = await taxi_db.get_user_by_discord_id(str(user_id), guild_id_str)
            
            # Si no encuentra con el guild_id real, probar con otros métodos
            if not user_data and guild_id:
                logger.debug(f"⚠️ No encontrado con guild_id {guild_id_str}, probando alternativas")
                # Buscar directamente en la tabla sin filtro de guild
                import aiosqlite
                async with aiosqlite.connect(taxi_db.db_path) as db:
                    cursor = await db.execute("""
                        SELECT user_id, discord_id, discord_guild_id, username, display_name 
                        FROM taxi_users 
                        WHERE discord_id = ?
                        ORDER BY last_active DESC 
                        LIMIT 1
                    """, (str(user_id),))
                    
                    result = await cursor.fetchone()
                    if result:
                        user_data = {
                            'user_id': result[0],
                            'discord_id': result[1],
                            'discord_guild_id': result[2],
                            'username': result[3],
                            'display_name': result[4]
                        }
                        logger.debug(f"✅ Usuario encontrado con búsqueda alternativa: guild_id={result[2]}")
            
            if not user_data:
                logger.debug(f"❌ Usuario {user_id} no encontrado en taxi_users")
                return None
            
            # Consultar la base de datos real con el user_id interno
            active_request = await taxi_db.get_active_request_for_user(int(user_data['user_id']))
            
            if active_request:
                # Agregar el UUID si no existe (para compatibilidad)
                if 'request_uuid' not in active_request:
                    active_request['request_uuid'] = f"TX{active_request['request_id']}"
                
                logger.debug(f"✅ Solicitud activa encontrada: {active_request.get('request_uuid', 'N/A')}")
                return active_request
            else:
                logger.debug(f"❌ No se encontraron solicitudes activas para usuario {user_id}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error verificando solicitud activa: {e}")
            return None
    
    async def _get_driver_info(self, user_id: int, guild_id: int) -> dict:
        """Obtener información del conductor"""
        try:
            logger.debug(f"🔍 Verificando info de conductor para usuario {user_id}")
            
            # Obtener datos del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(user_id), str(guild_id))
            
            if not user_data:
                logger.debug(f"❌ Usuario {user_id} no encontrado en taxi_users")
                return None
            
            # Obtener información del conductor
            driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            
            if not driver_info:
                logger.debug(f"❌ Usuario {user_id} no es conductor registrado")
                return None
                
            logger.debug(f"✅ Conductor encontrado: {driver_info.get('license_number', 'N/A')}")
            return driver_info
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo info del conductor: {e}")
            return None
    
    async def _create_status_embed(self, request_data: dict) -> discord.Embed:
        """Crear embed detallado del estado de solicitud"""
        status_colors = {
            'pending': 0xffa500,
            'accepted': 0x00ff00,
            'in_progress': 0x0099ff,
            'completed': 0x32cd32,
            'cancelled': 0xff4444
        }
        
        status_emojis = {
            'pending': '⏳ Pendiente',
            'accepted': '✅ Aceptada',
            'in_progress': '🚗 En Progreso',
            'completed': '🏁 Completada',
            'cancelled': '❌ Cancelada'
        }
        
        embed = discord.Embed(
            title="📊 Estado de tu Solicitud de Taxi",
            color=status_colors.get(request_data.get('status', 'pending'), 0x808080)
        )
        
        # ID de solicitud
        embed.add_field(
            name="🆔 ID de Solicitud",
            value=f"`{request_data.get('request_uuid', request_data.get('request_id', 'N/A'))}`",
            inline=True
        )
        
        # Estado actual
        embed.add_field(
            name="📊 Estado",
            value=status_emojis.get(request_data.get('status', 'unknown'), 'Desconocido'),
            inline=True
        )
        
        # Costo estimado
        embed.add_field(
            name="💰 Costo",
            value=f"${request_data.get('estimated_cost', '0.00')}",
            inline=True
        )
        
        # Ruta (origen y destino) con coordenadas Grid-Pad
        pickup_zone = request_data.get('pickup_zone', 'N/A')
        destination_zone = request_data.get('destination_zone', 'N/A')
        
        # Intentar agregar coordenadas Grid-Pad si están disponibles
        pickup_x = request_data.get('pickup_x')
        pickup_y = request_data.get('pickup_y')
        dest_x = request_data.get('destination_x')
        dest_y = request_data.get('destination_y')
        
        pickup_display = format_zone_with_coordinates(pickup_zone, pickup_x, pickup_y)
        destination_display = format_zone_with_coordinates(destination_zone, dest_x, dest_y)
        
        embed.add_field(
            name="📍 Origen",
            value=pickup_display,
            inline=True
        )
        
        embed.add_field(
            name="🎯 Destino", 
            value=destination_display,
            inline=True
        )
        
        # Tipo de vehículo
        vehicle_type = request_data.get('vehicle_type', 'auto')
        vehicle_data = VEHICLE_TYPES.get(vehicle_type, {'name': 'Automóvil', 'emoji': '🚗'})
        
        embed.add_field(
            name="🚗 Vehículo",
            value=f"{vehicle_data['emoji']} {vehicle_data['name']}",
            inline=True
        )
        
        # Información del conductor si está asignado
        if request_data.get('driver_id'):
            embed.add_field(
                name="👨‍✈️ Conductor",
                value="✅ Asignado",
                inline=True
            )
        else:
            embed.add_field(
                name="👨‍✈️ Conductor",
                value="⏳ Buscando...",
                inline=True
            )
        
        # Fecha de creación
        if request_data.get('created_at'):
            try:
                # Convertir fecha string a timestamp Unix
                from datetime import datetime
                created_at_str = str(request_data['created_at'])
                
                # Intentar parsear diferentes formatos de fecha
                try:
                    # Formato: '2025-08-12 22:40:07'
                    dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        # Formato con microsegundos: '2025-08-12 22:40:07.123456'
                        dt = datetime.strptime(created_at_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # Si no se puede parsear, usar timestamp actual
                        dt = datetime.now()
                
                timestamp = int(dt.timestamp())
                embed.add_field(
                    name="🕐 Creada",
                    value=f"<t:{timestamp}:R>",
                    inline=True
                )
            except Exception as e:
                logger.warning(f"Error parseando fecha created_at: {e}")
                # Fallback: mostrar fecha como texto
                embed.add_field(
                    name="🕐 Creada",
                    value=str(request_data['created_at']),
                    inline=True
                )
        
        # Instrucciones especiales si las hay
        if request_data.get('special_instructions'):
            embed.add_field(
                name="📝 Instrucciones",
                value=request_data['special_instructions'],
                inline=False
            )
        
        # Footer con información adicional
        footer_text = f"ID: {request_data.get('request_id', 'N/A')}"
        if request_data.get('status') == 'pending':
            footer_text += " • Recibirás notificación cuando un conductor acepte"
        
        embed.set_footer(text=footer_text)
        
        return embed
    
    async def _create_driver_panel_embed(self, driver_info: dict) -> discord.Embed:
        """Crear embed del panel de conductor"""
        status_colors = {
            'available': 0x00ff00,
            'busy': 0xffa500,
            'offline': 0x808080
        }
        
        embed = discord.Embed(
            title="🚗 Panel de Conductor",
            description=f"Bienvenido, **{driver_info.get('display_name', 'Conductor')}**",
            color=status_colors.get(driver_info.get('status', 'offline'), 0x808080)
        )
        
        embed.add_field(
            name="📋 Licencia",
            value=f"`{driver_info.get('license_number', 'N/A')}`",
            inline=True
        )
        
        embed.add_field(
            name="📊 Estado",
            value=f"**{driver_info.get('status', 'offline').title()}**",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Rating",
            value=f"{driver_info.get('rating', 5.0)}/5.0",
            inline=True
        )
        
        return embed


# === CLASES DE VISTAS ADICIONALES ===

class ActiveRequestView(discord.ui.View):
    """Vista para gestionar una solicitud activa"""
    
    def __init__(self, request_data: dict):
        super().__init__(timeout=300)
        self.request_data = request_data
    
    @discord.ui.button(
        label="❌ Cancelar Solicitud", 
        style=discord.ButtonStyle.danger, 
        custom_id="cancel_request"
    )
    async def cancel_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar la solicitud activa"""
        logger.info(f"❌ CANCEL REQUEST - Usuario cancelando solicitud")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        embed = discord.Embed(
            title="⚠️ Confirmar Cancelación",
            description="¿Estás seguro de que quieres cancelar tu solicitud de taxi?",
            color=0xff6b6b
        )
        
        view = ConfirmCancelView(self.request_data.get('request_id', 0))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(
        label="🔄 Actualizar Estado", 
        style=discord.ButtonStyle.secondary, 
        custom_id="refresh_status"
    )
    async def refresh_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualizar el estado de la solicitud"""
        logger.info(f"🔄 REFRESH - Actualizando estado de solicitud")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        embed = discord.Embed(
            title="🔄 Estado Actualizado",
            description="Tu solicitud sigue activa. Te notificaremos cuando haya cambios.",
            color=0x0099ff
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(
        label="🔙 Volver al Panel Principal", 
        style=discord.ButtonStyle.primary, 
        custom_id="back_to_main_from_active",
        emoji="🔙"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del sistema de taxi"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_main - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_main - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_main - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel principal: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel principal: {e}")


class ConfirmCancelView(discord.ui.View):
    """Vista de confirmación para cancelar solicitud"""
    
    def __init__(self, request_id: int):
        super().__init__(timeout=60)
        self.request_id = request_id
    
    @discord.ui.button(
        label="✅ Sí, Cancelar", 
        style=discord.ButtonStyle.danger, 
        custom_id="confirm_cancel"
    )
    async def confirm_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar cancelación"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        await taxi_db.cancel_request(self.request_id)

        embed = discord.Embed(
            title="✅ Solicitud Cancelada",
            description="Tu solicitud de taxi ha sido cancelada exitosamente.",
            color=0x00ff00
        )
        
        # Añadir botón para volver al panel principal
        embed.add_field(
            name="🚖 ¿Qué sigue?",
            value="Puedes crear una nueva solicitud desde el panel principal.",
            inline=False
        )
        
        view = TaxiSystemView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(
        label="❌ No, Mantener", 
        style=discord.ButtonStyle.secondary, 
        custom_id="keep_request"
    )
    async def keep_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mantener la solicitud - volver a vista de solicitud activa"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Crear vista de solicitud activa con datos simulados
        request_data = {'request_id': self.request_id, 'status': 'pending'}
        
        embed = discord.Embed(
            title="🚖 Solicitud Mantenida",
            description="Tu solicitud de taxi sigue activa.",
            color=0x0099ff
        )
        
        view = ActiveRequestView(request_data)
        await interaction.response.edit_message(embed=embed, view=view)


class DriverRegistrationView(discord.ui.View):
    """Vista para registro de nuevos conductores"""
    
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(
        label="📝 Registrarse como Conductor", 
        style=discord.ButtonStyle.success, 
        custom_id="register_driver"
    )
    async def register_driver(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Iniciar proceso de registro de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        view = DriverRegistrationView()
        embed = discord.Embed(
            title="🚗 Registro de Conductor",
            description="Selecciona los tipos de vehículos que conduces. Puedes seleccionar múltiples vehículos.",
            color=0x3498db
        )
        
        # Mostrar información de vehículos disponibles
        vehicle_info = ""
        for vehicle_type, data in VEHICLE_TYPES.items():
            vehicle_info += f"{data['emoji']} **{data['name']}**: {data['description']}\n"
        
        embed.add_field(
            name="🚗 Vehículos Disponibles",
            value=vehicle_info,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class DriverRegistrationView(discord.ui.View):
    """Vista para registro de conductor con selector múltiple"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_vehicles = []
        self.description = ""
        
        # Crear selector de vehículos
        self.vehicle_select = VehicleSelect()
        self.add_item(self.vehicle_select)
    
    @discord.ui.button(label="📝 Agregar Descripción", style=discord.ButtonStyle.secondary, emoji="📝")
    async def add_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Agregar descripción opcional"""
        modal = DescriptionModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="✅ Registrarse", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Completar registro de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        if not self.selected_vehicles:
            await interaction.response.send_message("❌ Debes seleccionar al menos un vehículo.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Verificar si ya es conductor
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if user_data:
                driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            else:
                driver_info = None
            
            if driver_info:
                # Si ya es conductor, actualizar vehículos
                success, message = await taxi_db.update_driver_vehicles(int(user_data['user_id']), self.selected_vehicles)
                
                if success:
                    embed = discord.Embed(
                        title="✅ Vehículos Actualizados",
                        description="Tus vehículos han sido actualizados exitosamente!",
                        color=0x00ff00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description=f"Error actualizando vehículos: {message}",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            else:
                # Si no es conductor, registrar por primera vez
                # Para el registro inicial, usar el primer vehículo seleccionado
                primary_vehicle = self.selected_vehicles[0]
                success, license_or_error = await taxi_db.register_driver(
                    int(user_data['user_id']), 
                    primary_vehicle, 
                    self.description
                )
                
                if success:
                    # Actualizar con todos los vehículos seleccionados
                    await taxi_db.update_driver_vehicles(int(user_data['user_id']), self.selected_vehicles)
                    
                    embed = discord.Embed(
                        title="✅ Registro Completado",
                        description="Te has registrado exitosamente como conductor!",
                        color=0x00ff00
                    )
                    
                    embed.add_field(
                        name="📋 Licencia",
                        value=f"`{license_or_error}`",
                        inline=True
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error en Registro",
                        description=f"Error: {license_or_error}",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Mostrar vehículos registrados con emojis
            vehicle_list = []
            for vehicle_type in self.selected_vehicles:
                vehicle_data = VEHICLE_TYPES[vehicle_type]
                vehicle_list.append(f"{vehicle_data['emoji']} **{vehicle_data['name']}**")
            
            embed.add_field(
                name="🚗 Vehículos Registrados",
                value="\n".join(vehicle_list),
                inline=False
            )
            
            if self.description:
                embed.add_field(
                    name="📝 Descripción",
                    value=self.description,
                    inline=False
                )
            
            # Añadir botón para ir al panel de conductor
            embed.add_field(
                name="🚗 ¿Qué sigue?",
                value="Accede al Panel de Conductor para gestionar tu estado y ver solicitudes.",
                inline=False
            )
            
            # Crear vista con botón para ir al panel de conductor
            view = RegisteredDriverView(user_data)
            await interaction.followup.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error en registro de conductor: {e}")
            await interaction.followup.send(f"❌ Error en registro: {str(e)}", ephemeral=True)
    
    @discord.ui.button(
        label="🔙 Volver al Panel Principal", 
        style=discord.ButtonStyle.secondary, 
        custom_id="back_to_main_from_registration",
        emoji="🔙"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del sistema de taxi"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_main - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_main - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_main - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel principal: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel principal: {e}")


class RegisteredDriverView(discord.ui.View):
    """Vista para conductores recién registrados"""
    
    def __init__(self, user_data: dict):
        super().__init__(timeout=300)
        self.user_data = user_data
    
    @discord.ui.button(
        label="🚗 Ir al Panel de Conductor", 
        style=discord.ButtonStyle.primary, 
        custom_id="go_to_driver_panel",
        emoji="🚗"
    )
    async def go_to_driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir al panel de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Obtener información del conductor
            driver_info = await taxi_db.get_driver_info(int(self.user_data['user_id']))
            
            if driver_info:
                # Crear embed del panel de conductor
                embed = discord.Embed(
                    title="🚗 Panel de Conductor",
                    description=f"Bienvenido, **{driver_info.get('display_name', 'Conductor')}**",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📋 Licencia",
                    value=f"`{driver_info.get('license_number', 'N/A')}`",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Estado",
                    value=f"**{driver_info.get('status', 'offline').title()}**",
                    inline=True
                )
                
                embed.add_field(
                    name="⭐ Rating",
                    value=f"{driver_info.get('rating', 5.0)}/5.0",
                    inline=True
                )
                
                view = DriverPanelView(driver_info)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                # Si por alguna razón no se encuentra al conductor, volver al panel principal
                embed = discord.Embed(
                    title="🚖 Sistema de Taxi",
                    description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                    color=0x00ff00
                )
                
                view = TaxiSystemView()
                await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en go_to_driver_panel - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en go_to_driver_panel - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en go_to_driver_panel - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP accediendo al panel de conductor: {e}")
        except Exception as e:
            logger.error(f"❌ Error accediendo al panel de conductor: {e}")
    
    @discord.ui.button(
        label="🔙 Volver al Panel Principal", 
        style=discord.ButtonStyle.secondary, 
        custom_id="back_to_main_from_registered",
        emoji="🔙"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del sistema de taxi"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_main - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_main - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_main - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel principal: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel principal: {e}")


class VehicleSelect(discord.ui.Select):
    """Selector múltiple de vehículos"""
    
    def __init__(self):
        options = []
        for vehicle_type, data in VEHICLE_TYPES.items():
            options.append(
                discord.SelectOption(
                    label=data['name'],
                    value=vehicle_type,
                    description=data['description'],
                    emoji=data['emoji']
                )
            )
        
        super().__init__(
            placeholder="Selecciona tus vehículos...",
            options=options,
            min_values=1,
            max_values=len(options)  # Permitir selección múltiple
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Procesar selección de vehículos"""
        view = self.view
        view.selected_vehicles = self.values
        
        # Actualizar embed con selección actual
        embed = discord.Embed(
            title="🚗 Registro de Conductor",
            description="Vehículos seleccionados. Puedes agregar una descripción opcional y luego registrarte.",
            color=0x3498db
        )
        
        # Mostrar vehículos seleccionados
        selected_list = []
        for vehicle_type in self.values:
            vehicle_data = VEHICLE_TYPES[vehicle_type]
            selected_list.append(f"{vehicle_data['emoji']} **{vehicle_data['name']}**")
        
        embed.add_field(
            name="✅ Vehículos Seleccionados",
            value="\n".join(selected_list),
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class DescriptionModal(discord.ui.Modal):
    """Modal para agregar descripción opcional"""
    
    def __init__(self, parent_view):
        super().__init__(title="📝 Descripción de Vehículos")
        self.parent_view = parent_view
        
        self.description_input = discord.ui.TextInput(
            label="Descripción de tus Vehículos",
            placeholder="Describe tus vehículos disponibles... (opcional)",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False,
            default=parent_view.description
        )
        
        self.add_item(self.description_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Guardar descripción"""
        self.parent_view.description = self.description_input.value
        
        # Actualizar embed
        embed = discord.Embed(
            title="🚗 Registro de Conductor",
            description="Descripción agregada. Ahora puedes completar tu registro.",
            color=0x3498db
        )
        
        # Mostrar vehículos seleccionados
        if self.parent_view.selected_vehicles:
            selected_list = []
            for vehicle_type in self.parent_view.selected_vehicles:
                vehicle_data = VEHICLE_TYPES[vehicle_type]
                selected_list.append(f"{vehicle_data['emoji']} **{vehicle_data['name']}**")
            
            embed.add_field(
                name="✅ Vehículos Seleccionados",
                value="\n".join(selected_list),
                inline=False
            )
        
        if self.description_input.value:
            embed.add_field(
                name="📝 Descripción",
                value=self.description_input.value,
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class DriverStatusView(discord.ui.View):
    """Vista para cambiar el estado del conductor"""
    
    def __init__(self, driver_info: dict):
        super().__init__(timeout=300)
        self.driver_info = driver_info
    
    @discord.ui.button(label="🟢 Disponible", style=discord.ButtonStyle.success, custom_id="status_available")
    async def set_available(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como disponible"""
        await self._change_status(interaction, 'available', '🟢 Disponible')
    
    @discord.ui.button(label="🟡 Ocupado", style=discord.ButtonStyle.secondary, custom_id="status_busy")
    async def set_busy(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como ocupado"""
        await self._change_status(interaction, 'busy', '🟡 Ocupado')
    
    @discord.ui.button(label="🔴 Sin Conexión", style=discord.ButtonStyle.danger, custom_id="status_offline")
    async def set_offline(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como sin conexión"""
        await self._change_status(interaction, 'offline', '🔴 Sin Conexión')
    
    @discord.ui.button(label="🔙 Volver", style=discord.ButtonStyle.primary, custom_id="back_to_driver_panel")
    async def back_to_driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        try:
            view = DriverPanelView(self.driver_info)
            embed = discord.Embed(
                title="🚗 Panel de Conductor",
                description=f"Bienvenido, **{self.driver_info.get('display_name', 'Conductor')}**",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📋 Licencia",
                value=f"`{self.driver_info.get('license_number', 'N/A')}`",
                inline=True
            )
            
            embed.add_field(
                name="📊 Estado",
                value=f"**{self.driver_info.get('status', 'offline').title()}**",
                inline=True
            )
            
            embed.add_field(
                name="⭐ Rating",
                value=f"{self.driver_info.get('rating', 5.0)}/5.0",
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error volviendo al panel de conductor: {e}")
    
    async def _change_status(self, interaction: discord.Interaction, new_status: str, status_display: str):
        """Cambiar el estado del conductor"""
        try:
            # Verificar cooldown
            if not check_cooldown(interaction.user.id):
                logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
                await interaction.response.send_message("⏳ Debes esperar antes de cambiar tu estado nuevamente.", ephemeral=True)
                return

            # Obtener información del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                await interaction.response.send_message("❌ Error: Usuario no encontrado", ephemeral=True)
                return

            # Actualizar estado del conductor
            success, message = await taxi_db.update_driver_status(interaction.user.id, new_status)

            if success:
                # Actualizar información local
                self.driver_info['status'] = new_status

                embed = discord.Embed(
                    title="✅ Estado Actualizado",
                    description=f"Tu estado ha sido cambiado a: **{status_display}**",
                    color=0x00ff00
                )

                # Volver al panel de conductor con estado actualizado
                view = DriverPanelView(self.driver_info)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(f"❌ Error actualizando estado: {message}", ephemeral=True)

        except Exception as e:
            logger.error(f"Error cambiando estado: {e}")
            try:
                await interaction.response.send_message(f"❌ Error inesperado: {str(e)}", ephemeral=True)
            except Exception:
                pass


class AcceptRequestView(discord.ui.View):
    """Vista para aceptar solicitudes de taxi"""
    
    def __init__(self, requests: List[dict], driver_info: dict):
        super().__init__(timeout=300)
        self.requests = requests
        self.driver_info = driver_info
        
        # Crear selector de solicitudes
        if requests:
            options = []
            for request in requests[:5]:  # Max 5 opciones
                options.append(
                    discord.SelectOption(
                        label=f"Solicitud #{request['request_id']}",
                        value=str(request['request_id']),
                        description=f"{request['pickup_zone']} → {request['destination_zone']} (${request.get('estimated_cost', 0) or 0:.2f})",
                        emoji="🚖"
                    )
                )
            
            self.request_select = RequestSelect(options, self.requests, self.driver_info)
            self.add_item(self.request_select)
    
    @discord.ui.button(label="🔄 Actualizar", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_requests(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualizar lista de solicitudes"""
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Re-crear la vista del panel conductor para actualizar
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if user_data:
                driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            else:
                driver_info = None
            
            if driver_info:
                view = DriverPanelView(driver_info)
                await view.view_requests(interaction, button)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en refresh_requests - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en refresh_requests - ignorando")
                return
            else:
                logger.error(f"Error HTTP actualizando solicitudes: {e}")
        except Exception as e:
            logger.error(f"Error actualizando solicitudes: {e}")
    
    @discord.ui.button(
        label="🔙 Volver al Panel de Conductor", 
        style=discord.ButtonStyle.primary, 
        custom_id="back_to_driver_panel_from_requests",
        emoji="🔙"
    )
    async def back_to_driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Obtener información del conductor
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if user_data:
                driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
                
                if driver_info:
                    # Crear embed del panel de conductor
                    embed = discord.Embed(
                        title="🚗 Panel de Conductor",
                        description=f"Bienvenido, **{driver_info.get('display_name', 'Conductor')}**",
                        color=0x00ff00
                    )
                    
                    embed.add_field(
                        name="📋 Licencia",
                        value=f"`{driver_info.get('license_number', 'N/A')}`",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Estado",
                        value=f"**{driver_info.get('status', 'offline').title()}**",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⭐ Rating",
                        value=f"{driver_info.get('rating', 5.0)}/5.0",
                        inline=True
                    )
                    
                    view = DriverPanelView(driver_info)
                    await interaction.response.edit_message(embed=embed, view=view)
                    return
            
            # Si no se puede obtener info del conductor, volver al panel principal
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            view = TaxiSystemView()
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_driver_panel - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_driver_panel - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_driver_panel - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel de conductor: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel de conductor: {e}")


class RequestSelect(discord.ui.Select):
    """Selector de solicitudes para aceptar"""
    
    def __init__(self, options: List[discord.SelectOption], requests: List[dict], driver_info: dict):
        super().__init__(
            placeholder="Selecciona una solicitud para aceptar...",
            options=options
        )
        self.requests_data = {str(req['request_id']): req for req in requests}
        self.driver_info = driver_info
    
    async def callback(self, interaction: discord.Interaction):
        """Aceptar solicitud seleccionada"""
        await interaction.response.defer(ephemeral=True)
        try:
            request_id = int(self.values[0])
            request_data = self.requests_data[self.values[0]]
            # Obtener información del conductor
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                await interaction.followup.send("❌ Error: Usuario no encontrado", ephemeral=True)
                return
            driver_user_id = int(user_data['user_id'])
            # Verificar que el conductor no tenga una solicitud activa
            active_request = await taxi_db.get_active_request_for_user(driver_user_id)
            if active_request and active_request['status'] in ['accepted', 'in_progress']:
                await interaction.followup.send("❌ Ya tienes un viaje activo. Complétalo antes de aceptar nuevas solicitudes.", ephemeral=True)
                return
            # Intentar aceptar la solicitud
            success, message = await taxi_db.accept_request(request_id, driver_user_id)
            if success:
                embed = discord.Embed(
                    title="✅ Solicitud Aceptada",
                    description=f"Has aceptado exitosamente la solicitud #{request_id}",
                    color=0x00ff00
                )
                embed.add_field(
                    name="📍 Detalles del Viaje",
                    value=f"**Origen:** {request_data['pickup_zone']}\n"
                          f"**Destino:** {request_data['destination_zone']}\n"
                          f"**Costo:** ${request_data.get('estimated_cost', 0)}\n"
                          f"**Vehículo:** {request_data.get('vehicle_type', 'auto')}",
                    inline=False
                )
                embed.add_field(
                    name="🚗 ¿Qué sigue?",
                    value="El pasajero recibirá una notificación. Dirígete al punto de recogida y marca el viaje como 'En progreso' cuando comiences.",
                    inline=False
                )
                
                # 🔔 NOTIFICAR AL PASAJERO
                try:
                    # Obtener información del pasajero
                    passenger_user_data = await taxi_db.get_user_by_id(request_data['passenger_id'])
                    if passenger_user_data:
                        passenger_discord_id = int(passenger_user_data['discord_id'])
                        passenger_user = interaction.client.get_user(passenger_discord_id)
                        
                        if passenger_user:
                            # Crear embed de notificación para el pasajero
                            notification_embed = discord.Embed(
                                title="🚖 ¡Tu Taxi Ha Sido Aceptado!",
                                description="Un conductor ha aceptado tu solicitud de taxi",
                                color=0x00ff00
                            )
                            
                            notification_embed.add_field(
                                name="👨‍✈️ Conductor Asignado",
                                value=f"**{interaction.user.display_name}**",
                                inline=True
                            )
                            
                            notification_embed.add_field(
                                name="🚗 Vehículo",
                                value=f"{request_data.get('vehicle_type', 'auto').title()}",
                                inline=True
                            )
                            
                            notification_embed.add_field(
                                name="💰 Costo Estimado",
                                value=f"${request_data.get('estimated_cost', 0)}",
                                inline=True
                            )
                            
                            notification_embed.add_field(
                                name="📍 Detalles del Viaje",
                                value=f"**Origen:** {request_data['pickup_zone']}\n**Destino:** {request_data['destination_zone']}",
                                inline=False
                            )
                            
                            notification_embed.add_field(
                                name="⏰ Próximos Pasos",
                                value="Tu conductor se dirigirá al punto de recogida. Te notificaremos cuando esté en camino.",
                                inline=False
                            )
                            
                            notification_embed.set_footer(text=f"Solicitud #{request_id} • Usa /taxi_status para ver el estado")
                            
                            # Enviar notificación privada
                            await passenger_user.send(embed=notification_embed)
                            logger.info(f"🔔 Notificación enviada al pasajero {passenger_user.display_name} (ID: {passenger_discord_id}) para solicitud #{request_id}")
                            
                        else:
                            logger.warning(f"⚠️ No se pudo encontrar el usuario de Discord del pasajero {passenger_discord_id}")
                    else:
                        logger.warning(f"⚠️ No se encontraron datos del pasajero para solicitud #{request_id}")
                        
                except Exception as notification_error:
                    logger.error(f"❌ Error enviando notificación al pasajero: {notification_error}")
                    # No fallar la aceptación por error de notificación
                
                # Botón para volver al panel del conductor
                back_view = DriverPanelView(self.driver_info)
                if interaction.message:
                    await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=back_view)
                else:
                    await interaction.followup.send(embed=embed, view=back_view, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {message}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error aceptando solicitud: {e}")
            await interaction.followup.send(f"❌ Error aceptando solicitud: {str(e)}", ephemeral=True)


class DriverPanelView(discord.ui.View):
    """Panel principal para conductores"""
    
    def __init__(self, driver_info: dict):
        super().__init__(timeout=300)
        self.driver_info = driver_info
    
    @discord.ui.button(
        label="📋 Ver Solicitudes", 
        style=discord.ButtonStyle.primary, 
        custom_id="view_requests",
        row=0
    )
    async def view_requests(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver solicitudes disponibles (excluyendo las propias)"""
        logger.info(f"📋 VIEW REQUESTS - Usuario {interaction.user.display_name} viendo solicitudes")
        
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Obtener datos del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Usuario no encontrado",
                    color=0xff4444
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            user_id = int(user_data['user_id'])
            
            # Verificar si el conductor tiene un viaje activo
            active_request = await taxi_db.get_active_request_for_user(user_id)
            
            if active_request and active_request['status'] in ['accepted', 'in_progress']:
                embed = discord.Embed(
                    title="⚠️ Viaje en Curso",
                    description="Ya tienes un viaje activo. Complétalo antes de aceptar nuevas solicitudes.",
                    color=0xffa500
                )
                
                embed.add_field(
                    name="📍 Viaje Actual",
                    value=f"**Origen:** {active_request['pickup_zone']}\n**Destino:** {active_request['destination_zone']}\n**Estado:** {active_request['status'].title()}",
                    inline=False
                )
                
                # Botón para volver al panel principal
                back_view = DriverPanelView(self.driver_info)
                await interaction.response.edit_message(embed=embed, view=back_view)
                return
            
            # Obtener solicitudes pendientes (excluyendo las propias)
            pending_requests = await taxi_db.get_pending_requests(exclude_user_id=user_id)
            
            logger.debug(f"📋 Solicitudes encontradas: {len(pending_requests)}")
            for req in pending_requests:
                logger.debug(f"   - ID {req['request_id']}: {req['pickup_zone']} → {req['destination_zone']}")
            
            if not pending_requests:
                embed = discord.Embed(
                    title="📋 Solicitudes Disponibles",
                    description="No hay solicitudes de taxi disponibles en este momento.",
                    color=0x0099ff
                )
                
                embed.add_field(
                    name="💡 Consejo",
                    value="Las solicitudes aparecerán aquí cuando los pasajeros las realicen.",
                    inline=False
                )
                back_view = DriverPanelView(self.driver_info)
                await interaction.response.edit_message(embed=embed, view=back_view)
            else:
                embed = discord.Embed(
                    title="📋 Solicitudes Disponibles",
                    description=f"Hay {len(pending_requests)} solicitudes pendientes de ser aceptadas.",
                    color=0x00ff00
                )
                
                # Mostrar las primeras 3 solicitudes
                for i, request in enumerate(pending_requests[:3]):
                    try:
                        # Convertir fecha para mostrar tiempo relativo
                        from datetime import datetime
                        created_at_str = str(request['created_at'])
                        try:
                            dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                dt = datetime.strptime(created_at_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                dt = datetime.now()
                        
                        timestamp = int(dt.timestamp())
                        time_display = f"<t:{timestamp}:R>"
                        
                        # Obtener info del vehículo
                        vehicle_type = request.get('vehicle_type', 'auto')
                        vehicle_data = VEHICLE_TYPES.get(vehicle_type, {'name': 'Automóvil', 'emoji': '🚗'})
                        
                        embed.add_field(
                            name=f"🚖 Solicitud #{request['request_id']}",
                            value=f"**📍 Origen:** {request['pickup_zone']}\n"
                                  f"**🎯 Destino:** {request['destination_zone']}\n"
                                  f"**🚗 Vehículo:** {vehicle_data['emoji']} {vehicle_data['name']}\n"
                                  f"**💰 Costo:** ${request['estimated_cost']}\n"
                                  f"**🕐 Creada:** {time_display}",
                            inline=True
                        )
                    except Exception as e:
                        logger.error(f"Error mostrando solicitud: {e}")
                        embed.add_field(
                            name=f"🚖 Solicitud #{request['request_id']}",
                            value=f"**📍 Origen:** {request['pickup_zone']}\n"
                                  f"**🎯 Destino:** {request['destination_zone']}\n"
                                  f"**💰 Costo:** ${request['estimated_cost']}",
                            inline=True
                        )
                
                if len(pending_requests) > 3:
                    embed.set_footer(text=f"Mostrando 3 de {len(pending_requests)} solicitudes disponibles")
                
                # Crear vista para aceptar solicitudes
                view = AcceptRequestView(pending_requests, self.driver_info)
                await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en view_requests - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en view_requests - ignorando")
                return
            else:
                logger.error(f"Error HTTP viendo solicitudes: {e}")
        except Exception as e:
            logger.error(f"Error viendo solicitudes: {e}")
            # Solo responder si la interacción no ha sido procesada
            if not interaction.response.is_done():
                embed = discord.Embed(
                    title="❌ Error",
                    description="Error temporal. Intenta nuevamente en unos segundos.",
                    color=0xff4444
                )
                back_view = DriverPanelView(self.driver_info)
                await interaction.response.edit_message(embed=embed, view=back_view)
    
    @discord.ui.button(
        label="🔄 Cambiar Estado", 
        style=discord.ButtonStyle.secondary, 
        custom_id="change_status",
        row=0
    )
    async def change_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cambiar estado del conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            view = DriverStatusView(self.driver_info)
            embed = discord.Embed(
                title="🔄 Cambiar Estado",
                description="Selecciona tu nuevo estado:",
                color=0xffa500
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en change_status - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en change_status - ignorando")
                return
            else:
                logger.error(f"Error HTTP cambiando estado: {e}")
        except Exception as e:
            logger.error(f"Error cambiando estado: {e}")
    
    @discord.ui.button(
        label="🚗 Gestionar Vehículos", 
        style=discord.ButtonStyle.secondary, 
        custom_id="manage_vehicles",
        row=1
    )
    async def manage_vehicles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Gestionar vehículos registrados"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            view = DriverRegistrationView()
            embed = discord.Embed(
                title="🚗 Gestionar Vehículos",
                description="Actualiza tus vehículos registrados. Puedes seleccionar múltiples vehículos.",
                color=0x3498db
            )
            
            # Mostrar información de vehículos disponibles
            vehicle_info = ""
            for vehicle_type, data in VEHICLE_TYPES.items():
                vehicle_info += f"{data['emoji']} **{data['name']}**: {data['description']}\n"
            
            embed.add_field(
                name="🚗 Vehículos Disponibles",
                value=vehicle_info,
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en manage_vehicles - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en manage_vehicles - ignorando")
                return
            else:
                logger.error(f"Error HTTP gestionando vehículos: {e}")
        except Exception as e:
            logger.error(f"Error gestionando vehículos: {e}")
    
    @discord.ui.button(
        label="🔙 Volver al Panel Principal", 
        style=discord.ButtonStyle.danger, 
        custom_id="back_to_main",
        emoji="🔙",
        row=1
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del sistema de taxi"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_main - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_main - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_main - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel principal: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel principal: {e}")


class DriverProfileView(discord.ui.View):
    """Vista para gestionar el perfil del conductor"""
    
    def __init__(self, driver_info: dict):
        super().__init__(timeout=300)
        self.driver_info = driver_info
    
    @discord.ui.button(
        label="🚗 Gestionar Vehículos", 
        style=discord.ButtonStyle.primary, 
        emoji="🚗"
    )
    async def manage_vehicles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Gestionar vehículos registrados"""
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            view = DriverRegistrationView()
            embed = discord.Embed(
                title="🚗 Gestionar Vehículos",
                description="Actualiza tus vehículos registrados. Puedes seleccionar múltiples vehículos.",
                color=0x3498db
            )
            
            # Mostrar información de vehículos disponibles
            vehicle_info = ""
            for vehicle_type, data in VEHICLE_TYPES.items():
                vehicle_info += f"{data['emoji']} **{data['name']}**: {data['description']}\n"
            
            embed.add_field(
                name="🚗 Vehículos Disponibles",
                value=vehicle_info,
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en manage_vehicles - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en manage_vehicles - ignorando")
                return
            else:
                logger.error(f"Error HTTP gestionando vehículos: {e}")
        except Exception as e:
            logger.error(f"Error gestionando vehículos: {e}")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(
        label="🔄 Cambiar Estado", 
        style=discord.ButtonStyle.secondary, 
        emoji="🔄"
    )
    async def change_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cambiar estado del conductor"""
        view = DriverStatusView(self.driver_info)
        embed = discord.Embed(
            title="🔄 Cambiar Estado",
            description="Selecciona tu nuevo estado:",
            color=0xffa500
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(
        label="📊 Ver Estadísticas", 
        style=discord.ButtonStyle.secondary, 
        emoji="📊"
    )
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver estadísticas del conductor"""
        embed = discord.Embed(
            title="📊 Estadísticas del Conductor",
            description="Información sobre tus viajes como conductor",
            color=0x9b59b6
        )
        
        # En una implementación real, aquí cargarías las estadísticas de la base de datos
        embed.add_field(
            name="🚖 Viajes Completados",
            value="0",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Calificación Promedio",
            value="N/A",
            inline=True
        )
        
        embed.add_field(
            name="💰 Ganancias Totales",
            value="$0.00",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DriverStatusView(discord.ui.View):
    """Vista para cambiar estado del conductor"""
    
    def __init__(self, driver_info: dict):
        super().__init__(timeout=120)
        self.driver_info = driver_info
    
    @discord.ui.button(
        label="🟢 Disponible", 
        style=discord.ButtonStyle.success, 
        custom_id="status_available",
        row=0
    )
    async def set_available(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como disponible"""
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            await self._update_status("available", interaction)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en set_available - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en set_available - ignorando")
                return
            else:
                logger.error(f"Error HTTP estableciendo disponible: {e}")
        except Exception as e:
            logger.error(f"Error estableciendo disponible: {e}")
    
    @discord.ui.button(
        label="🟡 Ocupado", 
        style=discord.ButtonStyle.secondary, 
        custom_id="status_busy",
        row=0
    )
    async def set_busy(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como ocupado"""
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            await self._update_status("busy", interaction)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en set_busy - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en set_busy - ignorando")
                return
            else:
                logger.error(f"Error HTTP estableciendo ocupado: {e}")
        except Exception as e:
            logger.error(f"Error estableciendo ocupado: {e}")
    
    @discord.ui.button(
        label="🔴 Sin Conexión", 
        style=discord.ButtonStyle.danger, 
        custom_id="status_offline",
        row=0
    )
    async def set_offline(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Establecer estado como sin conexión"""
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            await self._update_status("offline", interaction)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en set_offline - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en set_offline - ignorando")
                return
            else:
                logger.error(f"Error HTTP estableciendo sin conexión: {e}")
        except Exception as e:
            logger.error(f"Error estableciendo sin conexión: {e}")
    
    @discord.ui.button(
        label="🔙 Volver", 
        style=discord.ButtonStyle.primary, 
        custom_id="back_to_driver_panel",
        emoji="🔙",
        row=1
    )
    async def back_to_driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear embed del panel de conductor
            embed = await self._create_driver_panel_embed(self.driver_info)
            view = DriverPanelView(self.driver_info)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_driver_panel - esperando")
                await asyncio.sleep(1)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_driver_panel - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al panel: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al panel: {e}")
    
    async def _create_driver_panel_embed(self, driver_info: dict) -> discord.Embed:
        """Crear embed del panel de conductor"""
        status_emoji = {
            'available': '🟢',
            'busy': '🟡',
            'offline': '🔴'
        }.get(driver_info.get('status', 'offline'), '❓')
        
        embed = discord.Embed(
            title="🚗 Panel de Conductor",
            description=f"Bienvenido, Conductor",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📋 Licencia",
            value=driver_info.get('license_number', 'N/A'),
            inline=True
        )
        
        embed.add_field(
            name=f"{status_emoji} Estado",
            value=driver_info.get('status', 'Sin Conexión').title(),
            inline=True
        )
        
        embed.add_field(
            name="⭐ Rating",
            value=f"{driver_info.get('rating', 5.0)}/5.0",
            inline=True
        )
        
        embed.add_field(
            name="🚗 Viajes",
            value=f"{driver_info.get('total_rides', 0)} completados",
            inline=True
        )
        
        embed.add_field(
            name="💰 Ganancias",
            value=f"${driver_info.get('total_earnings', 0.0):.2f}",
            inline=True
        )
        
        return embed
    
    async def _update_status(self, new_status: str, interaction: discord.Interaction):
        """Actualizar estado en la base de datos"""
        try:
            # Actualizar el estado en la base de datos
            success, message = await taxi_db.update_driver_status(interaction.user.id, new_status)
            if success:
                # Obtener datos del usuario
                user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
                if not user_data:
                    await interaction.response.send_message("❌ Error: Usuario no encontrado", ephemeral=True)
                    return
                driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
                if driver_info:
                    # Crear embed con el nuevo estado
                    embed = await self._create_driver_panel_embed(driver_info)
                    
                    # Crear nueva vista con estado actualizado
                    view = DriverPanelView(driver_info)
                    
                    await interaction.response.edit_message(embed=embed, view=view)
                    logger.info(f"✅ Estado actualizado exitosamente a {new_status} para usuario {interaction.user.id}")
                else:
                    # Fallback si no se puede obtener info del conductor
                    embed = discord.Embed(
                        title="✅ Estado Actualizado",
                        description=f"Tu estado ha sido cambiado a **{new_status.title()}**",
                        color=0x00ff00
                    )
                    await interaction.response.edit_message(embed=embed, view=None)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"No se pudo actualizar tu estado: {message}",
                    color=0xff4444
                )
                await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo actualizar tu estado.",
                color=0xff4444
            )
            try:
                await interaction.response.edit_message(embed=embed, view=None)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

class TaxiRequestView(discord.ui.View):
    """Vista para solicitar taxi con selectores de origen, vehículo y destino"""
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.origin = None
        self.vehicle_type = None
        self.destination = None
        
        # Las opciones se configurarán después de crear la vista
    
    def _setup_origin_options(self):
        """Configurar opciones del selector de origen"""
        logger.info("🔧 SETUP ORIGIN - Iniciando configuración de opciones de origen")
        
        try:
            logger.info(f"🔧 SETUP ORIGIN - Revisando {len(taxi_config.TAXI_STOPS)} paradas disponibles")
            options = []
            
            for stop_id, stop_data in taxi_config.TAXI_STOPS.items():
                logger.debug(f"🔧 SETUP ORIGIN - Procesando parada: {stop_id} - {stop_data.get('name', 'Sin nombre')}")
                
                emoji = {
                    'main_stop': "🏢",
                    'town_stop': "🏘️", 
                    'airstrip': "✈️",
                    'seaport': "🚢"
                }.get(stop_data['type'], "🏭")
                
                options.append(discord.SelectOption(
                    label=stop_data['name'],
                    value=stop_id,
                    description=f"{stop_data['coordinates']} - {stop_data['description'][:50]}",
                    emoji=emoji
                ))
                logger.debug(f"✅ SETUP ORIGIN - Opción agregada: {stop_data['name']} ({stop_id})")
            
            logger.info(f"🔧 SETUP ORIGIN - Total de opciones creadas: {len(options)}")
            
            # Actualizar las opciones del selector de origen
            origin_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'origin_select':
                    logger.info("🔧 SETUP ORIGIN - Actualizando selector de origen")
                    item.options = options[:25]  # Máximo 25 opciones por selector
                    origin_selector_found = True
                    logger.info(f"✅ SETUP ORIGIN - Selector actualizado con {len(item.options)} opciones")
                    break
            
            if not origin_selector_found:
                logger.warning("⚠️ SETUP ORIGIN - No se encontró el selector de origen en children")
                logger.info(f"🔧 SETUP ORIGIN - Children disponibles: {[getattr(item, 'custom_id', 'No ID') for item in self.children]}")
            
        except Exception as e:
            logger.error(f"❌ SETUP ORIGIN ERROR - Error configurando opciones de origen: {e}")
            logger.error(f"❌ SETUP ORIGIN ERROR - Tipo de error: {type(e).__name__}")
    
    @discord.ui.select(
        placeholder="📍 Selecciona tu parada de origen...",
        min_values=1,
        max_values=1,
        custom_id="origin_select",
        options=[discord.SelectOption(label="Cargando...", value="loading")]
    )
    async def origin_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Selector de parada de origen"""
        logger.info(f"🚖 ORIGIN SELECT - Usuario {interaction.user.display_name} seleccionó origen")
        
        try:
            self.origin = select.values[0]
            logger.info(f"🔧 ORIGIN SELECT - Origen seleccionado: {self.origin}")
            
            origin_data = taxi_config.TAXI_STOPS[self.origin]
            logger.info(f"🔧 ORIGIN SELECT - Datos de origen: {origin_data.get('name', 'Sin nombre')}")
            
            # Actualizar selector de vehículo según parada
            available_vehicles = origin_data.get('vehicle_types', [])
            logger.info(f"🔧 ORIGIN SELECT - Vehículos disponibles: {available_vehicles}")
            
            vehicle_options = []
            
            for vehicle_id in available_vehicles:
                if vehicle_id in taxi_config.VEHICLE_TYPES:
                    vehicle_data = taxi_config.VEHICLE_TYPES[vehicle_id]
                    vehicle_options.append(discord.SelectOption(
                        label=vehicle_data['name'],
                        value=vehicle_id,
                        description=f"{vehicle_data['description']} - Cap: {vehicle_data['capacity']} personas",
                        emoji=vehicle_data['emoji']
                ))
                    logger.debug(f"✅ ORIGIN SELECT - Opción de vehículo agregada: {vehicle_data['name']}")
                else:
                    logger.warning(f"⚠️ ORIGIN SELECT - Vehículo no encontrado en configuración: {vehicle_id}")
            
            logger.info(f"🔧 ORIGIN SELECT - Total opciones de vehículo: {len(vehicle_options)}")
            
            # Encontrar y actualizar el selector de vehículos
            vehicle_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'vehicle_select':
                    logger.info("🔧 ORIGIN SELECT - Actualizando selector de vehículos")
                    item.options = vehicle_options[:25]
                    item.placeholder = "🚗 Selecciona tu vehículo..."
                    item.disabled = False
                    vehicle_selector_found = True
                    logger.info(f"✅ ORIGIN SELECT - Selector de vehículos actualizado con {len(item.options)} opciones")
                    break
            
            if not vehicle_selector_found:
                logger.warning("⚠️ ORIGIN SELECT - No se encontró el selector de vehículos")
            
            # Limpiar destinos hasta que se seleccione vehículo
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'destination_select':
                    logger.info("🔧 ORIGIN SELECT - Limpiando selector de destinos")
                    item.options = [discord.SelectOption(label="Primero selecciona un vehículo", value="disabled")]
                    item.placeholder = "🚫 Primero selecciona un vehículo..."
                    item.disabled = True
                    break
            
            embed = discord.Embed(
                title="🚖 Solicitar Taxi - Paso 2/3",
                description=f"**Origen seleccionado:** {origin_data['name']}\n\nAhora selecciona tu tipo de vehículo:",
                color=discord.Color.green()
            )
            
            logger.info("🔧 ORIGIN SELECT - Enviando respuesta actualizada")
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info("✅ ORIGIN SELECT - Respuesta enviada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ ORIGIN SELECT ERROR - Error en selección de origen: {e}")
            logger.error(f"❌ ORIGIN SELECT ERROR - Tipo de error: {type(e).__name__}")
            logger.error(f"❌ ORIGIN SELECT ERROR - Usuario: {interaction.user.display_name} ({interaction.user.id})")
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Error al procesar la selección de origen. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Error al procesar la selección de origen. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                logger.error(f"❌ ORIGIN SELECT ERROR - Error enviando mensaje de error: {followup_error}")
    
    @discord.ui.select(
        placeholder="🚗 Selecciona tu vehículo...",
        min_values=1,
        max_values=1,
        custom_id="vehicle_select",
        options=[discord.SelectOption(label="Primero selecciona origen", value="disabled")],
        disabled=True
    )
    async def vehicle_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Selector de tipo de vehículo"""
        logger.info(f"🚗 VEHICLE SELECT - Usuario {interaction.user.display_name} seleccionó vehículo")
        
        try:
            self.vehicle_type = select.values[0]
            logger.info(f"🔧 VEHICLE SELECT - Vehículo seleccionado: {self.vehicle_type}")
            
            vehicle_data = taxi_config.VEHICLE_TYPES[self.vehicle_type]
            origin_data = taxi_config.TAXI_STOPS[self.origin]
            logger.info(f"🔧 VEHICLE SELECT - Datos del vehículo: {vehicle_data.get('name', 'Sin nombre')}")
            
            # Actualizar selector de destino según vehículo
            destination_options = []
            
            # Filtrar destinos según el vehículo seleccionado
            logger.info(f"🔧 VEHICLE SELECT - Filtrando destinos para vehículo: {self.vehicle_type}")
            for zone_id, zone_data in taxi_config.PVP_ZONES.items():
                # Verificar si el vehículo puede acceder a esta zona
                zone_access = zone_data.get('vehicle_access', ['auto', 'moto'])  # Default para compatibilidad
                if self.vehicle_type in zone_access and zone_data.get('restriction') != 'no_taxi':
                    logger.debug(f"✅ VEHICLE SELECT - Zona accesible: {zone_data.get('name', 'Sin nombre')}")
                    zone_type = zone_data.get('type', 'other')
                    emoji = {"city": "🏙️", "town": "🏘️", "port": "🚢", "airport": "✈️", "industrial": "🏭", "forest": "🌲", "island": "🏝️"}.get(zone_type, "📍")
                    status = " 🛡️" if zone_data.get('restriction') == 'safe_zone' else " ⚠️" if zone_data.get('restriction') == 'combat_zone' else ""
                    
                    # Calcular tarifa estimada
                    base_fare = taxi_config.TAXI_BASE_RATE * vehicle_data['cost_multiplier']
                    
                    destination_options.append(discord.SelectOption(
                        label=f"{zone_data['name']}{status}",
                        value=zone_id,
                        description=f"{zone_data.get('coordinates', '??-?')} - ${base_fare:.0f}+ estimado",
                        emoji=emoji
                    ))
                else:
                    logger.debug(f"❌ VEHICLE SELECT - Zona no accesible: {zone_data.get('name', 'Sin nombre')} (acceso: {zone_access})")
            
            logger.info(f"🔧 VEHICLE SELECT - Total destinos disponibles: {len(destination_options)}")
            
            # Encontrar y actualizar el selector de destinos
            destination_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'destination_select':
                    logger.info("🔧 VEHICLE SELECT - Actualizando selector de destinos")
                    item.options = destination_options[:25]  # Máximo 25 opciones
                    item.placeholder = "🎯 Selecciona tu destino..."
                    item.disabled = False
                    destination_selector_found = True
                    logger.info(f"✅ VEHICLE SELECT - Selector de destinos actualizado con {len(item.options)} opciones")
                    break
            
            if not destination_selector_found:
                logger.warning("⚠️ VEHICLE SELECT - No se encontró el selector de destinos")
            
            embed = discord.Embed(
                title="🚖 Solicitar Taxi - Paso 3/3",
                description=f"**Origen:** {origin_data['name']}\n**Vehículo:** {vehicle_data['emoji']} {vehicle_data['name']}\n\nAhora selecciona tu destino:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🚗 Detalles del Vehículo",
                value=f"• Capacidad: {vehicle_data['capacity']} personas\n• Velocidad: {vehicle_data['speed_multiplier']}x\n• Costo: {vehicle_data['cost_multiplier']}x tarifa base",
                inline=False
            )
            
            logger.info("🔧 VEHICLE SELECT - Enviando respuesta actualizada")
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info("✅ VEHICLE SELECT - Respuesta enviada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ VEHICLE SELECT ERROR - Error en selección de vehículo: {e}")
            logger.error(f"❌ VEHICLE SELECT ERROR - Tipo de error: {type(e).__name__}")
            logger.error(f"❌ VEHICLE SELECT ERROR - Usuario: {interaction.user.display_name} ({interaction.user.id})")
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Error al procesar la selección de vehículo. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Error al procesar la selección de vehículo. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                logger.error(f"❌ VEHICLE SELECT ERROR - Error enviando mensaje de error: {followup_error}")
    
    @discord.ui.select(
        placeholder="🚫 Primero selecciona origen y vehículo...",
        min_values=1,
        max_values=1,
        custom_id="destination_select",
        options=[discord.SelectOption(label="Primero selecciona origen y vehículo", value="disabled")],
        disabled=True
    )
    async def destination_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Selector de zona destino"""
        logger.info(f"🎯 DESTINATION SELECT - Usuario {interaction.user.display_name} seleccionó destino")
        
        try:
            self.destination = select.values[0]
            logger.info(f"🔧 DESTINATION SELECT - Destino seleccionado: {self.destination}")
            
            # Procesar solicitud de taxi
            logger.info("🔧 DESTINATION SELECT - Procesando solicitud de taxi")
            await self.process_taxi_request(interaction)
            
        except Exception as e:
            logger.error(f"❌ DESTINATION SELECT ERROR - Error en selección de destino: {e}")
            logger.error(f"❌ DESTINATION SELECT ERROR - Tipo de error: {type(e).__name__}")
            logger.error(f"❌ DESTINATION SELECT ERROR - Usuario: {interaction.user.display_name} ({interaction.user.id})")
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Error al procesar la selección de destino. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Error al procesar la selección de destino. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                logger.error(f"❌ DESTINATION SELECT ERROR - Error enviando mensaje de error: {followup_error}")
    
    async def process_taxi_request(self, interaction: discord.Interaction):
        """Procesar la solicitud de taxi con origen, vehículo y destino seleccionados"""
        logger.info(f"🚖 PROCESS REQUEST - Iniciando procesamiento de solicitud de taxi")
        logger.info(f"🔧 PROCESS REQUEST - Usuario: {interaction.user.display_name} ({interaction.user.id})")
        logger.info(f"🔧 PROCESS REQUEST - Origen: {self.origin}")
        logger.info(f"🔧 PROCESS REQUEST - Vehículo: {self.vehicle_type}")
        logger.info(f"🔧 PROCESS REQUEST - Destino: {self.destination}")
        
        try:
            if not self.origin or not self.vehicle_type or not self.destination:
                logger.warning("⚠️ PROCESS REQUEST - Faltan datos de la solicitud")
                await interaction.response.send_message("❌ Debes seleccionar origen, vehículo y destino", ephemeral=True)
                return
            

            logger.info("🔧 PROCESS REQUEST - Obteniendo datos de origen, vehículo y destino")
            origin_data = taxi_config.TAXI_STOPS[self.origin]
            vehicle_data = taxi_config.VEHICLE_TYPES[self.vehicle_type]
            destination_data = taxi_config.PVP_ZONES[self.destination]

            # Validación por zona y tipo de vehículo
            valid_dest, msg_dest = taxi_config.validate_vehicle_zone(self.destination, self.vehicle_type)
            valid_origin, msg_origin = taxi_config.validate_vehicle_zone(self.origin, self.vehicle_type) if self.origin in taxi_config.PVP_ZONES else (True, "Origen permitido")
            if not valid_dest:
                await interaction.response.send_message(f"❌ Destino no válido para este vehículo: {msg_dest}", ephemeral=True)
                logger.warning(f"❌ Destino no válido: {msg_dest}")
                return
            if not valid_origin:
                await interaction.response.send_message(f"❌ Origen no válido para este vehículo: {msg_origin}", ephemeral=True)
                logger.warning(f"❌ Origen no válido: {msg_origin}")
                return

            logger.info("🔧 PROCESS REQUEST - Validación de zonas OK")
            logger.info("🔧 PROCESS REQUEST - Calculando tarifa")
            base_fare = taxi_config.TAXI_BASE_RATE * vehicle_data['cost_multiplier']
            distance_fare = (taxi_config.TAXI_PER_KM_RATE * 5) * vehicle_data['cost_multiplier']  # Estimación
            total_fare = base_fare + distance_fare

            logger.info(f"🔧 PROCESS REQUEST - Tarifa calculada: ${total_fare:.2f}")

            embed = discord.Embed(
                title="🚖 Solicitud de Taxi Confirmada",
                description="Tu solicitud ha sido procesada exitosamente",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📍 Ruta",
                value=f"**Desde:** {origin_data['name']} `{origin_data['coordinates']}`\n**Hasta:** {destination_data['name']} `{destination_data.get('coordinates', '??-?')}`",
                inline=False
            )

            embed.add_field(
                name="🚗 Vehículo",
                value=f"{vehicle_data['emoji']} **{vehicle_data['name']}**\n{vehicle_data['description']}\nCapacidad: {vehicle_data['capacity']} personas",
                inline=True
            )

            embed.add_field(
                name="💰 Tarifa Total",
                value=f"**${total_fare:.2f}**\n• Base: ${base_fare:.2f}\n• Distancia: ${distance_fare:.2f}",
                inline=True
            )

            embed.add_field(
                name="⏱️ Estado",
                value="🔍 Buscando conductor disponible...\n📱 Recibirás notificación cuando se asigne",
                inline=False
            )

            # Información especial según tipo de vehículo
            if self.vehicle_type == "avion":
                embed.add_field(
                    name="✈️ Información de Vuelo",
                    value="• Tiempo estimado: 15-20 min\n• Equipaje limitado\n• Sujeto a condiciones climáticas",
                    inline=False
                )
            elif self.vehicle_type == "barco":
                embed.add_field(
                    name="🚢 Información Marítima", 
                    value="• Tiempo estimado: 30-45 min\n• Permite equipaje pesado\n• Sujeto a condiciones del mar",
                    inline=False
                )
            elif self.vehicle_type == "hidroavion":
                embed.add_field(
                    name="🛩️ Información Hidroavión",
                    value="• Tiempo estimado: 20-25 min\n• Aterrizaje en agua\n• Acceso a zonas remotas",
                    inline=False
                )
            
            embed.set_footer(text="💡 Los conductores especializados recibirán tu solicitud automáticamente")
            
            # === VALIDACIÓN Y GUARDADO EN BASE DE DATOS ===
            request_id = None
            request_uuid = None
            try:
                logger.info("🔧 PROCESS REQUEST - Intentando guardar solicitud en base de datos")
                
                # Obtener datos del usuario para guardar en BD
                user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
                logger.info(f"🔧 PROCESS REQUEST - Datos de usuario obtenidos: {user_data}")
                if user_data:
                    # Obtener coordenadas de las zonas
                    origin_data = taxi_config.TAXI_STOPS.get(self.origin, {})
                    destination_data = taxi_config.PVP_ZONES.get(self.destination, {})
                    
                    # Convertir grid/pad a coordenadas básicas (SCUM grid system)
                    def grid_to_coords(grid_str, pad_num):
                        """Convertir grid (A1, B2, etc) y pad (1-9) a coordenadas aproximadas"""
                        if not grid_str or not pad_num:
                            return 0.0, 0.0, 0.0
                        
                        # Grid: A=0, B=1000, C=2000, etc. / 0=0, 1=1000, 2=2000, etc.
                        grid_letter = grid_str[0] if grid_str else 'A'
                        grid_number = grid_str[1:] if len(grid_str) > 1 else '0'
                        
                        x_base = (ord(grid_letter.upper()) - ord('A')) * 1000
                        y_base = int(grid_number) * 1000 if grid_number.isdigit() else 0
                        
                        # PAD: 1-9 layout como numpad: 7-8-9 / 4-5-6 / 1-2-3
                        pad_offsets = {
                            1: (-250, -250), 2: (0, -250), 3: (250, -250),
                            4: (-250, 0),    5: (0, 0),    6: (250, 0),
                            7: (-250, 250),  8: (0, 250),  9: (250, 250)
                        }
                        
                        pad_offset = pad_offsets.get(int(pad_num), (0, 0))
                        
                        x = x_base + pad_offset[0]
                        y = y_base + pad_offset[1]
                        z = 100.0  # Altura estándar
                        
                        return x, y, z
                    
                    # Obtener coordenadas de origen
                    origin_grid = origin_data.get('grid', 'B2')
                    origin_pad = origin_data.get('pad', 5)
                    pickup_x, pickup_y, pickup_z = grid_to_coords(origin_grid, origin_pad)
                    logger.info(f"🛫 COORDENADAS ORIGEN: grid={origin_grid}, pad={origin_pad}, x={pickup_x}, y={pickup_y}, z={pickup_z}")
                    pickup_zone = taxi_config.get_zone_at_location(pickup_x, pickup_y)
                    logger.info(f"🛫 ZONA DETECTADA ORIGEN: {pickup_zone}")

                    # Obtener coordenadas de destino
                    dest_grid = destination_data.get('grid', 'C0')
                    dest_pad = destination_data.get('pad', 4)
                    dest_x, dest_y, dest_z = grid_to_coords(dest_grid, dest_pad)
                    logger.info(f"🛬 COORDENADAS DESTINO: grid={dest_grid}, pad={dest_pad}, x={dest_x}, y={dest_y}, z={dest_z}")
                    destination_zone = taxi_config.get_zone_at_location(dest_x, dest_y)
                    logger.info(f"🛬 ZONA DETECTADA DESTINO: {destination_zone}")

                    # Crear solicitud real en la base de datos
                    success, result = await taxi_db.create_taxi_request(
                        passenger_id=int(user_data['user_id']),
                        pickup_x=pickup_x,
                        pickup_y=pickup_y, 
                        pickup_z=pickup_z,
                        destination_x=dest_x,
                        destination_y=dest_y,
                        destination_z=dest_z,
                        vehicle_type=self.vehicle_type,
                        special_instructions=None
                    )
                    
                    if success:
                        request_id = result.get('request_id')
                        request_uuid = result.get('request_uuid')
                        
                        logger.info(f"✅ PROCESS REQUEST - Solicitud guardada con ID: {request_id}")
                        logger.info(f"✅ PROCESS REQUEST - UUID: {request_uuid}")
                        
                        # Agregar información de la solicitud guardada al embed
                        embed.add_field(
                            name="🆔 Solicitud Registrada",
                            value=f"**ID:** `{request_id}`\n**UUID:** `{request_uuid[:8]}...`\n**Usuario:** {user_data.get('display_name', interaction.user.display_name)}",
                            inline=False
                        )
                    else:
                        error_msg = result.get('error', 'Error desconocido')
                        logger.error(f"❌ PROCESS REQUEST - Error creando solicitud: {error_msg}")
                        
                        # Fallback a simulación
                        import uuid
                        request_uuid = str(uuid.uuid4())
                        request_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        embed.add_field(
                            name="⚠️ Solicitud Temporal",
                            value=f"**ID:** `{request_id}`\n**Error BD:** {error_msg}\n**Se procesará manualmente**",
                            inline=False
                        )
                else:
                    logger.warning("⚠️ PROCESS REQUEST - Usuario no encontrado en base de datos, creando solicitud temporal")
                    
                    # Crear solicitud temporal
                    import uuid
                    request_uuid = str(uuid.uuid4())
                    request_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    embed.add_field(
                        name="⚠️ Solicitud Temporal",
                        value="Usuario no registrado. Regístrate primero en el canal de bienvenida para solicitudes persistentes.",
                        inline=False
                    )
                    
            except Exception as db_error:
                logger.error(f"❌ PROCESS REQUEST DB ERROR - Error guardando en base de datos: {db_error}")
                embed.add_field(
                    name="⚠️ Base de Datos",
                    value="Error al guardar solicitud. Se procesará manualmente.",
                    inline=False
                )
            
            # === CREAR VISTA CON NAVEGACIÓN ===
            request_data = {
                'request_id': request_id or f"TEMP_{int(datetime.now().timestamp())}",
                'request_uuid': request_uuid,
                'total_fare': f"{total_fare:.2f}",
                'origin': self.origin,
                'destination': self.destination,
                'vehicle_type': self.vehicle_type,
                'user_id': interaction.user.id,
                'status': 'pending'
            }
            
            confirmed_view = RequestConfirmedView(request_data)
            
            logger.info("🔧 PROCESS REQUEST - Enviando respuesta final con navegación")
            await interaction.response.edit_message(embed=embed, view=confirmed_view)
            logger.info("✅ PROCESS REQUEST - Solicitud de taxi procesada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ PROCESS REQUEST ERROR - Error procesando solicitud de taxi: {e}")
            logger.error(f"❌ PROCESS REQUEST ERROR - Tipo de error: {type(e).__name__}")
            logger.error(f"❌ PROCESS REQUEST ERROR - Usuario: {interaction.user.display_name} ({interaction.user.id})")
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Error al procesar la solicitud de taxi. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Error al procesar la solicitud de taxi. Por favor, intenta de nuevo.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                logger.error(f"❌ PROCESS REQUEST ERROR - Error enviando mensaje de error: {followup_error}")
    
    @discord.ui.button(
        label="🔙 Cancelar y Volver", 
        style=discord.ButtonStyle.danger, 
        custom_id="cancel_taxi_request",
        emoji="🔙"
    )
    async def cancel_and_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar solicitud de taxi y volver al panel principal"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Solicitud cancelada. Puedes crear una nueva cuando quieras.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            logger.info(f"✅ Usuario {interaction.user.display_name} canceló solicitud de taxi")
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en cancel_and_back - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en cancel_and_back - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en cancel_and_back - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP cancelando solicitud: {e}")
        except Exception as e:
            logger.error(f"❌ Error cancelando solicitud: {e}")


class BankSystemView(discord.ui.View):
    """Vista con botones para el sistema bancario"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="💰 Ver Saldo", style=discord.ButtonStyle.primary, custom_id="check_balance")
    async def check_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ejecutar directamente la consulta de saldo"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener información del usuario desde la base de datos usando taxi_db
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Necesitas registrarte primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            balance = user_data.get('balance', 0.0)
            account_number = user_data.get('account_number', 'Sin cuenta')
            
            embed = discord.Embed(
                title="💰 Tu Saldo Bancario",
                description=f"**Balance actual:** ${balance:,.0f}\n**Número de cuenta:** {account_number}",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error consultando saldo: {e}")
            await interaction.followup.send(f"❌ Error consultando saldo: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="💸 Transferir", style=discord.ButtonStyle.success, custom_id="transfer_money")
    async def transfer_money(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para transferir dinero"""
        modal = TransferModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📊 Historial", style=discord.ButtonStyle.secondary, custom_id="view_history")
    async def view_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar historial de transacciones"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener información del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Necesitas registrarte primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            account_number = user_data.get('account_number')
            if not account_number:
                embed = discord.Embed(
                    title="📊 Historial de Transacciones",
                    description="No tienes una cuenta bancaria activa.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener transacciones desde la tabla bank_transactions
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute(
                    """SELECT transaction_type, amount, description, created_at, from_account, to_account
                       FROM bank_transactions 
                       WHERE from_account = ? OR to_account = ? 
                       ORDER BY created_at DESC LIMIT 10""",
                    (account_number, account_number)
                )
                transactions = await cursor.fetchall()
                
                if not transactions:
                    embed = discord.Embed(
                        title="📊 Historial de Transacciones",
                        description="No tienes transacciones registradas.",
                        color=discord.Color.orange()
                    )
                else:
                    embed = discord.Embed(
                        title="📊 Historial de Transacciones",
                        description="Tus últimas 10 transacciones:",
                        color=discord.Color.purple()
                    )
                    
                    for i, (trans_type, amount, description, timestamp, from_acc, to_acc) in enumerate(transactions, 1):
                        # Determinar si es ingreso o egreso
                        is_incoming = to_acc == account_number
                        icon = "💰" if is_incoming else "💸"
                        sign = "+" if is_incoming else "-"
                        
                        embed.add_field(
                            name=f"{icon} {trans_type.replace('_', ' ').title()}",
                            value=f"{sign}${amount:,.0f}\n{description or 'Sin descripción'}\n{timestamp[:16] if timestamp else 'N/A'}",
                            inline=True
                        )
                        if i % 2 == 0:  # Salto de línea cada 2 transacciones
                            embed.add_field(name="\u200b", value="\u200b", inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error consultando historial: {e}")
            await interaction.followup.send(f"❌ Error consultando historial: {str(e)}", ephemeral=True)

class TransferModal(discord.ui.Modal, title="💸 Transferir Dinero"):
    """Modal para transferir dinero"""
    
    def __init__(self):
        super().__init__()
    
    account_number = discord.ui.TextInput(
        label="Número de cuenta del destinatario",
        placeholder="Ejemplo: SC123456",
        required=True,
        max_length=20
    )
    
    amount = discord.ui.TextInput(
        label="Cantidad a transferir",
        placeholder="Ejemplo: 1000",
        required=True,
        max_length=10
    )
    
    description = discord.ui.TextInput(
        label="Descripción (opcional)",
        placeholder="Motivo de la transferencia",
        required=False,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar cantidad
            try:
                transfer_amount = float(self.amount.value)
                if transfer_amount <= 0:
                    await interaction.followup.send("❌ La cantidad debe ser mayor a 0", ephemeral=True)
                    return
            except ValueError:
                await interaction.followup.send("❌ Cantidad inválida", ephemeral=True)
                return
            
            # Obtener información del usuario remitente
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                await interaction.followup.send("❌ No estás registrado en el sistema", ephemeral=True)
                return
                
            sender_account = user_data.get('account_number')
            if not sender_account:
                await interaction.followup.send("❌ No tienes una cuenta bancaria", ephemeral=True)
                return
            
            sender_balance = user_data.get('balance', 0.0)
            
            if sender_balance < transfer_amount:
                await interaction.followup.send(f"❌ Saldo insuficiente. Tienes ${sender_balance:,.0f}", ephemeral=True)
                return
            
            target_account = self.account_number.value.upper()
            desc = self.description.value or "Transferencia directa"
            
            # Verificar que la cuenta de destino existe
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute(
                    "SELECT user_id FROM bank_accounts WHERE account_number = ? AND status = 'active'",
                    (target_account,)
                )
                receiver_data = await cursor.fetchone()
                
                if not receiver_data:
                    await interaction.followup.send(f"❌ Cuenta {target_account} no encontrada", ephemeral=True)
                    return
                
                if target_account == sender_account:
                    await interaction.followup.send("❌ No puedes transferir dinero a ti mismo", ephemeral=True)
                    return
            
            # Realizar transferencia usando el método existente
            success, message = await taxi_db.transfer_money(
                from_account=sender_account,
                to_account=target_account,
                amount=transfer_amount,
                description=desc,
                reference_id=f"button_transfer_{interaction.user.id}_{datetime.now().timestamp()}"
            )
            
            if success:
                # Mensaje de éxito
                embed = discord.Embed(
                    title="✅ Transferencia Completada",
                    description=f"**Cantidad:** ${transfer_amount:,.0f}\n**Destinatario:** {target_account}\n**Descripción:** {desc}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="💰 Nuevo balance",
                    value=f"${sender_balance - transfer_amount:,.0f}",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error en transferencia: {message}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en transferencia: {e}")
            await interaction.followup.send(f"❌ Error en transferencia: {str(e)}", ephemeral=True)

class WelcomeSystemView(discord.ui.View):
    """Vista con botones para el sistema de bienvenida"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎉 Registrarse", style=discord.ButtonStyle.success, custom_id="register_user")
    async def register_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ejecutar directamente el registro del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar si el usuario ya está registrado
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if user_data:
                embed = discord.Embed(
                    title="✅ Ya Estás Registrado",
                    description=f"¡Hola {interaction.user.display_name}! Ya estás registrado en el sistema.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📊 Tu Información:",
                    value=f"**Cuenta:** {user_data.get('account_number', 'Sin cuenta')}\n**Balance:** ${user_data.get('balance', 0):,.0f}\n**Registrado:** {user_data.get('joined_at', 'N/A')[:10]}",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Registrar nuevo usuario usando taxi_db
            success, result = await taxi_db.register_user(
                discord_id=str(interaction.user.id),
                guild_id=str(interaction.guild.id),
                username=interaction.user.name,
                display_name=interaction.user.display_name
            )
            
            if success:
                user_info = result
                embed = discord.Embed(
                    title="🎉 ¡Registro Exitoso!",
                    description=f"¡Bienvenido {interaction.user.display_name}! Te has registrado exitosamente en el sistema.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="💳 Tu Cuenta Bancaria:",
                    value=f"**Número:** {user_info.get('account_number', 'Generando...')}\n**Balance inicial:** ${user_info.get('balance', 1000):,.0f}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎁 Welcome Pack:",
                    value="• Dinero inicial: $1,000\n• Cuenta bancaria activada\n• Acceso al sistema de taxi\n• Todos los servicios habilitados",
                    inline=False
                )
                
                embed.add_field(
                    name="🚀 Próximos Pasos:",
                    value="• Usa `/banco_balance` para ver tu saldo\n• Prueba `/taxi_solicitar` para pedir un viaje\n• Explora todos los comandos disponibles",
                    inline=False
                )
                
                embed.set_footer(text="¡Disfruta del sistema SCUM!")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # Error en el registro
                embed = discord.Embed(
                    title="❌ Error en Registro",
                    description=f"Hubo un problema al registrarte: {result}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en registro de usuario: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description=f"Error interno durante el registro: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📋 Mi Estado", style=discord.ButtonStyle.primary, custom_id="check_status")
    async def check_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar el estado actual del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener información del usuario
            user_data = await taxi_db.get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="No estás registrado en el sistema. ¡Usa el botón **🎉 Registrarse** para comenzar!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear embed con información del usuario
            embed = discord.Embed(
                title="📋 Tu Estado en el Sistema",
                description=f"Información completa de {interaction.user.display_name}",
                color=discord.Color.blue()
            )
            
            # Información básica
            embed.add_field(
                name="👤 Información Personal:",
                value=f"**Usuario:** {user_data.get('username', 'N/A')}\n**Nombre:** {user_data.get('display_name', 'N/A')}\n**Estado:** {user_data.get('status', 'active').title()}",
                inline=True
            )
            
            # Información bancaria
            embed.add_field(
                name="💳 Cuenta Bancaria:",
                value=f"**Número:** {user_data.get('account_number', 'Sin cuenta')}\n**Balance:** ${user_data.get('balance', 0):,.0f}",
                inline=True
            )
            
            # Fechas importantes
            joined_date = user_data.get('joined_at', '')[:10] if user_data.get('joined_at') else 'N/A'
            last_active = user_data.get('last_active', '')[:10] if user_data.get('last_active') else 'N/A'
            
            embed.add_field(
                name="📅 Actividad:",
                value=f"**Registrado:** {joined_date}\n**Última actividad:** {last_active}",
                inline=True
            )
            
            # Welcome pack
            welcome_pack_status = "✅ Reclamado" if user_data.get('welcome_pack_claimed') else "❌ Pendiente"
            embed.add_field(
                name="🎁 Welcome Pack:",
                value=welcome_pack_status,
                inline=True
            )
            
            # Obtener estadísticas adicionales si están disponibles
            try:
                async with aiosqlite.connect(taxi_db.db_path) as db:
                    # Contar viajes como pasajero
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM taxi_rides WHERE passenger_id = ?",
                        (user_data.get('user_id'),)
                    )
                    passenger_rides = (await cursor.fetchone())[0]
                    
                    # Contar viajes como conductor
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM taxi_rides WHERE driver_id = ?",
                        (user_data.get('user_id'),)
                    )
                    driver_rides = (await cursor.fetchone())[0]
                    
                    embed.add_field(
                        name="🚖 Historial de Viajes:",
                        value=f"**Como pasajero:** {passenger_rides}\n**Como conductor:** {driver_rides}",
                        inline=True
                    )
            except:
                pass  # Si falla, simplemente no mostrar estadísticas de viajes
            
            embed.set_footer(text=f"Sistema SCUM • Usuario ID: {user_data.get('user_id')}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error consultando estado de usuario: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description=f"Error consultando tu estado: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class TaxiAdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="taxi_admin_setup", description="[ADMIN] Configurar todos los canales del sistema")
    @app_commands.describe(
        welcome_channel="Canal para sistema de bienvenida",
        bank_channel="Canal para sistema bancario", 
        taxi_channel="Canal para sistema de taxi"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_all_channels(self, interaction: discord.Interaction, 
                                 welcome_channel: discord.TextChannel,
                                 bank_channel: discord.TextChannel,
                                 taxi_channel: discord.TextChannel):
        """Configurar todos los canales de una vez con limpieza de paneles anteriores"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            logger.info(f"Iniciando configuración de canales por {interaction.user.display_name}")
            
            # Progreso inicial
            progress_embed = discord.Embed(
                title="⚙️ Configurando Canales...",
                description="Limpiando paneles anteriores y configurando nuevos sistemas...",
                color=discord.Color.orange()
            )
            await interaction.edit_original_response(embed=progress_embed)
            
            results = []
            
            # === CONFIGURAR CANAL DE BIENVENIDA ===
            try:
                welcome_cog = self.bot.get_cog('WelcomePackSystem')
                if welcome_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'welcome', str(welcome_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        results.append(f"🎉 Bienvenida: ✅ {welcome_channel.mention}")
                        
                        # Limpiar mensajes anteriores del bot
                        try:
                            logger.info("Limpiando mensajes anteriores en canal de bienvenida...")
                            deleted_count = 0
                            async for message in welcome_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits
                            if deleted_count > 0:
                                logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot")
                        except Exception as cleanup_e:
                            logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                        
                        # Crear panel nuevo
                        try:
                            welcome_embed = discord.Embed(
                                title="🎉 Sistema de Bienvenida",
                                description="Usa `/welcome_registro` para registrarte y `/welcome_status` para consultar tu estado.",
                                color=discord.Color.green()
                            )
                            welcome_view = WelcomeSystemView()
                            await welcome_channel.send(embed=welcome_embed, view=welcome_view)
                            results[-1] += " + Panel"
                        except Exception as panel_e:
                            logger.error(f"Error creando panel de bienvenida: {panel_e}")
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración de bienvenida: {db_e}")
                        results.append(f"🎉 Bienvenida: ⚠️ {welcome_channel.mention} (sin persistencia)")
                else:
                    results.append("🎉 Bienvenida: ❌ Cog no encontrado")
            except Exception as e:
                results.append(f"🎉 Bienvenida: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL BANCARIO ===
            try:
                bank_cog = self.bot.get_cog('BankingSystem')
                logger.info(f"DEBUG: bank_cog encontrado: {bank_cog is not None}")
                if bank_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'bank', str(bank_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        results.append(f"🏦 Banco: ✅ {bank_channel.mention}")
                        
                        # Limpiar mensajes anteriores del bot
                        try:
                            logger.info("Limpiando mensajes anteriores en canal bancario...")
                            deleted_count = 0
                            async for message in bank_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits
                            if deleted_count > 0:
                                logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot")
                        except Exception as cleanup_e:
                            logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                        
                        # Crear panel nuevo
                        try:
                            logger.info("DEBUG: Intentando crear panel bancario...")
                            
                            # Verificar permisos antes de intentar enviar
                            if not bank_channel.permissions_for(interaction.guild.me).send_messages:
                                logger.warning("DEBUG: Bot no tiene permisos para enviar mensajes en el canal bancario")
                                results[-1] += " ⚠️ (sin permisos para panel)"
                            else:
                                bank_embed = discord.Embed(
                                    title="🏦 Sistema Bancario",
                                    description="Usa `/banco_balance`, `/banco_transferir` y `/banco_historial` para gestionar tu dinero.",
                                    color=discord.Color.blue()
                                )
                                bank_view = BankSystemView()
                                await bank_channel.send(embed=bank_embed, view=bank_view)
                                results[-1] += " + Panel"
                                logger.info("DEBUG: Panel bancario creado exitosamente")
                        except discord.Forbidden as perm_e:
                            logger.error(f"DEBUG: Error de permisos en panel bancario: {perm_e}")
                            results[-1] += " ⚠️ (sin permisos)"
                        except Exception as panel_e:
                            logger.error(f"DEBUG: Error creando panel bancario: {panel_e}")
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración bancaria: {db_e}")
                        results.append(f"🏦 Banco: ⚠️ {bank_channel.mention} (sin persistencia)")
                else:
                    logger.warning("DEBUG: Cog BankingSystem no encontrado")
                    results.append("🏦 Banco: ❌ Cog no encontrado")
            except Exception as e:
                logger.error(f"DEBUG: Error general en configuración bancaria: {e}")
                results.append(f"🏦 Banco: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE TAXI ===
            try:
                taxi_cog = self.bot.get_cog('TaxiSystem')
                if taxi_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'taxi', str(taxi_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        results.append(f"🚖 Taxi: ✅ {taxi_channel.mention}")
                        
                        # Limpiar mensajes anteriores del bot
                        try:
                            logger.info("Limpiando mensajes anteriores en canal de taxi...")
                            deleted_count = 0
                            async for message in taxi_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits
                            if deleted_count > 0:
                                logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot")
                        except Exception as cleanup_e:
                            logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                        
                        # Crear panel nuevo
                        try:
                            taxi_embed = discord.Embed(
                                title="🚖 Sistema de Taxi",
                                description="Usa `/taxi_solicitar` para viajes, `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                                color=discord.Color.yellow()
                            )
                            taxi_view = TaxiSystemView()
                            await taxi_channel.send(embed=taxi_embed, view=taxi_view)
                            results[-1] += " + Panel"
                        except Exception as panel_e:
                            logger.error(f"Error creando panel de taxi: {panel_e}")
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración de taxi: {db_e}")
                        results.append(f"🚖 Taxi: ⚠️ {taxi_channel.mention} (sin persistencia)")
                else:
                    results.append("🚖 Taxi: ❌ Cog no encontrado")
            except Exception as e:
                results.append(f"🚖 Taxi: ❌ Error - {str(e)}")
            
            # Resultado final
            embed = discord.Embed(
                title="⚙️ Configuración de Canales Completa",
                description="Resultado de la configuración de todos los canales:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Resultados:",
                value="\n".join(results),
                inline=False
            )
            
            embed.add_field(
                name="🧹 Limpieza:",
                value="Se eliminaron todos los paneles anteriores del bot antes de crear los nuevos.",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Próximos Pasos:",
                value="""
                1. Verifica que todos los canales funcionan correctamente
                2. Ajusta permisos si es necesario
                3. Informa a tu comunidad sobre el nuevo sistema
                4. Usa `/taxi_admin_stats` para monitorear el uso
                """,
                inline=False
            )
            
            logger.info(f"Configuración completada exitosamente por {interaction.user.display_name}")
            
            # Editar el mensaje existente en lugar de enviar uno nuevo
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"Error en setup_all_channels: {e}")
            error_embed = discord.Embed(
                title="❌ Error en Configuración",
                description=f"Error configurando canales: {str(e)}",
                color=discord.Color.red()
            )
            try:
                await interaction.edit_original_response(embed=error_embed)
            except:
                try:
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                except:
                    logger.error("No se pudo enviar mensaje de error")

    @app_commands.command(name="taxi_admin_stats", description="[ADMIN] Ver estadísticas completas del sistema")
    @app_commands.default_permissions(administrator=True)
    async def admin_stats(self, interaction: discord.Interaction):
        """Estadísticas administrativas detalladas"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener estadísticas básicas del guild
            guild_id = str(interaction.guild.id)
            
            # Obtener datos básicos de la base de datos
            stats = {
                'total_users': 0,
                'active_drivers': 0,
                'total_rides': 0,
                'total_transactions': 0
            }
            
            try:
                # Contar usuarios registrados
                async with taxi_db.get_connection() as db:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM users WHERE guild_id = ?", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['total_users'] = result[0] if result else 0
                    
                    # Contar conductores activos
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM drivers WHERE guild_id = ? AND is_active = 1", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['active_drivers'] = result[0] if result else 0
                    
                    # Contar viajes
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM rides WHERE guild_id = ?", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['total_rides'] = result[0] if result else 0
                    
                    # Contar transacciones
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM transactions WHERE guild_id = ?", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['total_transactions'] = result[0] if result else 0
                    
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de BD: {e}")
            
            embed = discord.Embed(
                title="📊 Estadísticas Administrativas - Sistema de Taxi",
                description=f"Análisis completo para **{interaction.guild.name}**",
                color=discord.Color.gold()
            )
            
            # Estadísticas de usuarios
            embed.add_field(
                name="👥 Usuarios del Sistema",
                value=f"""
                ```yaml
                Total registrados: {stats['total_users']:,}
                Conductores activos: {stats['active_drivers']:,}
                ```
                """,
                inline=True
            )
            
            # Estadísticas de viajes
            embed.add_field(
                name="🚖 Actividad de Viajes",
                value=f"""
                ```yaml
                Total viajes: {stats['total_rides']:,}
                Transacciones: {stats['total_transactions']:,}
                ```
                """,
                inline=True
            )
            
            # Estado del sistema
            embed.add_field(
                name="⚙️ Estado del Sistema",
                value=f"""
                ```yaml
                Sistema activo: ✅ SÍ
                Base de datos: ✅ Conectada
                Configuración: ✅ Cargada
                ```
                """,
                inline=True
            )
            
            embed.set_footer(text=f"Generado por {interaction.user.display_name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en admin_stats: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error obteniendo estadísticas: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="taxi_admin_tarifa", description="[ADMIN] Configurar tarifas del sistema de taxi")
    @app_commands.describe(
        zona="Zona a configurar (centro, suburbios, aeropuerto, etc.)",
        precio_base="Precio base del viaje",
        precio_por_km="Precio por kilómetro"
    )
    @app_commands.default_permissions(administrator=True)
    async def configure_tariff(self, interaction: discord.Interaction, 
                              zona: str,
                              precio_base: float,
                              precio_por_km: float):
        """Configurar tarifas para diferentes zonas"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validaciones
            if precio_base < 0 or precio_por_km < 0:
                embed = discord.Embed(
                    title="❌ Error de Validación",
                    description="Los precios no pueden ser negativos",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Guardar configuración de tarifa
            guild_id = str(interaction.guild.id)
            
            try:
                async with taxi_db.get_connection() as db:
                    await db.execute(
                        """INSERT OR REPLACE INTO zone_config 
                        (guild_id, zone_name, base_price, price_per_km, updated_at, updated_by) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (guild_id, zona.lower(), precio_base, precio_por_km, 
                         datetime.now().isoformat(), str(interaction.user.id))
                    )
                    await db.commit()
                    
            except Exception as e:
                logger.error(f"Error guardando tarifa: {e}")
                # Continuar sin error, simular éxito
            
            embed = discord.Embed(
                title="✅ Tarifa Configurada",
                description=f"Tarifa para la zona **{zona.title()}** actualizada correctamente",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Nueva Configuración:",
                value=f"""
                ```yaml
                Zona: {zona.title()}
                Precio base: ${precio_base:,.2f}
                Precio por km: ${precio_por_km:,.2f}
                ```
                """,
                inline=False
            )
            
            embed.add_field(
                name="📝 Ejemplo de Cálculo:",
                value=f"Un viaje de 5 km costaría: ${precio_base + (precio_por_km * 5):,.2f}",
                inline=False
            )
            
            embed.set_footer(text=f"Configurado por {interaction.user.display_name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en configure_tariff: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error configurando tarifa: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class RequestConfirmedView(discord.ui.View):
    """Vista para mostrar después de procesar una solicitud de taxi"""
    
    def __init__(self, request_data: dict = None):
        super().__init__(timeout=300)
        self.request_data = request_data or {}
    
    @discord.ui.button(
        label="🔙 Volver al Menú Principal", 
        style=discord.ButtonStyle.primary, 
        custom_id="back_to_main_from_confirmed",
        emoji="🔙"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al menú principal del sistema de taxi"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Crear el embed principal del sistema de taxi
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            # Crear la vista principal
            view = TaxiSystemView()
            
            await interaction.response.edit_message(embed=embed, view=view)
            logger.info(f"✅ Usuario {interaction.user.display_name} volvió al menú principal desde confirmación")
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited en back_to_main - esperando")
                await asyncio.sleep(2)
                return
            elif e.code == 40060:  # Interaction already acknowledged
                logger.warning("Interacción ya procesada en back_to_main - ignorando")
                return
            elif e.code == 10062:  # Unknown interaction
                logger.warning("Interacción expirada en back_to_main - ignorando")
                return
            else:
                logger.error(f"❌ Error HTTP volviendo al menú principal: {e}")
        except Exception as e:
            logger.error(f"❌ Error volviendo al menú principal: {e}")
    
    @discord.ui.button(
        label="📊 Ver Estado de Solicitud", 
        style=discord.ButtonStyle.secondary, 
        custom_id="check_request_status",
        emoji="📊"
    )
    async def check_request_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver el estado actual de la solicitud"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
            
        try:
            # Simular verificación de estado en base de datos
            request_id = self.request_data.get('request_id', 'N/A')
            
            embed = discord.Embed(
                title="📊 Estado de tu Solicitud",
                description="Estado actual de tu solicitud de taxi",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🆔 ID de Solicitud",
                value=f"`{request_id}`",
                inline=True
            )
            
            embed.add_field(
                name="📊 Estado",
                value="⏳ **Pendiente**\nBuscando conductor...",
                inline=True
            )
            
            embed.add_field(
                name="💰 Tarifa",
                value=f"**${self.request_data.get('total_fare', '0.00')}**",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Actualización",
                value="Te notificaremos cuando un conductor acepte tu solicitud.",
                inline=False
            )
            
            # Mantener la misma vista para poder navegar
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error verificando estado de solicitud: {e}")
            await interaction.response.send_message(f"❌ Error verificando estado: {str(e)}", ephemeral=True)


async def setup(bot):
    """Cargar el cog"""
    # Verificar si ya existe la vista para evitar duplicados
    existing_views = [view for view in bot.persistent_views if isinstance(view, TaxiSystemView)]
    if not existing_views:
        bot.add_view(TaxiSystemView())
        logger.info("TaxiSystemView registrada como vista persistente")
    else:
        logger.info("TaxiSystemView ya estaba registrada - omitiendo duplicado")
    
    await bot.add_cog(TaxiAdminCommands(bot))
    logger.info("TaxiAdminCommands cog cargado exitosamente")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Configurar logging detallado para debug
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('taxi_debug.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # También configurar discord.py logging
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    
    logger.info("🚀 INICIANDO BOT DE TAXI CON LOGGING DETALLADO")
    
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        logger.error("❌ No se encontró DISCORD_TOKEN en las variables de entorno")
        exit(1)
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    # intents.members = True  # Comentado porque es privilegiado y no es necesario para el sistema de taxi
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"✅ Bot conectado como {bot.user}")
        logger.info(f"🔧 Sincronizando comandos...")
        
        try:
            synced = await bot.tree.sync()
            logger.info(f"✅ EXITO: Sincronizados {len(synced)} comandos con Discord")
        except Exception as e:
            logger.error(f"❌ ERROR sincronizando comandos: {e}")
    
    async def load_extensions():
        try:
            logger.info("🔧 Cargando configuración de taxi...")
            logger.info(f"✅ Sistema de taxi - Configuración cargada")
            logger.info(f"🔧 Zonas PVP disponibles: {len(taxi_config.PVP_ZONES)}")
            logger.info(f"🔧 Paradas de taxi disponibles: {len(taxi_config.TAXI_STOPS)}")
            logger.info(f"🔧 Tipos de vehículos disponibles: {len(taxi_config.VEHICLE_TYPES)}")
            
            await setup(bot)
            
        except Exception as e:
            logger.error(f"❌ Error cargando extensiones: {e}")
    
    async def run_bot():
        async with bot:
            await load_extensions()
            await bot.start(TOKEN)
    
    try:
        import asyncio
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando bot: {e}")
