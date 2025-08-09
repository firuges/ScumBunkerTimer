#!/usr/bin/env python3
"""
Sistema de Monitoreo de Servidores SCUM usando Battlemetrics API
"""

import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class SCUMServerMonitor:
    def __init__(self):
        self.battlemetrics_api = "https://api.battlemetrics.com"
        self.session = None
        
    async def _get_session(self):
        """Obtener sesión HTTP reutilizable"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Cerrar sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_server_by_ip(self, server_ip: str, server_port: int = 7777) -> Optional[Dict]:
        """Buscar servidor por IP usando Battlemetrics API"""
        try:
            session = await self._get_session()
            
            # Buscar servidor por IP/nombre
            search_url = f"{self.battlemetrics_api}/servers"
            params = {
                'filter[game]': 'scum',
                'filter[search]': f"{server_ip}:{server_port}",
                'page[size]': 10
            }
            
            headers = {
                'User-Agent': 'SCUM-Bunker-Bot/1.0',
                'Accept': 'application/vnd.api+json'
            }
            
            async with session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('data') and len(data['data']) > 0:
                        logger.info(f"Encontrados {len(data['data'])} servidores para {server_ip}:{server_port}")
                        
                        # Buscar el servidor que coincida EXACTAMENTE con la IP y puerto
                        for server in data['data']:
                            attrs = server.get('attributes', {})
                            found_ip = attrs.get('ip')
                            found_port = attrs.get('port')
                            
                            logger.info(f"Verificando servidor {server['id']}: {found_ip}:{found_port} vs {server_ip}:{server_port}")
                            
                            # Coincidencia EXACTA de IP y puerto
                            if found_ip == server_ip and found_port == server_port:
                                logger.info(f"✅ COINCIDENCIA EXACTA encontrada: {server['id']} - {attrs.get('name')}")
                                return self._parse_server_data(server)
                        
                        # Si no hay coincidencia exacta, usar el primer resultado con advertencia
                        logger.warning(f"⚠️ No se encontró coincidencia exacta para {server_ip}:{server_port}, usando el primer resultado")
                        first_server = data['data'][0]
                        attrs = first_server.get('attributes', {})
                        logger.warning(f"Usando servidor {first_server['id']}: {attrs.get('ip')}:{attrs.get('port')} - {attrs.get('name')}")
                        return self._parse_server_data(first_server)
                    else:
                        logger.warning(f"No se encontró servidor con IP {server_ip}:{server_port}")
                        return None
                else:
                    logger.error(f"Error en API Battlemetrics: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error buscando servidor {server_ip}:{server_port}: {e}")
            return None
    
    async def get_server_status_by_id(self, battlemetrics_id: str) -> Optional[Dict]:
        """Obtener estado de servidor por ID de Battlemetrics (más eficiente)"""
        try:
            session = await self._get_session()
            
            url = f"{self.battlemetrics_api}/servers/{battlemetrics_id}"
            
            headers = {
                'User-Agent': 'SCUM-Bunker-Bot/1.0',
                'Accept': 'application/vnd.api+json'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Log para debugging
                    logger.info(f"Raw API response for server {battlemetrics_id}: status={response.status}")
                    if 'data' in data:
                        attrs = data['data'].get('attributes', {})
                        logger.info(f"Raw attributes - players: {attrs.get('players')}, maxPlayers: {attrs.get('maxPlayers')}, status: {attrs.get('status')}")
                        logger.info(f"Server name: {attrs.get('name', 'Unknown')}")
                    
                    return self._parse_server_data(data['data'])
                else:
                    logger.error(f"Error obteniendo servidor {battlemetrics_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo estado del servidor {battlemetrics_id}: {e}")
            return None
    
    def _parse_server_data(self, server_data: Dict) -> Dict:
        """Parsear datos del servidor desde Battlemetrics"""
        attributes = server_data.get('attributes', {})
        details = attributes.get('details', {})
        
        # Log para debugging
        logger.info(f"Parseando datos del servidor {server_data.get('id', 'Unknown')}")
        logger.info(f"Players: {attributes.get('players', 'Not found')}")
        logger.info(f"MaxPlayers: {attributes.get('maxPlayers', 'Not found')}")
        logger.info(f"Status: {attributes.get('status', 'Not found')}")
        
        # Calcular tiempo desde última actualización
        last_seen = attributes.get('lastSeen')
        last_seen_dt = None
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            except:
                pass
        
        # Verificar si los datos parecen ser válidos/actualizados
        players = attributes.get('players', 0)
        max_players = attributes.get('maxPlayers', 0)
        
        # Si los datos parecen incorrectos, agregar una nota
        data_warning = None
        if players == 0 and max_players > 50:  # Heurística para detectar datos posiblemente incorrectos
            data_warning = "⚠️ Los datos de jugadores pueden no estar actualizados"
        
        # Verificar si el servidor cambió de host (indicativo de problemas)
        server_name = attributes.get('name', 'Unknown')
        if 'ChangedHost' in server_name or server_name.startswith('ChangedHost'):
            data_warning = "⚠️ Servidor cambió de host - datos pueden estar desactualizados"
        
        return {
            'battlemetrics_id': server_data.get('id'),
            'online': attributes.get('status') == 'online',
            'name': attributes.get('name', 'Unknown'),
            'players': players,
            'max_players': max_players,
            'map': details.get('map', 'Unknown'),
            'country': attributes.get('country', 'Unknown'),
            'rank': attributes.get('rank'),
            'last_seen': last_seen,
            'last_seen_dt': last_seen_dt,
            'ip': attributes.get('ip'),
            'port': attributes.get('port'),
            'query_port': attributes.get('portQuery'),
            'version': details.get('version', 'Unknown'),
            'pve': details.get('pve', False),
            'private': attributes.get('private', False),
            'data_warning': data_warning,
            'data_source': 'server-endpoint'  # Indicar fuente de datos
        }
    
    async def get_server_players_history(self, battlemetrics_id: str, hours: int = 24) -> List[Dict]:
        """Obtener historial de jugadores (Premium feature)"""
        try:
            session = await self._get_session()
            
            # Calcular tiempo desde
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            url = f"{self.battlemetrics_api}/servers/{battlemetrics_id}/stats"
            params = {
                'start': start_time.isoformat() + 'Z',
                'resolution': '60'  # Datos cada 60 minutos
            }
            
            headers = {
                'User-Agent': 'SCUM-Bunker-Bot/1.0',
                'Accept': 'application/vnd.api+json'
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.warning(f"No se pudo obtener historial para servidor {battlemetrics_id}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error obteniendo historial del servidor {battlemetrics_id}: {e}")
            return []

# Instancia global
server_monitor = SCUMServerMonitor()

async def cleanup_monitor():
    """Función para limpiar recursos"""
    await server_monitor.close()
