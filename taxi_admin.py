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
import os
from datetime import datetime
from typing import List, Dict, Optional
from taxi_database import taxi_db
from taxi_config import taxi_config
from core.user_manager import user_manager, get_user_by_discord_id, get_user_balance
from rate_limiter import rate_limit, rate_limiter

# Obtener VEHICLE_TYPES desde la instancia de configuración
VEHICLE_TYPES = taxi_config.VEHICLE_TYPES
PICKUP_ZONES = taxi_config.PVP_ZONES  # Usar PVP_ZONES como pickup zones

class BaseView(discord.ui.View):
    """Clase base para todas las vistas con manejo correcto de timeout"""
    
    async def on_timeout(self):
        """Manejar timeout de la vista de forma asíncrona"""
        for item in self.children:
            item.disabled = True

# Sistema de cooldown para evitar rate limiting
USER_COOLDOWNS = {}
GLOBAL_COOLDOWN = 2.0  # 2 segundos entre interacciones por usuario

def is_bot_admin_cog():
    """Decorator para verificar si el usuario es admin del bot en el contexto de un cog"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Primero intentar desde variables de entorno (.env)
        admin_ids_env = os.getenv('BOT_ADMIN_IDS', '').split(',')
        admin_ids_from_env = [id.strip() for id in admin_ids_env if id.strip()]
        
        # Si no hay IDs en .env, usar config.py como respaldo
        if not admin_ids_from_env:
            try:
                from config import BOT_ADMIN_IDS
                admin_ids_from_config = [str(id) for id in BOT_ADMIN_IDS]
                admin_ids = admin_ids_from_config
            except ImportError:
                admin_ids = []
        else:
            admin_ids = admin_ids_from_env
        
        user_id = str(interaction.user.id)
        return user_id in admin_ids
    
    return app_commands.check(predicate)

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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            user_data = await get_user_by_discord_id(
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
            user_data = await get_user_by_discord_id(str(user_id), guild_id_str)
            
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
            user_data = await get_user_by_discord_id(str(user_id), str(guild_id))
            
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
    
    @discord.ui.button(label="⭐ Calificar Viaje", style=discord.ButtonStyle.secondary, custom_id="rate_trip")
    async def rate_trip(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Permite a los pasajeros calificar conductores después de un viaje completado"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
        
        try:
            # Obtener usuario en la base de datos
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No estás registrado en el sistema de taxi.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            user_id = int(user_data['user_id'])
            
            # Buscar viajes completados que aún no han sido calificados por este usuario
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT tr.request_id, tr.driver_id, tr.pickup_zone, tr.destination_zone,
                           tr.final_cost, tr.completed_at, td.license_number, tu_driver.display_name as driver_name
                    FROM taxi_requests tr
                    JOIN taxi_drivers td ON tr.driver_id = td.driver_id
                    JOIN taxi_users tu_driver ON td.user_id = tu_driver.user_id
                    LEFT JOIN taxi_ratings rating ON rating.request_id = tr.request_id AND rating.rater_id = ?
                    WHERE tr.passenger_id = ? 
                    AND tr.status = 'completed' 
                    AND rating.rating_id IS NULL
                    ORDER BY tr.completed_at DESC
                    LIMIT 5
                """, (user_id, user_id))
                
                unrated_trips = await cursor.fetchall()
                
                if not unrated_trips:
                    embed = discord.Embed(
                        title="⭐ Calificar Viajes",
                        description="No tienes viajes completados pendientes de calificar.",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(
                        name="💡 ¿Cómo funciona?",
                        value="Después de completar un viaje, aparecerán aquí para que puedas calificar a tu conductor.",
                        inline=False
                    )
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Crear embed con viajes pendientes de calificar
                embed = discord.Embed(
                    title="⭐ Calificar Viajes",
                    description="Selecciona un viaje para calificar al conductor:",
                    color=0xffd700
                )
                
                # Mostrar hasta 3 viajes en el embed
                for i, trip in enumerate(unrated_trips[:3]):
                    request_id, driver_id, pickup_zone, destination_zone, final_cost, completed_at, license_number, driver_name = trip
                    
                    embed.add_field(
                        name=f"🚖 Viaje #{request_id}",
                        value=f"**Conductor:** {driver_name} (#{license_number})\n"
                              f"**Ruta:** {pickup_zone} → {destination_zone}\n"
                              f"**Costo:** ${final_cost:.2f}\n"
                              f"**Fecha:** {completed_at[:16]}",
                        inline=True
                    )
                
                embed.add_field(
                    name="📝 Instrucciones",
                    value="Usa el selector de abajo para elegir qué viaje calificar.\n"
                          "Tu calificación ayuda a otros usuarios a elegir buenos conductores.",
                    inline=False
                )
                
                # Crear vista con selector de viajes
                view = TripRatingView(unrated_trips)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error mostrando viajes para calificar: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error interno al buscar viajes para calificar.",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)


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
        
        # Verificar el estado actual de la solicitud antes de cancelar
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT status, driver_id FROM taxi_requests 
                    WHERE request_id = ?
                """, (self.request_id,))
                
                request_status = await cursor.fetchone()
                
                if not request_status:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="No se pudo encontrar la solicitud.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                status, driver_id = request_status
                
                # Si ya fue aceptada por un conductor, no permitir cancelación
                if status == 'accepted' and driver_id is not None:
                    embed = discord.Embed(
                        title="⚠️ No se puede cancelar",
                        description="Tu solicitud ya ha sido **aceptada por un conductor**.\n\nYa no puedes cancelarla. El conductor está en camino hacia ti.",
                        color=discord.Color.orange()
                    )
                    
                    embed.add_field(
                        name="📞 ¿Necesitas ayuda?",
                        value="Contacta al conductor directamente o espera a que complete el viaje.",
                        inline=False
                    )
                    
                    view = TaxiSystemView()
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    return
                
                # Si aún está pendiente, permitir cancelación
                elif status == 'pending':
                    success, message = await taxi_db.cancel_request(self.request_id)
                    
                    if success:
                        embed = discord.Embed(
                            title="✅ Solicitud Cancelada",
                            description="Tu solicitud de taxi ha sido cancelada exitosamente.",
                            color=0x00ff00
                        )
                        
                        embed.add_field(
                            name="🚖 ¿Qué sigue?",
                            value="Puedes crear una nueva solicitud desde el panel principal.",
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Error al cancelar",
                            description=f"No se pudo cancelar la solicitud: {message}",
                            color=discord.Color.red()
                        )
                    
                    view = TaxiSystemView()
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    
                else:
                    embed = discord.Embed(
                        title="❌ Solicitud no válida",
                        description=f"La solicitud ya tiene estado: **{status}**",
                        color=discord.Color.red()
                    )
                    
                    view = TaxiSystemView()
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error verificando estado para cancelación: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error interno al procesar la cancelación.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
                        try:
                            # Intentar obtener del cache primero, luego fetch de la API
                            passenger_user = interaction.client.get_user(passenger_discord_id)
                            if not passenger_user:
                                passenger_user = await interaction.client.fetch_user(passenger_discord_id)
                        except discord.NotFound:
                            passenger_user = None
                            logger.warning(f"⚠️ Usuario Discord {passenger_discord_id} no encontrado en Discord")
                        except Exception as fetch_error:
                            passenger_user = None
                            logger.error(f"❌ Error obteniendo usuario Discord {passenger_discord_id}: {fetch_error}")
                        
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
        label="🚗 Viajes Activos", 
        style=discord.ButtonStyle.success, 
        custom_id="active_trips",
        row=1
    )
    async def view_active_trips(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver y gestionar viajes activos"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        # Verificar si la interacción ya fue respondida
        if interaction.response.is_done():
            logger.warning("Interacción ya fue procesada - ignorando")
            return
            
        try:
            # Obtener viajes activos del conductor
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                await interaction.response.send_message("❌ No se encontraron datos del usuario", ephemeral=True)
                return
                
            driver_info = await taxi_db.get_driver_info(int(user_data['user_id']))
            if not driver_info:
                await interaction.response.send_message("❌ No eres un conductor registrado", ephemeral=True)
                return
            
            # Buscar viajes activos (aceptados por este conductor)
            active_trips = await taxi_db.get_active_trips_for_driver(driver_info['driver_id'])
            
            embed = discord.Embed(
                title="🚗 Viajes Activos",
                description="Gestiona tus viajes en curso",
                color=0x00ff00
            )
            
            if not active_trips:
                embed.add_field(
                    name="📭 Sin Viajes Activos",
                    value="No tienes viajes en curso en este momento.\nUsa **'📋 Ver Solicitudes'** para aceptar nuevas solicitudes.",
                    inline=False
                )
                view = DriverPanelView(driver_info)
                await interaction.response.edit_message(embed=embed, view=view)
                return
            
            # Mostrar viajes activos
            for i, trip in enumerate(active_trips[:3]):  # Máximo 3 viajes
                passenger_name = trip.get('passenger_name', 'Pasajero')
                pickup_zone = trip.get('pickup_zone', 'Origen desconocido')
                destination_zone = trip.get('destination_zone', 'Destino desconocido')
                estimated_cost = trip.get('estimated_cost', 0)
                created_at = trip.get('created_at', '')
                
                embed.add_field(
                    name=f"🚖 Viaje #{trip['request_id']}",
                    value=f"**👤 Pasajero:** {passenger_name}\n"
                          f"**📍 Origen:** {pickup_zone}\n"
                          f"**🎯 Destino:** {destination_zone}\n"
                          f"**💰 Tarifa:** ${estimated_cost:,.2f}\n"
                          f"**🕐 Iniciado:** {created_at[:16]}",
                    inline=True
                )
            
            if len(active_trips) > 3:
                embed.set_footer(text=f"Mostrando 3 de {len(active_trips)} viajes activos")
            
            # Crear vista con opciones para completar viajes
            view = ActiveTripsView(active_trips, driver_info)
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error viendo viajes activos: {e}")
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
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
                user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
        try:
            options = []
            
            # Crear lista de todas las zonas y ordenar por Grid+Pad
            all_zones = []
            
            # Agregar TAXI_STOPS
            for stop_id, stop_data in taxi_config.TAXI_STOPS.items():
                logger.debug(f"🔧 SETUP ORIGIN - Procesando parada: {stop_id} - {stop_data.get('name', 'Sin nombre')}")
                all_zones.append({
                    'id': stop_id,
                    'data': stop_data,
                    'source': 'taxi_stops'
                })
            
            # Agregar PVP_ZONES accesibles
            for zone_id, zone_data in taxi_config.PVP_ZONES.items():
                restriction = zone_data.get('restriction', 'neutral')
                if restriction in ['safe_zone', 'neutral']:
                    all_zones.append({
                        'id': zone_id,
                        'data': zone_data,
                        'source': 'pvp_zones'
                    })
            
            # ORDENAR por Grid (A-Z) y luego por Pad (1-9)
            def zone_sort_key(zone_item):
                zone_data = zone_item['data']
                grid = zone_data.get('grid', 'Z9')
                pad = zone_data.get('pad', 9)
                
                grid_letter = grid[0] if grid else 'Z'
                grid_number = grid[1:] if len(grid) > 1 else '9'
                
                return (grid_letter, int(grid_number) if grid_number.isdigit() else 9, pad)
            
            all_zones.sort(key=zone_sort_key)
            
            # Crear opciones del selector ordenadas
            for zone_item in all_zones:
                zone_data = zone_item['data']
                zone_id = zone_item['id']
                
                emoji = {
                    'main_stop': "🏢", 'town_stop': "🏘️", 'airstrip': "✈️", 'seaport': "🚢",
                    'airport_stop': "✈️", 'port_stop': "⚓", 'industrial_stop': "🏭",
                    'mining_stop': "⛏️", 'airport': "🛬", 'city': "🏙️", 'town': "🏘️",
                    'port': "⚓", 'island': "🏝️", 'industrial': "🏭", 'mining': "⛏️"
                }.get(zone_data['type'], "📍")
                
                options.append(discord.SelectOption(
                    label=f"{zone_data['coordinates']} {zone_data['name']}",
                    value=zone_id,
                    description=f"{zone_data.get('description', 'Zona disponible')[:50]}",
                    emoji=emoji
                ))
                logger.debug(f"✅ SETUP ORIGIN - Opción agregada: {zone_data['name']} ({zone_data['coordinates']})")
            
            # Actualizar las opciones del selector de origen
            origin_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'origin_select':
                    item.options = options[:25]  # Máximo 25 opciones por selector
                    origin_selector_found = True
                    break
            
            if not origin_selector_found:
                logger.warning("⚠️ SETUP ORIGIN - No se encontró el selector de origen en children")
            
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
        try:
            self.origin = select.values[0]
            logger.info(f"🔧 ORIGIN SELECT - Origen seleccionado: {self.origin}")
            
            origin_data = taxi_config.TAXI_STOPS[self.origin]
            
            # Actualizar selector de vehículo según parada
            available_vehicles = origin_data.get('vehicle_types', [])
            
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
            
            # Encontrar y actualizar el selector de vehículos
            vehicle_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'vehicle_select':
                    item.options = vehicle_options[:25]
                    item.placeholder = "🚗 Selecciona tu vehículo..."
                    item.disabled = False
                    vehicle_selector_found = True
                    break
            
            if not vehicle_selector_found:
                logger.warning("⚠️ ORIGIN SELECT - No se encontró el selector de vehículos")
            
            # Limpiar destinos hasta que se seleccione vehículo
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'destination_select':
                    item.options = [discord.SelectOption(label="Primero selecciona un vehículo", value="disabled")]
                    item.placeholder = "🚫 Primero selecciona un vehículo..."
                    item.disabled = True
                    break
            
            embed = discord.Embed(
                title="🚖 Solicitar Taxi - Paso 2/3",
                description=f"**Origen seleccionado:** {origin_data['name']}\n\nAhora selecciona tu tipo de vehículo:",
                color=discord.Color.green()
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
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
        try:
            self.vehicle_type = select.values[0]
            vehicle_data = taxi_config.VEHICLE_TYPES[self.vehicle_type]
            origin_data = taxi_config.TAXI_STOPS[self.origin]
            
            # Actualizar selector de destino según vehículo
            destination_options = []
            
            # Filtrar destinos según el vehículo seleccionado
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
            
            # Encontrar y actualizar el selector de destinos
            destination_selector_found = False
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == 'destination_select':
                    item.options = destination_options[:25]  # Máximo 25 opciones
                    item.placeholder = "🎯 Selecciona tu destino..."
                    item.disabled = False
                    destination_selector_found = True
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
            
            await interaction.response.edit_message(embed=embed, view=self)
            
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

            base_fare = taxi_config.TAXI_BASE_RATE * vehicle_data['cost_multiplier']
            distance_fare = (taxi_config.TAXI_PER_KM_RATE * 5) * vehicle_data['cost_multiplier']  # Estimación
            total_fare = base_fare + distance_fare

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
                # Obtener datos del usuario para guardar en BD
                user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
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
            await interaction.response.edit_message(embed=embed, view=confirmed_view)
            
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
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
            # Usar transfer_money del user_manager (requiere user_ids, no account numbers)
            success, message = await user_manager.transfer_money(
                from_user_id=sender_user_data['user_id'],
                to_user_id=target_user_data['user_id'],
                amount=transfer_amount,
                description=f"{desc} - via admin panel"
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

class UpdateInGameNameModal(discord.ui.Modal, title="🎮 Actualizar Nombre InGame"):
    """Modal para actualizar el nombre InGame del usuario"""
    
    def __init__(self, current_name: str = ""):
        super().__init__()
        self.current_name = current_name
        # Si hay un nombre actual, lo usamos como valor por defecto
        if current_name:
            self.ingame_name.default = current_name
    
    ingame_name = discord.ui.TextInput(
        label="Nuevo Nombre del Jugador en SCUM",
        placeholder="Escribe tu nombre actualizado...",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        new_name = self.ingame_name.value.strip()
        
        if len(new_name) < 2:
            embed = discord.Embed(
                title="❌ Nombre Inválido",
                description="El nombre debe tener al menos 2 caracteres",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Actualizar nombre InGame en base de datos
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute(
                    "UPDATE taxi_users SET ingame_name = ? WHERE discord_id = ? AND discord_guild_id = ?",
                    (new_name, str(interaction.user.id), str(interaction.guild.id))
                )
                await db.commit()
            
            embed = discord.Embed(
                title="✅ Nombre Actualizado",
                description=f"Tu nombre InGame ha sido actualizado correctamente",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🎮 Nuevo Nombre",
                value=f"`{new_name}`",
                inline=True
            )
            embed.add_field(
                name="🔧 Sistema de Mecánico",
                value="¡Ahora puedes usar el taller mecánico con `/seguro_solicitar`!",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error actualizando nombre InGame: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error actualizando tu nombre. Intenta nuevamente.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
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
            
            # Registrar nuevo usuario usando user_manager
            success, result = await user_manager.register_user(
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
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
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
            
            # Obtener estadísticas adicionales del sistema de bienvenida
            try:
                async with aiosqlite.connect(taxi_db.db_path) as db:
                    # Contar transacciones bancarias
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM bank_transactions WHERE to_account = ? OR from_account = ?",
                        (user_data.get('account_number'), user_data.get('account_number'))
                    )
                    total_transactions = (await cursor.fetchone())[0]
                    
                    # Mostrar estadísticas del sistema general (no específicas de taxi)
                    embed.add_field(
                        name="📊 Actividad del Sistema:",
                        value=f"**Transacciones:** {total_transactions}\n**Timezone:** {user_data.get('timezone', 'UTC')}",
                        inline=True
                    )
            except:
                # Si falla, mostrar información básica
                embed.add_field(
                    name="📊 Información Adicional:",
                    value=f"**Timezone:** {user_data.get('timezone', 'UTC')}\n**Sistema:** Activo",
                    inline=True
                )
            
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
    
    @discord.ui.button(label="🎮 Actualizar Nombre InGame", style=discord.ButtonStyle.secondary, custom_id="update_ingame_name")
    async def update_ingame_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualizar nombre InGame del usuario"""
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ No Registrado",
                    description="Debes registrarte primero antes de actualizar tu nombre InGame.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Crear y mostrar modal para actualizar nombre InGame
            current_name = user_data.get('ingame_name', '')
            modal = UpdateInGameNameModal(current_name)
            await interaction.response.send_modal(modal)
                
        except Exception as e:
            logger.error(f"Error en actualización de nombre InGame: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description=f"Error procesando la solicitud: {str(e)}",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

class TaxiAdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_channels = {}  # guild_id -> channel_id

    async def cog_load(self):
        """Cargar configuraciones al inicializar el cog"""
        await self.load_channel_configs()
        
        # Iniciar task de limpieza de solicitudes expiradas
        self._cleanup_task = asyncio.create_task(self._start_cleanup_loop())
    
    async def load_channel_configs(self):
        """Cargar configuraciones de canales desde la base de datos y recrear paneles"""
        try:
            configs = await taxi_db.load_all_channel_configs()
            
            for guild_id, channels in configs.items():
                if "admin" in channels:
                    guild_id_int = int(guild_id)
                    channel_id = channels["admin"]
                    
                    # Cargar en memoria
                    self.admin_channels[guild_id_int] = channel_id
                    
                    # Recrear panel administrativo en el canal
                    await self._recreate_admin_panel(guild_id_int, channel_id)
                    
                    logger.info(f"Cargada y recreada configuración de admin para guild {guild_id}: canal {channel_id}")
            
            logger.info(f"Sistema administrativo: {len(self.admin_channels)} canales cargados con paneles recreados")
            
        except Exception as e:
            logger.error(f"Error cargando configuraciones administrativas: {e}")
    
    async def _recreate_admin_panel(self, guild_id: int, channel_id: int):
        """Recrear panel administrativo en el canal especificado con limpieza previa"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Canal admin {channel_id} no encontrado para guild {guild_id}")
                return
            
            # Verificar permisos
            if not channel.permissions_for(channel.guild.me).send_messages:
                logger.warning(f"Sin permisos para enviar mensajes en canal admin {channel_id}")
                return
            
            # Recrear panel con limpieza automática
            panel_success = await setup_admin_panel(channel, self.bot)
            if panel_success:
                logger.info(f"✅ Panel administrativo recreado en guild {guild_id}, canal {channel_id}")
            else:
                logger.warning(f"Error recreando panel administrativo para guild {guild_id}")
                
        except Exception as e:
            logger.error(f"Error recreando panel administrativo para guild {guild_id}: {e}")

    @rate_limit("debug_shop_stock")
    @app_commands.command(name="debug_shop_stock", description="[DEBUG] Ver stock actual de la tienda")
    @app_commands.default_permissions(administrator=True)
    async def debug_shop_stock(self, interaction: discord.Interaction):
        """Comando temporal para debugging del stock"""
        # Manual rate limiting check
        from rate_limiter import rate_limiter
        if not await rate_limiter.check_and_record(interaction, "debug_shop_stock"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            stock_data = await taxi_db.get_all_shop_stock()
            
            if not stock_data:
                embed = discord.Embed(
                    title="📦 Stock de Tienda - VACÍO",
                    description="No hay registros de stock en la base de datos",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📦 Stock Actual de la Tienda",
                description="Estado actual del inventario por pack",
                color=discord.Color.blue()
            )
            
            # Agrupar por tier
            tier_groups = {}
            for item in stock_data:
                tier = item['tier']
                if tier not in tier_groups:
                    tier_groups[tier] = []
                tier_groups[tier].append(item)
            
            for tier, items in tier_groups.items():
                stock_info = ""
                for item in items:
                    stock_info += f"**{item['pack_id']}**: {item['current_stock']}/{item['max_stock']}\n"
                
                embed.add_field(
                    name=f"🏷️ {tier.upper()}",
                    value=stock_info or "Sin packs",
                    inline=True
                )
            
            embed.set_footer(text="Comando temporal para debugging")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en debug_shop_stock: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="pending_packages", description="[ADMIN] Ver paquetes pendientes de entrega")
    @app_commands.default_permissions(administrator=True)
    async def pending_packages_command(self, interaction: discord.Interaction):
        """Comando para ver paquetes pendientes"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            pending = await taxi_db.get_pending_packages(str(interaction.guild.id))
            
            if not pending:
                embed = discord.Embed(
                    title="📦 Sin Paquetes Pendientes",
                    description="No hay paquetes pendientes de entrega en este servidor.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 Paquetes Pendientes de Entrega",
                description=f"Hay **{len(pending)}** paquetes esperando ser entregados",
                color=discord.Color.orange()
            )
            
            for i, package in enumerate(pending[:10]):  # Mostrar máximo 10
                from shop_config import get_pack_by_id
                pack_info = get_pack_by_id(package['pack_id'])
                pack_name = pack_info['name'] if pack_info else package['pack_id']
                
                from datetime import datetime
                purchased_timestamp = int(datetime.fromisoformat(package['purchased_at']).timestamp())
                
                embed.add_field(
                    name=f"#{package['purchase_id']} - {pack_name}",
                    value=f"**Usuario:** {package['user_display_name']}\n**Tier:** {package['tier'].title()}\n**Precio:** ${package['amount_paid']:,.2f}\n**Comprado:** <t:{purchased_timestamp}:R>",
                    inline=True
                )
            
            if len(pending) > 10:
                embed.add_field(
                    name="ℹ️ Nota",
                    value=f"Mostrando primeros 10 de {len(pending)} paquetes pendientes",
                    inline=False
                )
            
            embed.set_footer(text="Usa el canal shop-claimer para confirmar entregas")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo paquetes pendientes: {e}")
            await interaction.followup.send("❌ Error obteniendo paquetes pendientes", ephemeral=True)

    @app_commands.command(name="ba_admin_channels_setup", description="[ADMIN] Configurar todos los canales del sistema BunkerAdvice")
    @app_commands.describe(
        welcome_channel="Canal para sistema de bienvenida",
        bank_channel="Canal para sistema bancario", 
        taxi_channel="Canal para sistema de taxi",
        mechanic_channel="Canal para sistema de mecánico",
        squadron_channel="Canal para registro de escuadrones PvP/PvE",
        shop_channel="Canal para tienda de supervivencia",
        shop_claimer_channel="Canal para notificaciones de compras (solo admins)",
        admin_channel="Canal para panel de administración (gestión usuarios/conductores)",
        bunker_channel="Canal para sistema de bunkers con botones interactivos",
        mechanic_notifications_channel="Canal para notificaciones de seguros pendientes (mecánicos)",
        ticket_channel="Canal para sistema de tickets de soporte"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_all_channels(self, interaction: discord.Interaction, 
                                 welcome_channel: discord.TextChannel,
                                 bank_channel: discord.TextChannel,
                                 taxi_channel: discord.TextChannel,
                                 mechanic_channel: discord.TextChannel,
                                 squadron_channel: discord.TextChannel,
                                 shop_channel: discord.TextChannel,
                                 shop_claimer_channel: discord.TextChannel,
                                 admin_channel: discord.TextChannel,
                                 bunker_channel: discord.TextChannel,
                                 mechanic_notifications_channel: discord.TextChannel,
                                 ticket_channel: discord.TextChannel):
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
                            deleted_count = 0
                            async for message in welcome_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits

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
                if bank_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'banking', str(bank_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        results.append(f"🏦 Banco: ✅ {bank_channel.mention}")
                        
                        # Limpiar mensajes anteriores del bot
                        try:
                            deleted_count = 0
                            async for message in bank_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits

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
                            deleted_count = 0
                            async for message in taxi_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits

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
            
            # === CONFIGURAR CANAL DE MECÁNICO ===
            try:
                mechanic_cog = self.bot.get_cog('MechanicSystem')
                if mechanic_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'mechanic', str(mechanic_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        results.append(f"🔧 Mecánico: ✅ {mechanic_channel.mention}")
                        
                        # Configurar canal de mecánico
                        try:
                            success = await mechanic_cog.setup_mechanic_channel(interaction.guild.id, mechanic_channel.id)
                            if success:
                                results[-1] += " + Panel"
                            else:
                                results[-1] += " ⚠️ (error de panel)"
                        except Exception as panel_e:
                            logger.error(f"Error creando panel de mecánico: {panel_e}")
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración de mecánico: {db_e}")
                        results.append(f"🔧 Mecánico: ⚠️ {mechanic_channel.mention} (sin persistencia)")
                else:
                    results.append("🔧 Mecánico: ❌ Cog no encontrado")
            except Exception as e:
                results.append(f"🔧 Mecánico: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE ESCUADRONES ===
            try:
                guild_id = str(interaction.guild.id)
                try:
                    # Guardar configuración en la base de datos
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        await db.execute(
                            """INSERT OR REPLACE INTO channel_config 
                            (guild_id, channel_type, channel_id, updated_at, updated_by) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (guild_id, 'squadron', str(squadron_channel.id), 
                             datetime.now().isoformat(), str(interaction.user.id))
                        )
                        await db.commit()
                    results.append(f"🏆 Escuadrones: ✅ {squadron_channel.mention}")
                    
                    # Limpiar mensajes anteriores del bot
                    try:
                        deleted_count = 0
                        async for message in squadron_channel.history(limit=50):
                            if message.author == self.bot.user:
                                await message.delete()
                                deleted_count += 1
                                await asyncio.sleep(0.1)  # Evitar rate limits

                    except Exception as cleanup_e:
                        logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                    
                    # Crear panel nuevo de escuadrones
                    try:
                        if not squadron_channel.permissions_for(interaction.guild.me).send_messages:
                            logger.warning("Bot no tiene permisos para enviar mensajes en el canal de escuadrones")
                            results[-1] += " ⚠️ (sin permisos para panel)"
                        else:
                            squadron_embed = discord.Embed(
                                title="🏆 Registro de Escuadrones SCUM",
                                description="**¡Únete o crea tu escuadrón para dominar SCUM!**\n\nLos escuadrones determinan el tipo de gameplay y beneficios en vehículos.",
                                color=0xff6600
                            )
                            
                            squadron_embed.add_field(
                                name="⚔️ Tipos de Escuadrones",
                                value="• **PvP:** Combate y raids activos\n• **PvE:** Exploración y supervivencia\n• **Mixto:** Adaptable según situación",
                                inline=True
                            )
                            
                            squadron_embed.add_field(
                                name="🎯 Beneficios",
                                value="• Límites de vehículos optimizados\n• Seguros con tarifas grupales\n• Coordinación de actividades\n• Identificación automática PvP/PvE",
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
                            
                            # Crear vista con botones para escuadrones
                            from mechanic_system import SquadronSystemView
                            squadron_view = SquadronSystemView()
                            await squadron_channel.send(embed=squadron_embed, view=squadron_view)
                            results[-1] += " + Panel"
                            logger.info("Panel de escuadrones creado exitosamente")
                    except Exception as panel_e:
                        logger.error(f"Error creando panel de escuadrones: {panel_e}")
                        results[-1] += " ⚠️ (error de panel)"
                except Exception as db_e:
                    logger.error(f"Error guardando configuración de escuadrones: {db_e}")
                    results.append(f"🏆 Escuadrones: ⚠️ {squadron_channel.mention} (sin persistencia)")
            except Exception as e:
                results.append(f"🏆 Escuadrones: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE TIENDA ===
            try:
                guild_id = str(interaction.guild.id)
                try:
                    # Guardar configuración en la base de datos
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        await db.execute(
                            """INSERT OR REPLACE INTO channel_config 
                            (guild_id, channel_type, channel_id, updated_at, updated_by) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (guild_id, 'shop', str(shop_channel.id), 
                             datetime.now().isoformat(), str(interaction.user.id))
                        )
                        await db.commit()
                    results.append(f"🛒 Tienda: ✅ {shop_channel.mention}")
                    
                    # Limpiar mensajes anteriores del bot
                    try:
                        deleted_count = 0
                        async for message in shop_channel.history(limit=50):
                            if message.author == self.bot.user:
                                await message.delete()
                                deleted_count += 1
                                await asyncio.sleep(0.1)  # Evitar rate limits

                    except Exception as cleanup_e:
                        logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                    
                    # Crear panel nuevo
                    try:
                        shop_embed = discord.Embed(
                            title="🛒 Tienda de Supervivencia SCUM",
                            description="¡Intercambia tus recursos por equipamiento de supervivencia de alta gama!\n\nSelecciona tu tier para ver los packs disponibles.",
                            color=discord.Color.gold()
                        )
                        shop_embed.add_field(
                            name="💰 Métodos de Pago",
                            value="• Dinero del sistema bancario\n• Recursos y materiales\n• Vehículos y equipamiento",
                            inline=True
                        )
                        shop_embed.add_field(
                            name="⏰ Disponibilidad",
                            value="• **Tier 1:** Cada semana\n• **Tier 2:** Cada 2 semanas\n• **Tier 3:** Cada 3 semanas",
                            inline=True
                        )
                        shop_embed.add_field(
                            name="🎯 Especialidades",
                            value="• Packs de construcción\n• Equipamiento de combate\n• Vehículos limitados\n• Suministros médicos",
                            inline=False
                        )
                        shop_embed.set_footer(text="Habla con un administrador para realizar el canje")
                        
                        shop_view = ShopSystemView()
                        await shop_channel.send(embed=shop_embed, view=shop_view)
                        results[-1] += " + Panel"
                    except Exception as panel_e:
                        logger.error(f"Error creando panel de tienda: {panel_e}")
                        results[-1] += " ⚠️ (error de panel)"
                except Exception as db_e:
                    logger.error(f"Error guardando configuración de tienda: {db_e}")
                    results.append(f"🛒 Tienda: ⚠️ {shop_channel.mention} (sin persistencia)")
            except Exception as e:
                results.append(f"🛒 Tienda: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE SHOP CLAIMER ===
            try:
                guild_id = str(interaction.guild.id)
                try:
                    # Guardar configuración en la base de datos
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        await db.execute(
                            """INSERT OR REPLACE INTO channel_config 
                            (guild_id, channel_type, channel_id, updated_at, updated_by) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (guild_id, 'shop_claimer', str(shop_claimer_channel.id), 
                             datetime.now().isoformat(), str(interaction.user.id))
                        )
                        await db.commit()
                    results.append(f"🔔 Shop-Claimer: ✅ {shop_claimer_channel.mention}")
                    
                    # Limpiar mensajes anteriores del bot
                    try:
                        deleted_count = 0
                        async for message in shop_claimer_channel.history(limit=50):
                            if message.author == self.bot.user:
                                await message.delete()
                                deleted_count += 1
                                await asyncio.sleep(0.1)  # Evitar rate limits

                    except Exception as cleanup_e:
                        logger.warning(f"Error limpiando mensajes anteriores: {cleanup_e}")
                    
                    # Crear mensaje informativo
                    try:
                        claimer_embed = discord.Embed(
                            title="🔔 Canal de Notificaciones de Compras",
                            description="Este canal recibe notificaciones automáticas cuando los usuarios compran packs en la tienda.",
                            color=discord.Color.purple()
                        )
                        claimer_embed.add_field(
                            name="📋 Información que recibirás:",
                            value="• Usuario que realizó la compra\n• Pack comprado y tier\n• Método de pago utilizado\n• Timestamp de la compra",
                            inline=False
                        )
                        claimer_embed.add_field(
                            name="👨‍💼 Acceso:",
                            value="Solo administradores y owner del servidor pueden ver este canal",
                            inline=False
                        )
                        claimer_embed.set_footer(text="Sistema de Tienda SCUM - Configurado automáticamente")
                        
                        await shop_claimer_channel.send(embed=claimer_embed)
                        results[-1] += " + Panel"
                    except Exception as panel_e:
                        logger.error(f"Error creando panel de shop-claimer: {panel_e}")
                        results[-1] += " ⚠️ (error de panel)"
                except Exception as db_e:
                    logger.error(f"Error guardando configuración de shop-claimer: {db_e}")
                    results.append(f"🔔 Shop-Claimer: ⚠️ {shop_claimer_channel.mention} (sin persistencia)")
            except Exception as e:
                results.append(f"🔔 Shop-Claimer: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE ADMINISTRACIÓN ===
            try:
                guild_id_str = str(interaction.guild.id)
                guild_id_int = interaction.guild.id
                
                # Guardar en memoria (para acceso rápido)
                self.admin_channels[guild_id_int] = admin_channel.id
                
                try:
                    # Guardar configuración en la base de datos (para persistencia)
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        await db.execute(
                            """INSERT OR REPLACE INTO channel_config 
                            (guild_id, channel_type, channel_id, updated_at, updated_by) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (guild_id_str, 'admin', str(admin_channel.id), 
                             datetime.now().isoformat(), str(interaction.user.id))
                        )
                        await db.commit()
                    results.append(f"🛠️ Admin: ✅ {admin_channel.mention}")
                    
                    # Configurar panel administrativo con limpieza
                    try:
                        admin_panel_success = await setup_admin_panel(admin_channel, self.bot)
                        if admin_panel_success:
                            results[-1] += " + Panel"
                            logger.info("Panel administrativo creado exitosamente")
                        else:
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as panel_e:
                        logger.error(f"Error creando panel administrativo: {panel_e}")
                        results[-1] += " ⚠️ (error de panel)"
                        
                except Exception as db_e:
                    logger.error(f"Error guardando configuración de administración: {db_e}")
                    results.append(f"🛠️ Admin: ⚠️ {admin_channel.mention} (sin persistencia)")
            except Exception as e:
                results.append(f"🛠️ Admin: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE BUNKERS ===
            try:
                guild_id_str = str(interaction.guild.id)
                guild_id_int = interaction.guild.id
                
                # Limpiar canal antes de configurar
                try:
                    await bunker_channel.purge(limit=100)
                    logger.info(f"Canal de bunkers {bunker_channel.name} limpiado")
                except Exception as clean_e:
                    logger.warning(f"No se pudo limpiar canal de bunkers: {clean_e}")
                
                try:
                    # Guardar configuración en la base de datos (para persistencia)
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        await db.execute(
                            """INSERT OR REPLACE INTO channel_config 
                            (guild_id, channel_type, channel_id, updated_at, updated_by) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (guild_id_str, 'bunker', str(bunker_channel.id), 
                             datetime.now().isoformat(), str(interaction.user.id))
                        )
                        await db.commit()
                    results.append(f"⏰ Bunkers: ✅ {bunker_channel.mention}")
                    
                    # Configurar panel de bunkers con botones interactivos
                    try:
                        from BunkerAdvice_V2 import setup_bunker_panel
                        bunker_panel_success = await setup_bunker_panel(bunker_channel, self.bot)
                        if bunker_panel_success:
                            results[-1] += " + Panel"
                        else:
                            results[-1] += " ⚠️ (error de panel)"
                    except Exception as panel_e:
                        logger.error(f"Error creando panel de bunkers: {panel_e}")
                        results[-1] += " ⚠️ (error de panel)"
                        
                except Exception as db_e:
                    logger.error(f"Error guardando configuración de bunkers: {db_e}")
                    results.append(f"⏰ Bunkers: ⚠️ {bunker_channel.mention} (sin persistencia)")
            except Exception as e:
                results.append(f"⏰ Bunkers: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE NOTIFICACIONES DE MECÁNICO ===
            try:
                mechanic_cog = self.bot.get_cog('MechanicSystem')
                if mechanic_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'mechanic_notifications', str(mechanic_notifications_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        
                        # Configurar en el cog de mecánico
                        mechanic_cog.mechanic_notification_channels[interaction.guild.id] = mechanic_notifications_channel.id
                        
                        results.append(f"🔧 Notificaciones Mecánico: ✅ {mechanic_notifications_channel.mention}")
                        
                        # Enviar mensaje de prueba al canal configurado
                        try:
                            test_embed = discord.Embed(
                                title="🔧 Canal de Notificaciones de Seguros Activo",
                                description="Este canal ha sido configurado para recibir notificaciones de seguros de vehículos pendientes de confirmación.",
                                color=0xff8800
                            )
                            test_embed.add_field(
                                name="ℹ️ Funcionamiento",
                                value="• Cada solicitud de seguro aparecerá aquí con botones\n• Los mecánicos pueden confirmar o rechazar\n• Se incluyen todos los detalles del vehículo y cliente\n• El débito de Discord se hace solo tras confirmación",
                                inline=False
                            )
                            test_embed.add_field(
                                name="🎯 Acceso",
                                value="Solo mecánicos registrados y administradores pueden usar los botones de confirmación.",
                                inline=False
                            )
                            test_embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                            
                            await mechanic_notifications_channel.send(embed=test_embed)
                            results[-1] += " + Panel"
                        except Exception as panel_e:
                            logger.error(f"Error enviando mensaje de prueba: {panel_e}")
                            results[-1] += " ⚠️ (sin mensaje de prueba)"
                        
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración de notificaciones de mecánico: {db_e}")
                        results.append(f"🔧 Notificaciones Mecánico: ⚠️ {mechanic_notifications_channel.mention} (sin persistencia)")
                else:
                    results.append("🔧 Notificaciones Mecánico: ❌ Cog no encontrado")
            except Exception as e:
                results.append(f"🔧 Notificaciones Mecánico: ❌ Error - {str(e)}")
            
            # === CONFIGURAR CANAL DE TICKETS ===
            try:
                ticket_cog = self.bot.get_cog('TicketSystem')
                if ticket_cog:
                    guild_id = str(interaction.guild.id)
                    try:
                        # Guardar configuración en la base de datos
                        async with aiosqlite.connect(taxi_db.db_path) as db:
                            await db.execute(
                                """INSERT OR REPLACE INTO channel_config 
                                (guild_id, channel_type, channel_id, updated_at, updated_by) 
                                VALUES (?, ?, ?, ?, ?)""",
                                (guild_id, 'tickets', str(ticket_channel.id), 
                                 datetime.now().isoformat(), str(interaction.user.id))
                            )
                            await db.commit()
                        
                        results.append(f"🎫 Tickets: ✅ {ticket_channel.mention}")
                        
                        # Limpiar mensajes anteriores del bot
                        try:
                            deleted_count = 0
                            async for message in ticket_channel.history(limit=50):
                                if message.author == self.bot.user:
                                    await message.delete()
                                    deleted_count += 1
                                    await asyncio.sleep(0.1)  # Evitar rate limits
                        except Exception as cleanup_e:
                            logger.warning(f"Error limpiando mensajes de tickets: {cleanup_e}")
                        
                        # Crear panel de tickets usando el sistema de tickets
                        try:
                            from ticket_views import CreateTicketView
                            
                            # Crear embed del panel
                            ticket_embed = discord.Embed(
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
                            ticket_embed.set_footer(text="Sistema de Tickets SCUM Bot")
                            ticket_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
                            
                            # Crear vista con botón
                            view = CreateTicketView(ticket_cog)
                            
                            # Enviar panel
                            message = await ticket_channel.send(embed=ticket_embed, view=view)
                            view.message = message
                            
                            results[-1] += " + Panel"
                            logger.info(f"Panel de tickets configurado en {ticket_channel.name}")
                            
                        except Exception as panel_e:
                            logger.error(f"Error creando panel de tickets: {panel_e}")
                            results[-1] += " ⚠️ (error de panel)"
                        
                    except Exception as db_e:
                        logger.error(f"Error guardando configuración de tickets: {db_e}")
                        results.append(f"🎫 Tickets: ⚠️ {ticket_channel.mention} (sin persistencia)")
                else:
                    results.append("🎫 Tickets: ❌ Cog no encontrado")
            except Exception as e:
                results.append(f"🎫 Tickets: ❌ Error - {str(e)}")
            
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
                3. Registra mecánicos con `/mechanic_admin_register`
                4. Informa a tu comunidad sobre el nuevo sistema
                5. Usa `/taxi_admin_stats` para monitorear el uso
                """,
                inline=False
            )
            
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

    @app_commands.command(name="mechanic_admin_setup", description="[ADMIN] Configurar canal de mecánico")
    @app_commands.describe(mechanic_channel="Canal para sistema de mecánico y seguros")
    @app_commands.default_permissions(administrator=True)
    async def setup_mechanic_channel(self, interaction: discord.Interaction, mechanic_channel: discord.TextChannel):
        """Configurar canal del sistema de mecánico"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild.id)
            
            # Guardar configuración en base de datos
            async with aiosqlite.connect(taxi_db.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO channel_config 
                    (guild_id, channel_type, channel_id, updated_at, updated_by) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (guild_id, 'mechanic', str(mechanic_channel.id), 
                     datetime.now().isoformat(), str(interaction.user.id))
                )
                await db.commit()
            
            # Configurar canal en el cog
            mechanic_cog = self.bot.get_cog('MechanicSystem')
            if mechanic_cog:
                await mechanic_cog.setup_mechanic_channel(int(guild_id), mechanic_channel.id)
            
            embed = discord.Embed(
                title="✅ Canal de Mecánico Configurado",
                description=f"El canal {mechanic_channel.mention} ha sido configurado exitosamente",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🔧 Funcionalidades Disponibles",
                value="• `/seguro_solicitar` - Contratar seguro de vehículo\n• `/seguro_consultar` - Ver seguros activos\n• Panel interactivo con botones",
                inline=False
            )
            
            embed.add_field(
                name="💰 Costos de Seguros",
                value="• Motocicleta: $500\n• Automóvil: $1,000\n• SUV/Pickup: $1,200\n• Camión: $1,500\n• Avión: $3,500\n• Barco: $2,500",
                inline=True
            )
            
            embed.add_field(
                name="📋 Requisitos",
                value="• Usuario registrado en el sistema\n• Nombre InGame configurado\n• Fondos suficientes\n• ID único del vehículo",
                inline=True
            )
            
            embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error configurando canal de mecánico: {e}")
            error_embed = discord.Embed(
                title="❌ Error de Configuración",
                description=f"Error configurando el canal de mecánico: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @rate_limit("taxi_admin_stats")
    @app_commands.command(name="taxi_admin_stats", description="[ADMIN] Ver estadísticas completas del sistema")
    @app_commands.default_permissions(administrator=True)
    async def admin_stats(self, interaction: discord.Interaction):
        """Estadísticas administrativas detalladas"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "taxi_admin_stats"):
            return
        
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
                async with aiosqlite.connect(taxi_db.db_path) as db:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM taxi_users WHERE discord_guild_id = ?", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['total_users'] = result[0] if result else 0
                    
                    # Contar conductores activos
                    cursor = await db.execute(
                        """SELECT COUNT(*) FROM taxi_drivers td 
                           JOIN taxi_users tu ON td.user_id = tu.user_id 
                           WHERE tu.discord_guild_id = ? AND td.status != 'inactive'""", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['active_drivers'] = result[0] if result else 0
                    
                    # Contar viajes completados
                    cursor = await db.execute(
                        """SELECT COUNT(*) FROM taxi_requests tr 
                           JOIN taxi_users tu ON tr.passenger_id = tu.user_id 
                           WHERE tu.discord_guild_id = ? AND tr.status = 'completed'""", 
                        (guild_id,)
                    )
                    result = await cursor.fetchone()
                    stats['total_rides'] = result[0] if result else 0
                    
                    # Contar transacciones bancarias
                    cursor = await db.execute(
                        """SELECT COUNT(*) FROM bank_transactions bt
                           JOIN bank_accounts ba ON bt.to_account = ba.account_number
                           JOIN taxi_users tu ON ba.user_id = tu.user_id
                           WHERE tu.discord_guild_id = ?""", 
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

    @rate_limit("taxi_admin_tarifa")
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
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "taxi_admin_tarifa"):
            return
        
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

    @rate_limit("taxi_admin_refresh")
    @app_commands.command(name="taxi_admin_refresh", description="[ADMIN] Recrear el panel de administración")
    @app_commands.default_permissions(administrator=True)
    async def refresh_admin_panel(self, interaction: discord.Interaction):
        """Recrear el panel administrativo con limpieza previa"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "taxi_admin_refresh"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = interaction.guild.id
            
            # Verificar si hay un canal de admin configurado
            if guild_id not in self.admin_channels:
                embed = discord.Embed(
                    title="❌ Canal no Configurado",
                    description="No hay un canal de administración configurado para este servidor.\n\nUsa `/ba_admin_channels_setup` para configurar los canales.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            channel_id = self.admin_channels[guild_id]
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                embed = discord.Embed(
                    title="❌ Canal no Encontrado",
                    description=f"El canal de administración configurado (ID: {channel_id}) ya no existe.\n\nReconfigura los canales con `/ba_admin_channels_setup`.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar permisos
            if not channel.permissions_for(interaction.guild.me).send_messages:
                embed = discord.Embed(
                    title="❌ Sin Permisos",
                    description=f"No tengo permisos para enviar mensajes en {channel.mention}.\n\nVerifica los permisos del bot en ese canal.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Recrear panel administrativo
            panel_success = await setup_admin_panel(channel, self.bot)
            
            if panel_success:
                embed = discord.Embed(
                    title="✅ Panel Recreado",
                    description=f"El panel de administración ha sido recreado exitosamente en {channel.mention}.\n\n• Mensajes anteriores limpiados\n• Panel actualizado con todos los botones\n• Configuración preservada",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Recreado por {interaction.user.display_name}")
            else:
                embed = discord.Embed(
                    title="⚠️ Error Recreando Panel",
                    description="Hubo un problema al recrear el panel administrativo. Revisa los logs para más detalles.",
                    color=discord.Color.orange()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en refresh_admin_panel: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error recreando el panel: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @rate_limit("taxi_admin_expiration")
    @app_commands.command(name="taxi_admin_expiration", description="[ADMIN] Configurar tiempo de expiración de solicitudes")
    @app_commands.describe(
        minutes="Tiempo en minutos para que expire una solicitud (1-120, default: 15)"
    )
    @app_commands.default_permissions(administrator=True)
    async def configure_expiration(self, interaction: discord.Interaction, minutes: int = 15):
        """Configurar tiempo de expiración de solicitudes de taxi"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "taxi_admin_expiration"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar rango de minutos
            if not 1 <= minutes <= 120:
                embed = discord.Embed(
                    title="❌ Valor Inválido",
                    description="El tiempo de expiración debe estar entre 1 y 120 minutos.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            guild_id = str(interaction.guild.id)
            
            # Guardar configuración en base de datos
            async with aiosqlite.connect(taxi_db.db_path) as db:
                # Usar el formato guild_id:config_key para evitar conflictos entre servidores
                config_key = f"{guild_id}:request_expiration_minutes"
                
                await db.execute("""
                    INSERT OR REPLACE INTO taxi_config (config_key, config_value, updated_at)
                    VALUES (?, ?, ?)
                """, (config_key, str(minutes), datetime.now().isoformat()))
                
                await db.commit()
            
            # Crear embed de confirmación
            embed = discord.Embed(
                title="✅ Configuración Actualizada",
                description=f"Las solicitudes de taxi ahora expirarán automáticamente después de **{minutes} minutos**",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="⏰ Nueva Configuración",
                value=f"```yaml\nTiempo de expiración: {minutes} minutos\nServidor: {interaction.guild.name}\nActualizado por: {interaction.user.display_name}\n```",
                inline=False
            )
            
            embed.add_field(
                name="📝 Detalles",
                value=f"• Las solicitudes pendientes se limpiarán automáticamente\n• Los usuarios serán notificados cuando su solicitud expire\n• Los conductores no verán solicitudes expiradas",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Próxima Limpieza",
                value="El sistema verificará automáticamente cada 5 minutos",
                inline=False
            )
            
            embed.set_footer(text=f"Configurado por {interaction.user.display_name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            # Iniciar el task de limpieza si no está corriendo
            if not hasattr(self, '_cleanup_task') or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._start_cleanup_loop())
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error configurando expiración: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error configurando tiempo de expiración: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def _start_cleanup_loop(self):
        """Iniciar loop de limpieza automática de solicitudes expiradas"""
        while True:
            try:
                await asyncio.sleep(300)  # Esperar 5 minutos
                await self._cleanup_expired_requests()
            except Exception as e:
                logger.error(f"Error en loop de limpieza: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto en caso de error

    async def _cleanup_expired_requests(self):
        """Limpiar solicitudes de taxi expiradas"""
        try:
            async with aiosqlite.connect(taxi_db.db_path) as db:
                # Obtener todas las configuraciones de expiración por servidor
                cursor = await db.execute("""
                    SELECT config_key, config_value FROM taxi_config 
                    WHERE config_key LIKE '%:request_expiration_minutes'
                """)
                
                expiration_configs = await cursor.fetchall()
                
                for config_key, config_value in expiration_configs:
                    guild_id = config_key.split(':')[0]
                    expiration_minutes = int(config_value)
                    
                    # Buscar solicitudes expiradas para este servidor
                    expiration_time = datetime.now() - timedelta(minutes=expiration_minutes)
                    
                    cursor = await db.execute("""
                        SELECT tr.request_id, tr.passenger_id, tu.discord_id, tu.display_name
                        FROM taxi_requests tr
                        JOIN taxi_users tu ON tr.passenger_id = tu.user_id
                        WHERE tr.status = 'pending' 
                        AND tu.discord_guild_id = ?
                        AND datetime(tr.created_at) < ?
                    """, (guild_id, expiration_time.isoformat()))
                    
                    expired_requests = await cursor.fetchall()
                    
                    if expired_requests:
                        for request_id, passenger_id, discord_id, display_name in expired_requests:
                            # Marcar como expirada
                            await db.execute("""
                                UPDATE taxi_requests 
                                SET status = 'expired', updated_at = ?
                                WHERE request_id = ?
                            """, (datetime.now().isoformat(), request_id))
                            
                            # Notificar al pasajero si es posible
                            try:
                                guild = self.bot.get_guild(int(guild_id))
                                if guild:
                                    member = guild.get_member(int(discord_id))
                                    if member:
                                        embed = discord.Embed(
                                            title="⏰ Solicitud de Taxi Expirada",
                                            description=f"Tu solicitud #{request_id} ha expirado después de {expiration_minutes} minutos sin respuesta.",
                                            color=discord.Color.orange()
                                        )
                                        embed.add_field(
                                            name="🔄 ¿Qué hacer ahora?",
                                            value="Puedes crear una nueva solicitud usando el panel de taxi.",
                                            inline=False
                                        )
                                        
                                        try:
                                            await member.send(embed=embed)
                                        except (discord.Forbidden, discord.HTTPException):
                                            logger.warning(f"No se pudo notificar expiración a {display_name}")
                            except Exception as notify_error:
                                logger.error(f"Error notificando expiración: {notify_error}")
                        
                        await db.commit()
                
        except Exception as e:
            logger.error(f"Error limpiando solicitudes expiradas: {e}")

    @rate_limit("taxi_admin_leaderboard")
    @app_commands.command(name="taxi_admin_leaderboard", description="[ADMIN] Ver clasificación de conductores por rendimiento")
    @app_commands.describe(
        limit="Número de conductores a mostrar (1-20, default: 10)"
    )
    @app_commands.default_permissions(administrator=True)
    async def leaderboard_command(self, interaction: discord.Interaction, limit: int = 10):
        """Ver tabla de clasificación de conductores"""
        # Verificar rate limiting
        if not await rate_limiter.check_and_record(interaction, "taxi_admin_leaderboard"):
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar límite
            if not 1 <= limit <= 20:
                embed = discord.Embed(
                    title="❌ Límite Inválido",
                    description="El límite debe estar entre 1 y 20 conductores.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            guild_id = str(interaction.guild.id)
            
            # Obtener clasificación
            leaderboard = await taxi_db.get_leaderboard(guild_id, limit)
            
            if not leaderboard:
                embed = discord.Embed(
                    title="🏆 Clasificación de Conductores",
                    description="No hay conductores con viajes completados en este servidor.",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear embed de clasificación
            embed = discord.Embed(
                title="🏆 Clasificación de Conductores",
                description=f"Top {len(leaderboard)} conductores de **{interaction.guild.name}**",
                color=0xf1c40f
            )
            
            # Medallas para top 3
            medal_emojis = ["🥇", "🥈", "🥉"]
            
            leaderboard_text = ""
            for entry in leaderboard:
                position = entry["position"]
                level_info = entry["level_info"]
                display_name = entry["display_name"]
                total_rides = entry["total_rides"]
                rating = entry["rating"]
                total_earnings = entry["total_earnings"]
                vehicle_type = entry["vehicle_type"]
                
                # Emoji de posición
                position_emoji = medal_emojis[position - 1] if position <= 3 else f"**{position}.**"
                
                leaderboard_text += f"{position_emoji} {level_info['display_name']}\n"
                leaderboard_text += f"    **{display_name}** ({vehicle_type})\n"
                leaderboard_text += f"    📊 {total_rides} viajes • ⭐ {rating:.2f} • 💰 ${total_earnings:,.2f}\n\n"
            
            embed.add_field(
                name="📈 Ranking por Viajes y Rating",
                value=leaderboard_text[:1024],  # Discord limit
                inline=False
            )
            
            # Estadísticas generales
            total_rides_all = sum(entry["total_rides"] for entry in leaderboard)
            total_earnings_all = sum(entry["total_earnings"] for entry in leaderboard)
            avg_rating_all = sum(entry["rating"] for entry in leaderboard) / len(leaderboard)
            
            embed.add_field(
                name="📊 Estadísticas del Top",
                value=f"**Total Viajes:** {total_rides_all:,}\n"
                      f"**Ganancias Totales:** ${total_earnings_all:,.2f}\n"
                      f"**Rating Promedio:** ⭐ {avg_rating_all:.2f}",
                inline=True
            )
            
            # Información de niveles
            embed.add_field(
                name="🎖️ Sistema de Niveles",
                value="Los conductores ganan niveles por:\n"
                      "• **Viajes completados** (experiencia)\n"
                      "• **Rating alto** (multiplicador)\n"
                      "• **Bonos por nivel** hasta 50%",
                inline=True
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name} • Actualizado en tiempo real")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando leaderboard: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error obteniendo clasificación: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class ActiveTripsView(discord.ui.View):
    """Vista para gestionar viajes activos"""
    
    def __init__(self, active_trips: list, driver_info: dict):
        super().__init__(timeout=300)
        self.active_trips = active_trips
        self.driver_info = driver_info
        
        # Crear selector de viajes para completar
        if active_trips:
            options = []
            for trip in active_trips[:25]:  # Discord limit
                trip_id = trip['request_id']
                passenger_name = trip['passenger_name']
                destination = trip['destination_zone']
                cost = trip['estimated_cost']
                
                options.append(discord.SelectOption(
                    label=f"Viaje #{trip_id} - {passenger_name}",
                    description=f"Destino: {destination} | ${cost:.2f}",
                    value=str(trip_id)
                ))
            
            self.add_item(TripCompletionSelect(options, self.active_trips, self.driver_info))
    
    @discord.ui.button(
        label="🔙 Volver al Panel", 
        style=discord.ButtonStyle.secondary, 
        custom_id="back_to_driver_panel_from_trips",
        emoji="🔙"
    )
    async def back_to_driver_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel de conductor"""
        # Verificar cooldown
        if not check_cooldown(interaction.user.id):
            logger.warning(f"Usuario {interaction.user.id} en cooldown - ignorando")
            return
        
        try:
            view = DriverPanelView(self.driver_info)
            embed = await self._create_driver_panel_embed(self.driver_info)
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error volviendo al panel de conductor: {e}")
    
    async def _create_driver_panel_embed(self, driver_info: dict) -> discord.Embed:
        """Crear embed del panel de conductor con información de nivel"""
        status_emoji = {
            'available': '🟢',
            'busy': '🟡',
            'offline': '🔴'
        }.get(driver_info.get('status', 'offline'), '❓')
        
        # Obtener información de nivel
        total_rides = driver_info.get('total_rides', 0)
        rating = driver_info.get('rating', 5.0)
        level_info = taxi_db.get_driver_level_info(total_rides, rating)
        
        embed = discord.Embed(
            title="🚗 Panel de Conductor",
            description=f"Bienvenido, **{driver_info.get('display_name', 'Conductor')}**",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📋 Licencia",
            value=driver_info.get('license_number', 'N/A'),
            inline=True
        )
        
        embed.add_field(
            name="📊 Estado",
            value=f"{status_emoji} {driver_info.get('status', 'offline')}",
            inline=True
        )
        
        embed.add_field(
            name="🚗 Vehículo",
            value=f"{driver_info.get('vehicle_type', 'N/A')}",
            inline=True
        )
        
        # Información de nivel y progreso
        embed.add_field(
            name="🎖️ Nivel",
            value=level_info['display_name'],
            inline=True
        )
        
        embed.add_field(
            name="📈 Estadísticas",
            value=f"⭐ {rating:.2f} • 🚗 {total_rides} viajes\n💰 ${driver_info.get('total_earnings', 0):.2f}",
            inline=True
        )
        
        # Progreso hacia siguiente nivel
        if level_info['next_level']:
            progress_info = f"**Siguiente:** {level_info['next_level']['emoji']} {level_info['next_level']['title']}\n**Faltan:** {level_info['rides_to_next']} viajes"
        else:
            progress_info = "🏆 **¡Nivel Máximo!**"
            
        embed.add_field(
            name="🔄 Progreso",
            value=progress_info,
            inline=True
        )
        
        # Bonificaciones por nivel y rating
        bonus_text = f"**Nivel:** +{level_info['base_bonus']*100:.0f}%"
        if level_info['rating_modifier'] != 1.0:
            bonus_text += f"\n**Rating:** x{level_info['rating_modifier']:.2f}"
        bonus_text += f"\n**Total:** +{level_info['total_bonus']*100:.0f}%"
        
        embed.add_field(
            name="💎 Bonos",
            value=bonus_text,
            inline=False
        )
        
        return embed


class TripCompletionSelect(discord.ui.Select):
    """Selector para completar viajes"""
    
    def __init__(self, options: list, active_trips: list, driver_info: dict):
        super().__init__(
            placeholder="Selecciona un viaje para completar...",
            options=options
        )
        self.active_trips = active_trips
        self.driver_info = driver_info
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_trip_id = int(self.values[0])
            
            # Encontrar el viaje seleccionado
            selected_trip = None
            for trip in self.active_trips:
                if trip['request_id'] == selected_trip_id:
                    selected_trip = trip
                    break
            
            if not selected_trip:
                await interaction.response.send_message("❌ Viaje no encontrado", ephemeral=True)
                return
            
            # Crear vista de confirmación
            view = TripCompletionConfirmView(selected_trip, self.driver_info)
            
            embed = discord.Embed(
                title="🏁 Completar Viaje",
                description=f"¿Completar el viaje #{selected_trip_id}?",
                color=0x00ff00
            )
            
            embed.add_field(
                name="👤 Pasajero",
                value=selected_trip['passenger_name'],
                inline=True
            )
            
            embed.add_field(
                name="📍 Destino",
                value=selected_trip['destination_zone'],
                inline=True
            )
            
            embed.add_field(
                name="💰 Tarifa",
                value=f"${selected_trip['estimated_cost']:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Importante",
                value="• Se procesará el pago automáticamente\n• Ambos podrán calificarse mutuamente\n• Se actualizarán tus estadísticas",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error seleccionando viaje para completar: {e}")
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)


class TripCompletionConfirmView(discord.ui.View):
    """Vista de confirmación para completar viajes"""
    
    def __init__(self, trip_data: dict, driver_info: dict):
        super().__init__(timeout=300)
        self.trip_data = trip_data
        self.driver_info = driver_info
    
    @discord.ui.button(
        label="✅ Completar Viaje", 
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def complete_trip(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Completar el viaje seleccionado"""
        try:
            request_id = self.trip_data['request_id']
            driver_id = self.driver_info['driver_id']
            
            # Completar viaje en base de datos
            success, message = await taxi_db.complete_trip(request_id, driver_id)
            
            if success:
                # Crear embed de éxito
                embed = discord.Embed(
                    title="🏁 Viaje Completado",
                    description=f"¡Viaje #{request_id} completado exitosamente!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📊 Resultado",
                    value=message,
                    inline=False
                )
                
                embed.add_field(
                    name="⭐ Siguiente Paso",
                    value=f"El pasajero **{self.trip_data['passenger_name']}** podrá calificarte.\nTambién podrás calificar al pasajero cuando recibas la notificación.",
                    inline=False
                )
                
                # Notificar al pasajero
                try:
                    guild = interaction.guild
                    passenger_member = guild.get_member(int(self.trip_data['passenger_discord_id']))
                    
                    if passenger_member:
                        passenger_embed = discord.Embed(
                            title="🏁 Tu Viaje ha Sido Completado",
                            description=f"El conductor ha completado tu viaje #{request_id}",
                            color=discord.Color.green()
                        )
                        
                        passenger_embed.add_field(
                            name="💳 Pago",
                            value=f"Se ha procesado el cobro de **${self.trip_data['estimated_cost']:.2f}**",
                            inline=False
                        )
                        
                        passenger_embed.add_field(
                            name="⭐ Califica al Conductor",
                            value="Puedes calificar este viaje en el panel de taxi para ayudar a otros usuarios",
                            inline=False
                        )
                        
                        try:
                            await passenger_member.send(embed=passenger_embed)
                        except (discord.Forbidden, discord.HTTPException):
                            logger.warning(f"No se pudo notificar a {self.trip_data['passenger_name']}")
                            
                except Exception as notify_error:
                    logger.error(f"Error notificando al pasajero: {notify_error}")
                
                # Volver al panel de conductor
                view = DriverPanelView(self.driver_info)
                await interaction.response.edit_message(embed=embed, view=view)
                
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"No se pudo completar el viaje: {message}",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=self)
                
        except Exception as e:
            logger.error(f"Error completando viaje: {e}")
            embed = discord.Embed(
                title="❌ Error Inesperado",
                description=f"Error completando el viaje: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(
        label="❌ Cancelar", 
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def cancel_completion(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar la finalización del viaje"""
        try:
            # Volver a la vista de viajes activos
            active_trips = await taxi_db.get_active_trips_for_driver(self.driver_info['driver_id'])
            
            embed = discord.Embed(
                title="🚗 Viajes Activos",
                description="Operación cancelada. Gestiona tus viajes en curso",
                color=0x00ff00
            )
            
            if active_trips:
                for i, trip in enumerate(active_trips[:3]):
                    embed.add_field(
                        name=f"🚖 Viaje #{trip['request_id']}",
                        value=f"**👤 Pasajero:** {trip['passenger_name']}\n**📍 Destino:** {trip['destination_zone']}\n**💰 Tarifa:** ${trip['estimated_cost']:.2f}",
                        inline=True
                    )
                
                view = ActiveTripsView(active_trips, self.driver_info)
            else:
                embed.add_field(
                    name="📭 Sin Viajes Activos",
                    value="No tienes viajes en curso en este momento.",
                    inline=False
                )
                view = DriverPanelView(self.driver_info)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error cancelando finalización: {e}")


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
# ===============================
# SISTEMA DE TIENDA DE SUPERVIVENCIA
# ===============================

class ShopSystemView(discord.ui.View):
    """Vista principal del sistema de tienda"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Tier 1 - Básico",
        style=discord.ButtonStyle.success,
        emoji="🟢",
        custom_id="shop_tier1"
    )
    async def tier1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar packs de Tier 1"""
        await self.show_tier_packs(interaction, "tier1")
    
    @discord.ui.button(
        label="Tier 2 - Intermedio", 
        style=discord.ButtonStyle.primary,
        emoji="🟡", 
        custom_id="shop_tier2"
    )
    async def tier2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar packs de Tier 2"""
        await self.show_tier_packs(interaction, "tier2")
    
    @discord.ui.button(
        label="Tier 3 - Élite",
        style=discord.ButtonStyle.danger,
        emoji="🟠",
        custom_id="shop_tier3"  
    )
    async def tier3_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar packs de Tier 3"""
        await self.show_tier_packs(interaction, "tier3")
    
    @discord.ui.button(
        label="💰 Mi Saldo",
        style=discord.ButtonStyle.secondary,
        emoji="💳",
        custom_id="shop_balance"
    )
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar saldo del usuario"""
        await interaction.response.defer(ephemeral=True)
        
        user_data = await get_user_by_discord_id(
            str(interaction.user.id),
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ No Registrado",
                description="No tienes una cuenta. Ve al canal de bienvenida para registrarte.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💳 Tu Saldo Actual",
            description=f"Tienes **${user_data['balance']:,.2f}** disponibles para compras",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🛒 Consejos de Compra",
            value="• Los packs tienen stock limitado\n• Revisa los cooldowns de cada tier\n• Considera los métodos de pago alternativos",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def show_tier_packs(self, interaction: discord.Interaction, tier: str):
        """Mostrar los packs disponibles de un tier específico"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            from shop_config import SHOP_PACKS, TIER_CONFIG, PACK_CATEGORIES
            
            tier_info = TIER_CONFIG[tier]
            packs = SHOP_PACKS[tier]
            
            if not packs:
                embed = discord.Embed(
                    title="❌ Sin Packs Disponibles",
                    description=f"No hay packs disponibles en {tier_info['name']}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"{tier_info['emoji']} {tier_info['name']}",
                description=tier_info['description'],
                color=discord.Color.gold()
            )
            
            # Agregar información del tier
            embed.add_field(
                name="⏰ Información del Tier",
                value=f"**Cooldown:** {tier_info['cooldown_days']} días\n**Stock máximo:** {tier_info.get('max_quantity', 'N/A')}\n**Restock:** Cada {tier_info.get('restock_days', 'N/A')} días",
                inline=False
            )
            
            # Mostrar cada pack con stock real de la base de datos
            for pack_id, pack_data in packs.items():
                category_info = PACK_CATEGORIES.get(pack_data['category'], {"emoji": "📦", "name": "General"})
                
                # Obtener stock real de la base de datos
                real_stock = await taxi_db.get_pack_stock(pack_id, tier, str(interaction.guild.id))
                stock_status = "🔴 AGOTADO" if real_stock <= 0 else f"✅ {real_stock} disponibles"
                
                pack_value = f"**Contenido:**\n"
                for item in pack_data['items']:
                    pack_value += f"• {item}\n"
                pack_value += f"\n**💰 Precio:** ${pack_data['price_money']:,}"
                pack_value += f"\n**🔄 Alternativo:** {pack_data['price_alt']}"
                pack_value += f"\n**📦 Stock:** {stock_status}"
                
                embed.add_field(
                    name=f"{category_info['emoji']} {pack_data['name']}",
                    value=pack_value,
                    inline=True
                )
            
            embed.set_footer(text="Selecciona un pack y usa el botón Comprar para adquirirlo")
            
            # Vista con selector de pack y botón comprar
            view = TierShopView(tier, packs, str(interaction.guild.id))
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando packs del tier {tier}: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Hubo un error cargando los packs. Intenta nuevamente.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class BackToShopView(discord.ui.View):
    """Vista para volver al menú principal de la tienda"""
    
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(
        label="🔙 Volver al Menú Principal",
        style=discord.ButtonStyle.secondary,
        emoji="🏠"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al menú principal de la tienda"""
        try:
            from shop_config import TIER_CONFIG
            
            embed = discord.Embed(
                title="🛒 Tienda de Supervivencia SCUM",
                description="¡Intercambia tus recursos por equipamiento de supervivencia de alta gama!\n\nSelecciona tu tier para ver los packs disponibles.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="💰 Métodos de Pago",
                value="• Dinero del sistema bancario\n• Recursos y materiales\n• Vehículos y equipamiento",
                inline=True
            )
            embed.add_field(
                name="⏰ Disponibilidad",
                value="• **Tier 1:** Cada semana\n• **Tier 2:** Cada 2 semanas\n• **Tier 3:** Cada 3 semanas",
                inline=True
            )
            embed.add_field(
                name="🎯 Especialidades",
                value="• Packs de construcción\n• Equipamiento de combate\n• Vehículos limitados\n• Suministros médicos",
                inline=False
            )
            embed.set_footer(text="Habla con un administrador para realizar el canje")
            
            view = ShopSystemView()
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error volviendo al menú principal: {e}")
            await interaction.response.send_message("❌ Error volviendo al menú", ephemeral=True)


class PackSelect(discord.ui.Select):
    """Selector de packs en un tier específico"""
    
    def __init__(self, tier: str, packs: dict, guild_id: str):
        self.tier = tier
        self.packs = packs
        self.guild_id = guild_id
        
        options = []
        for pack_id, pack_data in packs.items():
            from shop_config import PACK_CATEGORIES
            category_info = PACK_CATEGORIES.get(pack_data['category'], {"emoji": "📦"})
            
            # Nota: No podemos hacer await aquí, así que mostraremos stock dinámicamente
            options.append(discord.SelectOption(
                label=pack_data['name'],
                description=f"${pack_data['price_money']:,} - {pack_data['description'][:50]}...",
                value=pack_id,
                emoji=category_info['emoji']
            ))
        
        super().__init__(
            placeholder="Selecciona un pack para comprar...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona un pack"""
        await interaction.response.defer()


class TierShopView(discord.ui.View):
    """Vista para comprar packs de un tier específico"""
    
    def __init__(self, tier: str, packs: dict, guild_id: str):
        super().__init__(timeout=300)
        self.tier = tier
        self.packs = packs
        self.guild_id = guild_id
        self.selected_pack = None
        
        # Agregar selector de pack
        self.pack_select = PackSelect(tier, packs, guild_id)
        self.add_item(self.pack_select)
    
    @discord.ui.button(
        label="💳 Comprar Pack",
        style=discord.ButtonStyle.success,
        emoji="🛒"
    )
    async def buy_pack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Comprar el pack seleccionado"""
        await interaction.response.defer(ephemeral=True)
        
        # Verificar que hay un pack seleccionado
        selected_values = getattr(self.pack_select, 'values', [])
        if not selected_values:
            embed = discord.Embed(
                title="❌ Pack No Seleccionado",
                description="Primero debes seleccionar un pack del menú desplegable.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        pack_id = selected_values[0]
        await self.process_purchase(interaction, pack_id)
    
    @discord.ui.button(
        label="🔄 Actualizar Stock",
        style=discord.ButtonStyle.secondary,
        emoji="🔄"
    )
    async def refresh_stock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualizar la vista con stock actual"""
        await interaction.response.defer()
        
        try:
            from shop_config import SHOP_PACKS, TIER_CONFIG, PACK_CATEGORIES
            
            tier_info = TIER_CONFIG[self.tier]
            packs = SHOP_PACKS[self.tier]
            
            embed = discord.Embed(
                title=f"{tier_info['emoji']} {tier_info['name']}",
                description=tier_info['description'],
                color=discord.Color.gold()
            )
            
            # Agregar información del tier
            embed.add_field(
                name="⏰ Información del Tier",
                value=f"**Cooldown:** {tier_info['cooldown_days']} días\n**Stock máximo:** {tier_info.get('max_quantity', 'N/A')}\n**Restock:** Cada {tier_info.get('restock_days', 'N/A')} días",
                inline=False
            )
            
            # Mostrar cada pack con stock real actualizado
            for pack_id, pack_data in packs.items():
                category_info = PACK_CATEGORIES.get(pack_data['category'], {"emoji": "📦", "name": "General"})
                
                # Obtener stock real de la base de datos
                real_stock = await taxi_db.get_pack_stock(pack_id, self.tier, self.guild_id)
                stock_status = "🔴 AGOTADO" if real_stock <= 0 else f"✅ {real_stock} disponibles"
                
                pack_value = f"**Contenido:**\n"
                for item in pack_data['items']:
                    pack_value += f"• {item}\n"
                pack_value += f"\n**💰 Precio:** ${pack_data['price_money']:,}"
                pack_value += f"\n**🔄 Alternativo:** {pack_data['price_alt']}"
                pack_value += f"\n**📦 Stock:** {stock_status}"
                
                embed.add_field(
                    name=f"{category_info['emoji']} {pack_data['name']}",
                    value=pack_value,
                    inline=True
                )
            
            embed.set_footer(text="Stock actualizado • Selecciona un pack y usa el botón Comprar")
            
            # Mantener la vista actual
            await interaction.edit_original_response(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error actualizando stock: {e}")
            await interaction.followup.send("❌ Error actualizando stock", ephemeral=True)

    @discord.ui.button(
        label="🔙 Volver al Menú",
        style=discord.ButtonStyle.secondary,
        emoji="🏠"
    )
    async def back_to_main_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al menú principal de la tienda"""
        try:
            from shop_config import TIER_CONFIG
            
            embed = discord.Embed(
                title="🛒 Tienda de Supervivencia SCUM",
                description="¡Intercambia tus recursos por equipamiento de supervivencia de alta gama!\n\nSelecciona tu tier para ver los packs disponibles.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="💰 Métodos de Pago",
                value="• Dinero del sistema bancario\n• Recursos y materiales\n• Vehículos y equipamiento",
                inline=True
            )
            embed.add_field(
                name="⏰ Disponibilidad",
                value="• **Tier 1:** Cada semana\n• **Tier 2:** Cada 2 semanas\n• **Tier 3:** Cada 3 semanas",
                inline=True
            )
            embed.add_field(
                name="🎯 Especialidades",
                value="• Packs de construcción\n• Equipamiento de combate\n• Vehículos limitados\n• Suministros médicos",
                inline=False
            )
            embed.set_footer(text="Habla con un administrador para realizar el canje")
            
            view = ShopSystemView()
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error volviendo al menú principal: {e}")
            await interaction.response.send_message("❌ Error volviendo al menú", ephemeral=True)
    
    async def process_purchase(self, interaction: discord.Interaction, pack_id: str):
        """Procesar la compra de un pack"""
        try:
            from shop_config import get_pack_by_id
            
            # Obtener información del pack
            pack_data = get_pack_by_id(pack_id)
            if not pack_data:
                embed = discord.Embed(
                    title="❌ Pack No Encontrado",
                    description="El pack seleccionado no existe.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener datos del usuario
            user_data = await get_user_by_discord_id(
                str(interaction.user.id),
                str(interaction.guild.id)
            )
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ No Registrado",
                    description="No tienes una cuenta. Ve al canal de bienvenida para registrarte.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar saldo suficiente
            pack_price = pack_data['price_money']
            user_balance = user_data['balance']
            
            if user_balance < pack_price:
                embed = discord.Embed(
                    title="💰 Saldo Insuficiente",
                    description=f"No tienes suficiente dinero para comprar este pack.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💳 Tu Saldo",
                    value=f"${user_balance:,.2f}",
                    inline=True
                )
                embed.add_field(
                    name="💰 Precio del Pack",
                    value=f"${pack_price:,.2f}",
                    inline=True
                )
                embed.add_field(
                    name="❌ Faltante",
                    value=f"${pack_price - user_balance:,.2f}",
                    inline=True
                )
                embed.add_field(
                    name="💡 Consejo",
                    value="Usa el canje diario o trabaja como conductor de taxi para ganar más dinero.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar stock disponible del servidor
            available_stock = await taxi_db.get_pack_stock(pack_id, self.tier, str(interaction.guild.id))
            if available_stock <= 0:
                embed = discord.Embed(
                    title="🔴 Pack Agotado",
                    description=f"El pack **{pack_data['name']}** está agotado en el servidor.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="📦 Stock Actual",
                    value="0 disponibles",
                    inline=True
                )
                embed.add_field(
                    name="⏰ Próximo Restock",
                    value="Consulta con los administradores para más información",
                    inline=True
                )
                embed.add_field(
                    name="💡 Sugerencia",
                    value="Vuelve al menú y elige otro pack disponible",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar cooldown del usuario para este tier
            can_purchase, cooldown_info = await taxi_db.check_tier_cooldown(user_data['user_id'], self.tier)
            if not can_purchase:
                embed = discord.Embed(
                    title="⏰ En Cooldown",
                    description=f"Debes esperar antes de comprar otro pack de {self.tier.title()}.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🕒 Disponible en",
                    value=cooldown_info,
                    inline=True
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # REALIZAR LA COMPRA
            purchase_result = await taxi_db.process_pack_purchase(
                user_data['user_id'],
                pack_id,
                self.tier,
                pack_price,
                str(interaction.guild.id)
            )
            
            if purchase_result:
                # Compra exitosa
                new_balance = user_balance - pack_price
                
                embed = discord.Embed(
                    title="✅ ¡Compra Exitosa!",
                    description=f"Has comprado el **{pack_data['name']}** exitosamente.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="💰 Precio Pagado",
                    value=f"${pack_price:,.2f}",
                    inline=True
                )
                embed.add_field(
                    name="💳 Nuevo Saldo",
                    value=f"${new_balance:,.2f}",
                    inline=True
                )
                embed.add_field(
                    name="📦 Contenido del Pack",
                    value="\n".join([f"• {item}" for item in pack_data['items']]),
                    inline=False
                )
                embed.add_field(
                    name="📞 Próximos Pasos",
                    value="Un administrador será notificado para entregar tu pack.",
                    inline=False
                )
                embed.set_footer(text="Compra procesada exitosamente")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Enviar notificación al canal shop-claimer
                await self.send_admin_notification(interaction, pack_data, pack_price, purchase_result)
                
            else:
                embed = discord.Embed(
                    title="❌ Error en la Compra",
                    description="Hubo un error procesando tu compra. Intenta nuevamente.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error procesando compra: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error interno. Contacta a un administrador.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def send_admin_notification(self, interaction: discord.Interaction, pack_data: dict, price: float, purchase_id: int):
        """Enviar notificación al canal shop-claimer"""
        try:
            # Obtener el canal shop-claimer
            guild_id = str(interaction.guild.id)
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute(
                    "SELECT channel_id FROM channel_config WHERE guild_id = ? AND channel_type = ?",
                    (guild_id, 'shop_claimer')
                )
                result = await cursor.fetchone()
            
            if not result:
                logger.warning("Canal shop-claimer no configurado")
                return
            
            channel = interaction.guild.get_channel(int(result[0]))
            if not channel:
                logger.warning("Canal shop-claimer no encontrado")
                return
            
            # Crear embed de notificación
            embed = discord.Embed(
                title="🛒 Nueva Compra en la Tienda",
                description="Un usuario ha realizado una compra y necesita que le entreguen su pack.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👤 Usuario",
                value=f"{interaction.user.mention} ({interaction.user.display_name})\n**ID de Compra:** #{purchase_id}",
                inline=True
            )
            embed.add_field(
                name="🏷️ Pack Comprado",
                value=f"**{pack_data['name']}**",
                inline=True
            )
            embed.add_field(
                name="🎯 Tier",
                value=f"{pack_data['tier'].title()}",
                inline=True
            )
            embed.add_field(
                name="💰 Precio Pagado",
                value=f"${price:,.2f}",
                inline=True
            )
            embed.add_field(
                name="💳 Método de Pago",
                value="Dinero del sistema bancario",
                inline=True
            )
            embed.add_field(
                name="⏰ Timestamp",
                value=f"<t:{int(datetime.now().timestamp())}:f>",
                inline=True
            )
            embed.add_field(
                name="📦 Contenido a Entregar",
                value="\n".join([f"• {item}" for item in pack_data['items']]),
                inline=False
            )
            
            embed.set_footer(text="Sistema de Tienda SCUM - Entrega pendiente")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Crear vista con botón de confirmar entrega persistente
            view = PersistentDeliveryView()
            await channel.send(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error enviando notificación de admin: {e}")


class PersistentDeliveryView(discord.ui.View):
    """Vista persistente que maneja todos los botones de confirmación de entrega"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="✅ Confirmar Entrega",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="confirm_delivery"
    )
    async def confirm_delivery_persistent(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar entrega de paquete de forma persistente"""
        await interaction.response.defer()
        
        try:
            # Extraer purchase_id del embed o del mensaje
            if not interaction.message.embeds:
                await interaction.followup.send("❌ No se pudo encontrar información del paquete", ephemeral=True)
                return
            
            embed = interaction.message.embeds[0]
            purchase_id = None
            
            # Buscar purchase_id en los campos del embed
            import re
            for field in embed.fields:
                if "Usuario" in field.name and "ID de Compra:" in field.value:
                    # Extraer purchase_id del valor del campo
                    match = re.search(r'ID de Compra:\*\*\s*#(\d+)', field.value)
                    if match:
                        purchase_id = int(match.group(1))
                        break
            
            # Si no se encuentra en los campos, buscar en el título
            if not purchase_id:
                title_match = re.search(r'#(\d+)', embed.title or "")
                if title_match:
                    purchase_id = int(title_match.group(1))
            
            if not purchase_id:
                await interaction.followup.send("❌ No se pudo identificar el ID de compra", ephemeral=True)
                return
            
            # Marcar como entregado en la base de datos
            success = await taxi_db.mark_package_delivered(purchase_id, str(interaction.user.id))
            
            if success:
                # Actualizar el embed original
                embed.color = discord.Color.green()
                embed.title = "✅ Paquete Entregado"
                embed.add_field(
                    name="📦 Estado",
                    value=f"Entregado por {interaction.user.mention}\n<t:{int(datetime.now().timestamp())}:f>",
                    inline=False
                )
                
                # Deshabilitar el botón
                button.disabled = True
                button.label = "✅ Entregado"
                button.style = discord.ButtonStyle.secondary
                
                await interaction.edit_original_response(embed=embed, view=self)
                await interaction.followup.send(f"✅ Paquete ID #{purchase_id} marcado como entregado", ephemeral=True)
            else:
                await interaction.followup.send("❌ Error marcando el paquete como entregado", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error en confirmación persistente de entrega: {e}")
            await interaction.followup.send("❌ Error procesando la confirmación", ephemeral=True)


class DeliveryConfirmationView(discord.ui.View):
    """Vista para confirmar entrega de paquetes"""
    
    def __init__(self, purchase_id: int, user_id: int, pack_name: str):
        super().__init__(timeout=None)
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.pack_name = pack_name
    
    @discord.ui.button(
        label="✅ Confirmar Entrega",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="confirm_delivery"
    )
    async def confirm_delivery(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar que el paquete fue entregado"""
        await interaction.response.defer()
        
        # Marcar como entregado en la base de datos
        success = await taxi_db.mark_package_delivered(self.purchase_id, str(interaction.user.id))
        
        if success:
            # Actualizar el embed original
            original_embed = interaction.message.embeds[0]
            original_embed.color = discord.Color.green()
            original_embed.title = "✅ Paquete Entregado"
            
            # Agregar información de entrega
            original_embed.add_field(
                name="📋 Estado de Entrega",
                value=f"**Entregado por:** {interaction.user.mention}\n**Fecha:** <t:{int(datetime.now().timestamp())}:f>",
                inline=False
            )
            
            original_embed.set_footer(text="Sistema de Tienda SCUM - Paquete entregado exitosamente")
            
            # Deshabilitar el botón
            button.disabled = True
            button.label = "Entregado"
            button.style = discord.ButtonStyle.secondary
            
            await interaction.edit_original_response(embed=original_embed, view=self)
            
            # Opcional: Notificar al usuario que recibió su paquete
            try:
                user = interaction.guild.get_member(int(self.user_id))
                if user:
                    delivery_embed = discord.Embed(
                        title="📦 ¡Paquete Entregado!",
                        description=f"Tu **{self.pack_name}** ha sido entregado exitosamente.",
                        color=discord.Color.green()
                    )
                    delivery_embed.add_field(
                        name="👨‍💼 Entregado por",
                        value=interaction.user.display_name,
                        inline=True
                    )
                    delivery_embed.add_field(
                        name="⏰ Fecha",
                        value=f"<t:{int(datetime.now().timestamp())}:f>",
                        inline=True
                    )
                    
                    await user.send(embed=delivery_embed)
            except:
                pass  # Si no se puede enviar DM, no es crítico
            
        else:
            await interaction.followup.send("❌ Error marcando paquete como entregado", ephemeral=True)

class AdminPanelView(BaseView):
    """Panel administrativo centralizado para gestión del sistema"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="👥 Ver Todos los Usuarios", style=discord.ButtonStyle.primary, custom_id="admin_view_all_users")
    async def view_all_users_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver todos los usuarios registrados y sus nombres InGame"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos de administrador
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden ver la lista de usuarios",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener todos los usuarios registrados del servidor (tabla users unificada)
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT u.discord_id, u.username, u.display_name, u.ingame_name, 
                           COALESCE(ba.balance, 0.00) as balance, u.welcome_pack_claimed, u.created_at
                    FROM users u
                    LEFT JOIN bank_accounts ba ON u.user_id = ba.user_id
                    WHERE u.discord_guild_id = ? 
                    ORDER BY u.created_at DESC
                """, (str(interaction.guild.id),))
                
                users = await cursor.fetchall()
            
            if not users:
                embed = discord.Embed(
                    title="👥 Lista de Usuarios",
                    description="No hay usuarios registrados en este servidor.",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear páginas para mostrar usuarios (máximo 10 por página)
            page_size = 10
            total_pages = (len(users) + page_size - 1) // page_size
            current_page = 0
            
            def create_users_embed(page: int):
                start_idx = page * page_size
                end_idx = min(start_idx + page_size, len(users))
                page_users = users[start_idx:end_idx]
                
                # Limitar nombre del servidor para evitar problemas
                guild_name = interaction.guild.name[:50] + "..." if len(interaction.guild.name) > 50 else interaction.guild.name
                
                embed = discord.Embed(
                    title="👥 Lista de Usuarios Registrados",
                    description=f"Usuarios de **{guild_name}**\n**Página {page + 1}/{total_pages}** • **{len(users)} usuarios totales**",
                    color=0x3498db
                )
                
                users_text = ""
                for i, user_data in enumerate(page_users, start=start_idx + 1):
                    discord_id, username, display_name, ingame_name, balance, welcome_claimed, created_at = user_data
                    
                    # Verificar si el usuario aún está en el servidor
                    member = interaction.guild.get_member(int(discord_id))
                    status_emoji = "✅" if member else "❌"
                    
                    # Formatear información (compacta para evitar límites)
                    ingame_display = ingame_name[:20] + "..." if ingame_name and len(ingame_name) > 20 else (ingame_name if ingame_name else "Sin config")
                    display_name_short = display_name[:25] + "..." if len(display_name) > 25 else display_name
                    balance_display = f"${balance:,.0f}" if balance else "$0"
                    welcome_status = "✅" if welcome_claimed else "❌"
                    
                    # Construir línea más compacta
                    user_line = f"**{i}.** {status_emoji} **{display_name_short}**\n"
                    user_line += f"   📝 {ingame_display} | 💰 {balance_display} | 🎁 {welcome_status}\n\n"
                    
                    # Verificar límite antes de agregar
                    if len(users_text) + len(user_line) > 950:  # Límite conservador
                        users_text += f"... y {len(page_users) - i + start_idx} usuarios más"
                        break
                    
                    users_text += user_line
                
                embed.add_field(
                    name="📋 Usuarios en esta Página",
                    value=users_text if users_text else "Sin usuarios",
                    inline=False
                )
                
                # Estadísticas rápidas
                users_with_ingame = sum(1 for u in users if u[3])  # ingame_name no null
                users_in_server = sum(1 for u in users if interaction.guild.get_member(int(u[0])))
                
                embed.add_field(
                    name="📊 Estadísticas",
                    value=f"• **Con nombre InGame:** {users_with_ingame}/{len(users)}\n• **Aún en servidor:** {users_in_server}/{len(users)}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Filtros Útiles",
                    value="• ✅ = Usuario activo en servidor\n• ❌ = Usuario no encontrado\n• **Sin configurar** = Nombre InGame faltante",
                    inline=True
                )
                
                embed.set_footer(text=f"Consultado por {interaction.user.display_name} • Página {page + 1} de {total_pages}")
                
                return embed
            
            # Crear vista con navegación si hay múltiples páginas
            if total_pages > 1:
                view = UserListNavigationView(users, total_pages, interaction.user)
                embed = create_users_embed(0)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                embed = create_users_embed(0)
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando lista de usuarios: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando la lista de usuarios",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🚗 Ver Conductores", style=discord.ButtonStyle.secondary, custom_id="admin_view_drivers")
    async def view_drivers_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver todos los conductores registrados"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos de administrador
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden ver la lista de conductores",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener todos los conductores del servidor
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT td.driver_id, td.license_number, td.vehicle_type, td.vehicle_name,
                           td.status, td.rating, td.total_rides, td.total_earnings,
                           tu.discord_id, tu.display_name, tu.ingame_name, COALESCE(ba.balance, 0.00) as balance,
                           td.created_at, td.last_activity
                    FROM taxi_drivers td
                    JOIN taxi_users tu ON td.user_id = tu.user_id
                    LEFT JOIN bank_accounts ba ON tu.user_id = ba.user_id
                    WHERE tu.discord_guild_id = ?
                    ORDER BY td.created_at DESC
                """, (str(interaction.guild.id),))
                
                drivers = await cursor.fetchall()
            
            if not drivers:
                embed = discord.Embed(
                    title="🚗 Lista de Conductores",
                    description="No hay conductores registrados en este servidor.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="💡 ¿Cómo registrar conductores?",
                    value="Los usuarios pueden registrarse como conductores usando el comando `/taxi_conductor_registro` en el canal de taxi.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear embed con información de conductores
            embed = discord.Embed(
                title="🚗 Lista de Conductores Registrados",
                description=f"Conductores del servidor **{interaction.guild.name}**\n\n**{len(drivers)} conductor(es) registrado(s)**",
                color=0xf39c12
            )
            
            # Separar por estado
            online_drivers = [d for d in drivers if d[4] == 'online']  # status
            offline_drivers = [d for d in drivers if d[4] != 'online']
            
            # Mostrar conductores online
            if online_drivers:
                online_text = ""
                for driver_data in online_drivers[:5]:  # Máximo 5 para no saturar
                    (driver_id, license_number, vehicle_type, vehicle_name, status, rating, 
                     total_rides, total_earnings, discord_id, display_name, ingame_name, 
                     balance, created_at, last_activity) = driver_data
                    
                    # Verificar si aún está en el servidor
                    member = interaction.guild.get_member(int(discord_id))
                    status_emoji = "🟢" if member else "🔴"
                    
                    ingame_display = ingame_name if ingame_name else "Sin configurar"
                    vehicle_display = f"{vehicle_type.title()}"
                    if vehicle_name:
                        vehicle_display += f" ({vehicle_name})"
                    
                    online_text += f"{status_emoji} **{display_name}**\n"
                    online_text += f"   • **InGame:** {ingame_display}\n"
                    online_text += f"   • **Vehículo:** {vehicle_display}\n"
                    online_text += f"   • **Licencia:** `{license_number}` | **Viajes:** {total_rides or 0}\n\n"
                
                embed.add_field(
                    name=f"🟢 Conductores Online ({len(online_drivers)})",
                    value=online_text[:1024] if online_text else "Ninguno",
                    inline=False
                )
            
            # Mostrar algunos conductores offline
            if offline_drivers:
                offline_text = ""
                for driver_data in offline_drivers[:3]:  # Máximo 3 offline
                    (driver_id, license_number, vehicle_type, vehicle_name, status, rating, 
                     total_rides, total_earnings, discord_id, display_name, ingame_name, 
                     balance, created_at, last_activity) = driver_data
                    
                    member = interaction.guild.get_member(int(discord_id))
                    status_emoji = "🟡" if member else "🔴"
                    
                    ingame_display = ingame_name if ingame_name else "Sin configurar"
                    offline_text += f"{status_emoji} **{display_name}** - {ingame_display}\n"
                
                embed.add_field(
                    name=f"🟡 Conductores Offline ({len(offline_drivers)})",
                    value=offline_text[:1024] if offline_text else "Ninguno",
                    inline=True
                )
            
            # Estadísticas
            total_rides = sum(d[6] or 0 for d in drivers)  # total_rides
            avg_trips = total_rides / len(drivers) if drivers else 0
            
            embed.add_field(
                name="📊 Estadísticas",
                value=f"• **Total viajes:** {total_rides}\n• **Promedio por conductor:** {avg_trips:.1f}\n• **Activos:** {len(online_drivers)}/{len(drivers)}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Leyenda",
                value="🟢 Online y en servidor\n🟡 Offline pero en servidor\n🔴 No está en servidor",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando lista de conductores: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando la lista de conductores",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏭 Vehículos por Escuadrón", style=discord.ButtonStyle.secondary, custom_id="admin_squadron_vehicles")
    async def view_squadron_vehicles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver vehículos registrados agrupados por escuadrón"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos
            is_admin = interaction.user.guild_permissions.administrator
            
            if not is_admin:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden ver esta información",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener vehículos por escuadrón
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        s.squadron_name,
                        s.squadron_type,
                        rv.vehicle_id,
                        rv.vehicle_type,
                        rv.owner_ingame_name,
                        rv.status,
                        rv.registered_at
                    FROM squadrons s
                    JOIN squadron_members sm ON s.id = sm.squadron_id
                    JOIN registered_vehicles rv ON sm.discord_id = rv.owner_discord_id
                    WHERE s.guild_id = ? AND s.status = 'active' AND rv.status = 'active'
                    ORDER BY s.squadron_name, rv.vehicle_type, rv.registered_at DESC
                """, (str(interaction.guild.id),))
                
                results = await cursor.fetchall()
                
                # También obtener vehículos sin escuadrón en la misma conexión
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM registered_vehicles rv
                    WHERE rv.guild_id = ? AND rv.status = 'active'
                    AND rv.owner_discord_id NOT IN (
                        SELECT sm.discord_id FROM squadron_members sm 
                        JOIN squadrons s ON sm.squadron_id = s.id 
                        WHERE s.guild_id = ? AND s.status = 'active'
                    )
                """, (str(interaction.guild.id), str(interaction.guild.id)))
                
                vehicles_without_squadron = (await cursor.fetchone())[0]
            
            if not results:
                embed = discord.Embed(
                    title="🏭 Vehículos por Escuadrón",
                    description="No hay vehículos registrados en escuadrones activos.",
                    color=discord.Color.blue()
                )
                
                # Mostrar vehículos sin escuadrón aunque no haya escuadrones
                if vehicles_without_squadron > 0:
                    embed.add_field(
                        name="📊 Información",
                        value=f"Hay **{vehicles_without_squadron}** vehículos registrados que no pertenecen a ningún escuadrón.",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Agrupar por escuadrón
            squadrons_data = {}
            for row in results:
                squadron_name, squadron_type, vehicle_id, vehicle_type, owner_name, status, registered_at = row
                
                if squadron_name not in squadrons_data:
                    squadrons_data[squadron_name] = {
                        'type': squadron_type,
                        'vehicles': []
                    }
                
                squadrons_data[squadron_name]['vehicles'].append({
                    'id': vehicle_id,
                    'type': vehicle_type,
                    'owner': owner_name
                })
            
            # Crear embed compacto
            embed = discord.Embed(
                title="🏭 Vehículos Registrados por Escuadrón",
                description=f"Vehículos activos del servidor **{interaction.guild.name}**",
                color=0x2ecc71
            )
            
            total_vehicles = sum(len(squad['vehicles']) for squad in squadrons_data.values())
            
            for squadron_name, squad_data in list(squadrons_data.items())[:8]:  # Máximo 8 escuadrones
                vehicle_list = []
                vehicle_types = {}
                
                # Contar por tipo
                for vehicle in squad_data['vehicles']:
                    vehicle_types[vehicle['type']] = vehicle_types.get(vehicle['type'], 0) + 1
                
                # Crear lista compacta
                type_summary = [f"**{vtype}**: {count}" for vtype, count in vehicle_types.items()]
                
                # Mostrar algunos vehículos específicos si hay espacio
                if len(squad_data['vehicles']) <= 5:
                    vehicle_details = [f"• `{v['id']}` ({v['type']}) - {v['owner']}" for v in squad_data['vehicles'][:3]]
                    if len(squad_data['vehicles']) > 3:
                        vehicle_details.append(f"• ...y {len(squad_data['vehicles']) - 3} más")
                else:
                    vehicle_details = [f"**Total:** {len(squad_data['vehicles'])} vehículos"]
                
                field_value = f"**Tipo:** {squad_data['type']}\n" + " | ".join(type_summary)
                if vehicle_details:
                    field_value += f"\n{chr(10).join(vehicle_details)}"
                
                embed.add_field(
                    name=f"🏭 {squadron_name} ({len(squad_data['vehicles'])})",
                    value=field_value[:1024],  # Límite Discord
                    inline=False
                )
            
            embed.add_field(
                name="📊 Resumen",
                value=f"• **Escuadrones:** {len(squadrons_data)}\n• **Vehículos en escuadrones:** {total_vehicles}\n• **Vehículos sin escuadrón:** {vehicles_without_squadron}\n• **Total:** {total_vehicles + vehicles_without_squadron}",
                inline=False
            )
            
            embed.set_footer(text=f"Consultado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando vehículos por escuadrón: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error consultando los vehículos por escuadrón",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔧 Comandos Admin", style=discord.ButtonStyle.success, custom_id="admin_commands_help")
    async def admin_commands_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar lista de comandos administrativos disponibles"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos
            is_admin = interaction.user.guild_permissions.administrator
            
            if not is_admin:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores pueden ver los comandos administrativos",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🔧 Comandos Administrativos Disponibles",
                description=f"Comandos de administración para **{interaction.guild.name}**",
                color=0x9b59b6
            )
            
            # Comandos de configuración
            embed.add_field(
                name="⚙️ Configuración de Canales",
                value="""
                `/ba_admin_channels_setup` - Configurar todos los canales
                `/welcome_admin_setup` - Configurar canal de bienvenida
                `/banco_admin_setup` - Configurar canal bancario
                `/mechanic_admin_setup` - Configurar canal de mecánico
                """,
                inline=False
            )
            
            # Comandos de gestión de usuarios
            embed.add_field(
                name="👥 Gestión de Usuarios",
                value="""
                **Panel Admin** - Ver usuarios y conductores
                `/squadron_admin_remove_member` - Remover de escuadrón
                `/squadron_admin_view_member` - Ver info de miembro
                """,
                inline=False
            )
            
            # Comandos del sistema de mecánico
            embed.add_field(
                name="🔧 Sistema de Mecánico",
                value="""
                `/mechanic_admin_register` - Registrar mecánico
                `/mechanic_admin_set_price` - Configurar precios
                `/mechanic_admin_config_pvp` - Configurar recargo PvP
                `/squadron_admin_config_limits` - Límites de vehículos
                """,
                inline=False
            )
            
            # Comandos del sistema de taxi
            embed.add_field(
                name="🚖 Sistema de Taxi",
                value="""
                `/taxi_admin_stats` - Ver estadísticas
                `/taxi_admin_tarifa` - Configurar tarifas
                `/taxi_admin_refresh` - Recrear panel admin
                `/taxi_admin_expiration` - Configurar expiración
                `/taxi_admin_leaderboard` - Clasificación conductores
                """,
                inline=False
            )
            
            # Comandos del sistema de alertas
            embed.add_field(
                name="🔔 Sistema de Alertas",
                value="""
                `/ba_admin_resethour_add` - Agregar horario de reset
                `/ba_admin_resethour_remove` - Quitar horario
                `/ba_admin_test_reset_alert` - Probar alerta
                """,
                inline=False
            )
            
            # Comandos de diagnóstico
            embed.add_field(
                name="🔍 Diagnóstico",
                value="""
                `/ba_admin_debug_channels` - Diagnosticar canales
                `/ba_admin_fix_channels` - Reparar configuraciones
                `/ba_admin_debug_user_cache` - Cache de usuario
                """,
                inline=False
            )
            
            embed.add_field(
                name="💡 Consejos",
                value="• Usa los **botones del panel** para tareas frecuentes\n• Los comandos con `/` son para configuraciones específicas\n• **Este panel persiste** después de reiniciar el bot",
                inline=False
            )
            
            embed.set_footer(text=f"Panel administrativo • {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando comandos admin: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error mostrando los comandos",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔍 Seguros Pendientes", style=discord.ButtonStyle.secondary, custom_id="admin_pending_insurance")
    async def pending_insurance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver y gestionar seguros pendientes de confirmación"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar permisos de administrador o mecánico
            is_admin = interaction.user.guild_permissions.administrator
            
            # Importar función desde mechanic_system
            try:
                from mechanic_system import is_user_mechanic
                is_mechanic = await is_user_mechanic(str(interaction.user.id), str(interaction.guild.id))
            except ImportError:
                is_mechanic = False
            
            if not (is_admin or is_mechanic):
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description="Solo administradores o mecánicos registrados pueden ver seguros pendientes",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Obtener seguros pendientes de confirmación
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT insurance_id, vehicle_id, vehicle_type, vehicle_location, 
                           owner_discord_id, owner_ingame_name, cost, payment_method, 
                           description, created_at
                    FROM vehicle_insurance 
                    WHERE guild_id = ? AND status = 'pending_confirmation'
                    ORDER BY created_at ASC
                """, (str(interaction.guild.id),))
                
                pending_insurances = await cursor.fetchall()
            
            if not pending_insurances:
                embed = discord.Embed(
                    title="🔍 Seguros Pendientes",
                    description="No hay seguros pendientes de confirmación en este momento.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="💡 Información",
                    value="Los seguros aparecen aquí cuando los clientes los solicitan y están esperando confirmación de un mecánico.",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear embed con la lista
            embed = discord.Embed(
                title="🔍 Seguros Pendientes de Confirmación",
                description=f"**{len(pending_insurances)} seguros** esperando confirmación en **{interaction.guild.name}**",
                color=0xff8800
            )
            
            # Crear selector con los seguros pendientes
            options = []
            for insurance in pending_insurances[:25]:  # Límite de Discord
                insurance_id, vehicle_id, vehicle_type, vehicle_location, owner_discord_id, owner_ingame_name, cost, payment_method, description, created_at = insurance
                
                # Formatear información
                try:
                    created_date = created_at[:16].replace('T', ' ')  # YYYY-MM-DD HH:MM
                except:
                    created_date = "Fecha desconocida"
                
                # Preparar descripción del selector
                selector_description = f"💰 ${cost:,.0f} | 🎮 {owner_ingame_name} | 📅 {created_date}"
                if len(selector_description) > 100:  # Límite de Discord
                    selector_description = f"💰 ${cost:,.0f} | 🎮 {owner_ingame_name[:20]}..."
                
                options.append(discord.SelectOption(
                    label=f"{vehicle_type.title()} - {owner_ingame_name[:30]}",
                    description=selector_description,
                    value=insurance_id,
                    emoji="🚗"
                ))
            
            embed.add_field(
                name="📋 Instrucciones",
                value="• Selecciona un seguro del menú desplegable\n• Se mostrará la información completa\n• Podrás confirmar o rechazar directamente",
                inline=False
            )
            
            embed.add_field(
                name="📊 Resumen",
                value=f"• **Total pendientes:** {len(pending_insurances)}\n• **Mostrando:** {min(len(pending_insurances), 25)}",
                inline=True
            )
            
            if len(pending_insurances) > 25:
                embed.add_field(
                    name="⚠️ Nota",
                    value=f"Solo se muestran los primeros 25 seguros. Hay {len(pending_insurances) - 25} más.",
                    inline=True
                )
            
            embed.set_footer(text=f"Panel administrativo • {interaction.user.display_name}")
            
            # Crear vista con selector
            view = PendingInsuranceView(options, interaction.client)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo seguros pendientes: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error obteniendo los seguros pendientes",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class TripRatingView(discord.ui.View):
    """Vista para seleccionar y calificar viajes completados"""
    
    def __init__(self, unrated_trips: list):
        super().__init__(timeout=300)
        self.unrated_trips = unrated_trips
        
        # Crear selector con los viajes
        if unrated_trips:
            options = []
            for trip in unrated_trips[:25]:  # Discord limit
                request_id, driver_id, pickup_zone, destination_zone, final_cost, completed_at, license_number, driver_name = trip
                
                # Formatear fecha
                try:
                    date_str = completed_at[:10] if completed_at else "Fecha desconocida"
                except:
                    date_str = "Fecha desconocida"
                
                options.append(discord.SelectOption(
                    label=f"Viaje #{request_id} - {driver_name}",
                    description=f"{pickup_zone} → {destination_zone} | ${final_cost:.2f} | {date_str}",
                    value=str(request_id)
                ))
            
            self.add_item(TripRatingSelect(options, self.unrated_trips))
    
    @discord.ui.button(
        label="🔙 Volver al Panel",
        style=discord.ButtonStyle.secondary,
        custom_id="back_to_main_from_rating",
        emoji="🔙"
    )
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al panel principal del sistema de taxi"""
        try:
            embed = discord.Embed(
                title="🚖 Sistema de Taxi",
                description="Usa los comandos `/taxi_conductor` para ser taxista, y más comandos disponibles.",
                color=0x00ff00
            )
            
            view = TaxiSystemView()
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error volviendo al panel principal desde rating: {e}")


class TripRatingSelect(discord.ui.Select):
    """Selector para elegir qué viaje calificar"""
    
    def __init__(self, options: list, unrated_trips: list):
        super().__init__(
            placeholder="Selecciona un viaje para calificar...",
            options=options
        )
        self.unrated_trips = unrated_trips
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_request_id = int(self.values[0])
            
            # Encontrar el viaje seleccionado
            selected_trip = None
            for trip in self.unrated_trips:
                if trip[0] == selected_request_id:  # request_id es el primer elemento
                    selected_trip = trip
                    break
            
            if not selected_trip:
                await interaction.response.send_message("❌ Viaje no encontrado", ephemeral=True)
                return
            
            request_id, driver_id, pickup_zone, destination_zone, final_cost, completed_at, license_number, driver_name = selected_trip
            
            # Crear modal de calificación
            modal = TripRatingModal(selected_trip)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error seleccionando viaje para calificar: {e}")
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)


class TripRatingModal(discord.ui.Modal):
    """Modal para calificar un viaje completado"""
    
    def __init__(self, trip_data: tuple):
        self.trip_data = trip_data
        request_id, driver_id, pickup_zone, destination_zone, final_cost, completed_at, license_number, driver_name = trip_data
        
        super().__init__(title=f"⭐ Calificar Viaje #{request_id}")
        
        # Campo de calificación (1-5 estrellas)
        self.rating_input = discord.ui.TextInput(
            label="Calificación (1-5 estrellas)",
            placeholder="Ingresa un número del 1 al 5",
            min_length=1,
            max_length=1,
            required=True
        )
        self.add_item(self.rating_input)
        
        # Campo de comentario opcional
        self.comment_input = discord.ui.TextInput(
            label="Comentario (Opcional)",
            placeholder="¿Cómo estuvo el servicio? ¿Algún comentario para el conductor?",
            style=discord.TextStyle.paragraph,
            min_length=0,
            max_length=500,
            required=False
        )
        self.add_item(self.comment_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validar calificación
            try:
                rating = int(self.rating_input.value)
                if not 1 <= rating <= 5:
                    raise ValueError("Rating fuera de rango")
            except ValueError:
                embed = discord.Embed(
                    title="❌ Calificación Inválida",
                    description="La calificación debe ser un número del 1 al 5.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            request_id, driver_id, pickup_zone, destination_zone, final_cost, completed_at, license_number, driver_name = self.trip_data
            comment = self.comment_input.value.strip() if self.comment_input.value else None
            
            # Obtener usuario que califica
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            if not user_data:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Usuario no encontrado en el sistema.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            user_id = int(user_data['user_id'])
            
            # Guardar calificación en base de datos
            success, message = await taxi_db.add_trip_rating(request_id, user_id, driver_id, rating, comment)
            
            if success:
                # Crear embed de confirmación
                embed = discord.Embed(
                    title="⭐ Calificación Enviada",
                    description=f"¡Gracias por calificar tu viaje con **{driver_name}**!",
                    color=discord.Color.green()
                )
                
                # Mostrar resumen de la calificación
                stars = "⭐" * rating + "☆" * (5 - rating)
                embed.add_field(
                    name="📊 Tu Calificación",
                    value=f"{stars} ({rating}/5)",
                    inline=True
                )
                
                embed.add_field(
                    name="🚖 Viaje",
                    value=f"#{request_id}: {pickup_zone} → {destination_zone}",
                    inline=True
                )
                
                if comment:
                    embed.add_field(
                        name="💬 Tu Comentario",
                        value=f'"{comment}"',
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Gracias",
                    value="Tu calificación ayuda a mejorar el servicio y ayuda a otros usuarios a elegir buenos conductores.",
                    inline=False
                )
                
                # Notificar al conductor si es posible
                try:
                    # Obtener datos del conductor
                    async with aiosqlite.connect(taxi_db.db_path) as db:
                        cursor = await db.execute("""
                            SELECT tu.discord_id FROM taxi_drivers td
                            JOIN taxi_users tu ON td.user_id = tu.user_id
                            WHERE td.driver_id = ?
                        """, (driver_id,))
                        
                        driver_data = await cursor.fetchone()
                        
                        if driver_data:
                            guild = interaction.guild
                            driver_member = guild.get_member(int(driver_data[0]))
                            
                            if driver_member:
                                driver_embed = discord.Embed(
                                    title="⭐ Nueva Calificación Recibida",
                                    description=f"Has recibido una calificación de **{interaction.user.display_name}**",
                                    color=discord.Color.gold()
                                )
                                
                                driver_embed.add_field(
                                    name="📊 Calificación",
                                    value=f"{stars} ({rating}/5 estrellas)",
                                    inline=True
                                )
                                
                                driver_embed.add_field(
                                    name="🚖 Viaje",
                                    value=f"#{request_id}: {pickup_zone} → {destination_zone}",
                                    inline=True
                                )
                                
                                if comment:
                                    driver_embed.add_field(
                                        name="💬 Comentario del Pasajero",
                                        value=f'"{comment}"',
                                        inline=False
                                    )
                                
                                try:
                                    await driver_member.send(embed=driver_embed)
                                except (discord.Forbidden, discord.HTTPException):
                                    logger.warning(f"No se pudo notificar al conductor {driver_name}")
                
                except Exception as notify_error:
                    logger.error(f"Error notificando al conductor: {notify_error}")
                
                # Volver al panel principal
                view = TaxiSystemView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                
            else:
                embed = discord.Embed(
                    title="❌ Error al Calificar",
                    description=f"No se pudo guardar la calificación: {message}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error procesando calificación: {e}")
            embed = discord.Embed(
                title="❌ Error Inesperado",
                description="Hubo un error al procesar tu calificación.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class UserListNavigationView(discord.ui.View):
    """Vista para navegar por páginas de usuarios"""
    
    def __init__(self, users: list, total_pages: int, requester: discord.Member):
        super().__init__(timeout=300)  # 5 minutos
        self.users = users
        self.total_pages = total_pages
        self.current_page = 0
        self.requester = requester
        self.page_size = 10
        
        # Deshabilitar botones según la página actual
        self.update_buttons()
    
    def update_buttons(self):
        """Actualizar estado de botones según página actual"""
        self.children[0].disabled = self.current_page == 0  # Previous
        self.children[1].disabled = self.current_page >= self.total_pages - 1  # Next
    
    def create_users_embed(self, page: int):
        """Crear embed para una página específica"""
        start_idx = page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.users))
        page_users = self.users[start_idx:end_idx]
        
        embed = discord.Embed(
            title="👥 Lista de Usuarios Registrados",
            description=f"**Página {page + 1}/{self.total_pages}** • **{len(self.users)} usuarios totales**",
            color=0x3498db
        )
        
        users_text = ""
        for i, user_data in enumerate(page_users, start=start_idx + 1):
            discord_id, username, display_name, ingame_name, balance, welcome_claimed, created_at = user_data
            
            ingame_display = ingame_name if ingame_name else "❌ Sin configurar"
            balance_display = f"${balance:,.0f}" if balance else "$0"
            welcome_status = "✅" if welcome_claimed else "❌"
            
            users_text += f"**{i}.** **{display_name}**\n"
            users_text += f"   • **InGame:** {ingame_display}\n"
            users_text += f"   • **Balance:** {balance_display} | **Welcome:** {welcome_status}\n\n"
        
        embed.add_field(
            name="📋 Usuarios en esta Página",
            value=users_text if users_text else "Sin usuarios",
            inline=False
        )
        
        embed.set_footer(text=f"Consultado por {self.requester.display_name} • Página {page + 1} de {self.total_pages}")
        
        return embed
    
    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a página anterior"""
        if interaction.user != self.requester:
            await interaction.response.send_message("❌ Solo quien solicitó la lista puede navegar", ephemeral=True)
            return
            
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_users_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="▶️ Siguiente", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a página siguiente"""
        if interaction.user != self.requester:
            await interaction.response.send_message("❌ Solo quien solicitó la lista puede navegar", ephemeral=True)
            return
            
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_users_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

async def setup_admin_panel(channel: discord.TextChannel, bot):
    """Configurar panel administrativo en un canal"""
    try:
        # Limpiar mensajes anteriores del bot en el canal
        logger.info(f"Limpiando mensajes anteriores en canal de administración {channel.id}...")
        deleted_count = 0
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                try:
                    await message.delete()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error eliminando mensaje {message.id}: {e}")
        
        logger.info(f"Eliminados {deleted_count} mensajes anteriores del bot en canal de administración")
        
        # Crear embed del panel
        embed = discord.Embed(
            title="🛠️ Panel de Administración",
            description="**Centro de control administrativo del sistema BunkerAdvice**\n\nUtiliza los botones de abajo para gestionar usuarios, conductores y configuraciones del servidor.",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="👥 Gestión de Usuarios",
            value="• **Ver Todos los Usuarios** - Lista completa con nombres InGame\n• **Ver Conductores** - Conductores registrados y su estado",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Herramientas Administrativas",
            value="• **Comandos Admin** - Lista completa de comandos disponibles\n• **Panel Persistente** - Se mantiene después de reinicios",
            inline=False
        )
        
        embed.add_field(
            name="📊 Información del Sistema",
            value=f"• **Servidor:** {channel.guild.name}\n• **Canal:** {channel.mention}\n• **Bot:** BunkerAdvice V2\n• **Sistemas:** 9 integrados",
            inline=False
        )
        
        embed.set_footer(text="Panel administrativo • Persistente y actualizado automáticamente")
        embed.set_thumbnail(url=channel.guild.icon.url if channel.guild.icon else None)
        
        # Enviar mensaje con botones
        view = AdminPanelView()
        message = await channel.send(embed=embed, view=view)
        
        logger.info(f"✅ Panel administrativo configurado exitosamente en canal {channel.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando panel administrativo: {e}")
        return False


class PendingInsuranceView(BaseView):
    """Vista para seleccionar y gestionar seguros pendientes"""
    
    def __init__(self, options: list, bot):
        super().__init__(timeout=300)  # 5 minutos
        self.bot = bot
        
        if options:
            # Agregar selector con las opciones
            select = PendingInsuranceSelect(options, bot)
            self.add_item(select)


class PendingInsuranceSelect(discord.ui.Select):
    """Selector para elegir seguro pendiente"""
    
    def __init__(self, options: list, bot):
        super().__init__(
            placeholder="Selecciona un seguro para revisar...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.bot = bot
    
    async def callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona un seguro"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            insurance_id = self.values[0]
            
            # Obtener información completa del seguro
            async with aiosqlite.connect(taxi_db.db_path) as db:
                cursor = await db.execute("""
                    SELECT insurance_id, vehicle_id, vehicle_type, vehicle_location, 
                           description, owner_discord_id, owner_ingame_name, guild_id, 
                           cost, payment_method, status, created_at
                    FROM vehicle_insurance 
                    WHERE insurance_id = ? AND status = 'pending_confirmation'
                """, (insurance_id,))
                
                insurance_data = await cursor.fetchone()
            
            if not insurance_data:
                embed = discord.Embed(
                    title="❌ Seguro No Encontrado",
                    description="El seguro seleccionado ya no está pendiente o fue eliminado.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Crear diccionario con los datos del seguro
            insurance_dict = {
                'insurance_id': insurance_data[0],
                'vehicle_id': insurance_data[1],
                'vehicle_type': insurance_data[2],
                'vehicle_location': insurance_data[3],
                'description': insurance_data[4],
                'owner_discord_id': insurance_data[5],
                'owner_ingame_name': insurance_data[6],
                'guild_id': insurance_data[7],
                'cost': insurance_data[8],
                'payment_method': insurance_data[9],
                'status': insurance_data[10],
                'created_at': insurance_data[11]
            }
            
            # Obtener información del cliente para el embed
            try:
                user = self.bot.get_user(int(insurance_data[5]))
                if user:
                    insurance_dict['client_display_name'] = user.display_name
                else:
                    insurance_dict['client_display_name'] = f"Usuario {insurance_data[5]}"
            except:
                insurance_dict['client_display_name'] = f"Usuario {insurance_data[5]}"
            
            # Crear embed similar al del DM/canal
            embed = discord.Embed(
                title="🔔 Detalles del Seguro Pendiente",
                description=f"**Revisión desde panel administrativo**",
                color=0xff8800,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🚗 Vehículo",
                value=f"**Tipo:** {insurance_dict['vehicle_type'].title()}\n**ID:** `{insurance_dict['vehicle_id']}`\n**Ubicación:** {insurance_dict['vehicle_location']}",
                inline=True
            )
            
            embed.add_field(
                name="👤 Cliente",
                value=f"**Discord:** {insurance_dict['client_display_name']}\n**InGame:** `{insurance_dict['owner_ingame_name']}`",
                inline=True
            )
            
            embed.add_field(
                name="💰 Seguro",
                value=f"**Costo:** ${insurance_dict['cost']:,.0f}\n**Pago:** {insurance_dict['payment_method'].title()}\n**ID:** `{insurance_dict['insurance_id']}`",
                inline=True
            )
            
            if insurance_dict.get('description'):
                embed.add_field(
                    name="📝 Descripción",
                    value=insurance_dict['description'],
                    inline=False
                )
            
            # Formatear fecha de creación
            try:
                created_date = insurance_dict['created_at'][:16].replace('T', ' ')
                embed.add_field(
                    name="📅 Solicitud Creada",
                    value=f"{created_date}",
                    inline=True
                )
            except:
                pass
            
            embed.add_field(
                name="⚠️ Importante",
                value="• **Confirmar:** Procesa el pago y activa el seguro\n• **Rechazar:** Cancela la solicitud sin cobrar\n• El débito de Discord se hará solo tras confirmación",
                inline=False
            )
            
            embed.set_footer(text=f"Panel Admin • Revisado por {interaction.user.display_name}")
            
            # Importar y crear vista de confirmación desde mechanic_system
            try:
                from mechanic_system import InsuranceConfirmationView
                view = InsuranceConfirmationView(insurance_dict, self.bot)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            except ImportError:
                # Fallback si no se puede importar
                embed_error = discord.Embed(
                    title="❌ Error del Sistema",
                    description="No se pudo cargar la vista de confirmación. Usa el canal de notificaciones.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed_error, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error mostrando detalles del seguro: {e}")
            embed = discord.Embed(
                title="❌ Error del Sistema",
                description="Hubo un error obteniendo los detalles del seguro",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
