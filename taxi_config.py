#!/usr/bin/env python3
"""
Configuración del Sistema de Taxi Modular para SCUM
Compatible con servidores PVE/PVP con restricciones de zona
"""

from typing import Dict, List, Tuple
import json
import aiosqlite
import asyncio

class TaxiConfig:
    def __init__(self, guild_id: str = None):
        self.guild_id = guild_id
        # Auto-detectar qué base usar (compatibilidad durante migración)
        import os
        if os.path.exists("scum_main.db"):
            self.db_path = "scum_main.db"
        else:
            self.db_path = "scum_main.db"  # Default
        
        # Initialize with default values first
        self._initialize_defaults()
        
        # If guild_id is provided, try to load from database
        if guild_id:
            try:
                asyncio.run(self.load_server_config(guild_id))
            except Exception as e:
                print(f"Error loading server config for {guild_id}: {e}")
                # Continue with defaults
    
    def _initialize_defaults(self):
        # === CONFIGURACIÓN GENERAL ===
        self.FEATURE_ENABLED = True  # Master switch para todo el sistema
        self.TAXI_ENABLED = True     # Switch específico para taxi
        self.BANK_ENABLED = True     # Switch específico para banco
        self.WELCOME_PACK_ENABLED = True  # Switch para welcome pack
        
        # === CONFIGURACIÓN ECONÓMICA ===
        self.WELCOME_BONUS = 7500.0  # Dinero inicial (optimizado +50%)
        self.TAXI_BASE_RATE = 500.0   # Tarifa base
        self.TAXI_PER_KM_RATE = 20.5  # Por kilómetro
        self.TAXI_WAIT_RATE = 2.0    # Por minuto de espera
        self.DRIVER_COMMISSION = 0.85  # 85% para el conductor (optimizado +10%)
        self.PLATFORM_FEE = 0.15      # 15% para la plataforma
        # === TIPOS DE VEHÍCULOS ===
        self.VEHICLE_TYPES = {
            "auto": {
                "name": "Automóvil",
                "emoji": "🚗",
                "description": "Vehículo terrestre estándar",
                "capacity": 4,
                "speed_multiplier": 1.0,
                "cost_multiplier": 1.0,
                "access_types": ["land", "road"],
                "restricted_zones": ["water", "air_only"]
            },
            
            "moto": {
                "name": "Motocicleta", 
                "emoji": "🏍️",
                "description": "Vehículo rápido y ágil",
                "capacity": 2,
                "speed_multiplier": 1.3,
                "cost_multiplier": 0.8,
                "access_types": ["land", "road", "offroad"],
                "restricted_zones": ["water", "air_only"]
            },
            
            "avion": {
                "name": "Avión",
                "emoji": "✈️", 
                "description": "Transporte aéreo rápido",
                "capacity": 2,
                "speed_multiplier": 3.0,
                "cost_multiplier": 3.5,
                "access_types": ["air", "airstrip"],
                "restricted_zones": ["water_only"],
                "landing_zones": ["Z0-8", "A4-3", "B4-1", "A0-1"]
            },
            
            "hidroavion": {
                "name": "Hidroavión",
                "emoji": "🛩️",
                "description": "Avión que aterriza en agua",
                "capacity": 2,
                "speed_multiplier": 2.5,
                "cost_multiplier": 3.0,
                "access_types": ["air", "water", "seaplane"],
                "restricted_zones": [],
                "landing_zones": ["water_zones"]  # Se define dinámicamente
            },
            
            "barco": {
                "name": "Barco",
                "emoji": "🚢",
                "description": "Transporte marítimo",
                "capacity": 4,
                "speed_multiplier": 0.8,
                "cost_multiplier": 4.5,
                "access_types": ["water", "port"],
                "restricted_zones": ["land_only", "air_only"]
            }
        }
        # === SISTEMA DE ZONAS BASADO EN PADS DE SCUM ===
        # Sistema de coordenadas: A0-D4 dividido en PADs 1-9
        # PAD Layout: 7-8-9
        #             4-5-6  
        #             1-2-3
        
        # === PARADAS DE TAXI (PUNTOS DE ORIGEN) ===
        self.TAXI_STOPS = {
            # Paradas principales en ciudades (Terrestres)
            "stop_b2_city": {
                "id": "b2_city",
                "grid": "B2",
                "pad": 7,
                "coordinates": "B2-7",
                "name": "Parada Ciudad Central",
                "type": "main_stop",
                "description": "Parada principal frente al Ayuntamiento",
                "always_available": True,
                "max_taxis": 8,
                "access_types": ["land", "road"],
                "vehicle_types": ["auto", "moto"]
            },
            
            "stop_c0_port": {
                "id": "c0_port", 
                "grid": "C0",
                "pad": 4,
                "coordinates": "C0-4",
                "name": "Parada Puerto Este",
                "type": "port_stop",
                "description": "Parada en el puerto comercial",
                "always_available": True,
                "max_taxis": 5,
                "access_types": ["land", "water", "port"],
                "vehicle_types": ["auto", "moto", "barco"]
            },
            
            "stop_b4_airport": {
                "id": "b4_airport",
                "grid": "B4", 
                "pad": 1,
                "coordinates": "B4-1",
                "name": "Trader B4",
                "type": "airport_stop",
                "description": "Terminal Trader B4",
                "always_available": True,
                "max_taxis": 6,
                "access_types": ["land", "road", "air", "airstrip","water", "port"],
                "vehicle_types": ["auto", "moto", "avion", "Hidroavion", "barco"]
            },
            
            # Pistas de aterrizaje específicas
            "stop_z0_airstrip": {
                "id": "z0_airstrip",
                "grid": "Z0",
                "pad": 8,
                "coordinates": "Z0-8",
                "name": "Pista de Aterrizaje Sur",
                "type": "airstrip",
                "description": "Pista para aviones en zona sur",
                "always_available": False,
                "max_taxis": 3,
                "access_types": ["air", "airstrip", "land", "road"],
                "vehicle_types": ["avion", "auto", "moto"]
            },
            
            "stop_a4_airstrip": {
                "id": "a4_airstrip",
                "grid": "A4",
                "pad": 3,
                "coordinates": "A4-3", 
                "name": "Pista Militar Oeste",
                "type": "airstrip",
                "description": "Pista militar abandonada",
                "always_available": False,
                "max_taxis": 2,
                "access_types": ["air", "airstrip","land", "road"],
                "vehicle_types": ["auto", "moto","avion"]
            },
            
            "stop_a0_airstrip": {
                "id": "a0_airstrip",
                "grid": "A0",
                "pad": 1,
                "coordinates": "A0-1",
                "name": "Pista Costera Este TRADER A0",
                "type": "airstrip",
                "description": "Pista cerca de la costa  TRADER A0",
                "always_available": False,
                "max_taxis": 2,
                "access_types": ["land", "road","air", "airstrip","water", "port"],
                "vehicle_types": ["auto", "moto","avion", "Hidroavion", "barco"]
            },
            
            # Puertos marítimos
            "stop_seaport_north": {
                "id": "seaport_north",
                "grid": "C0",
                "pad": 1,
                "coordinates": "C0-1",
                "name": "Zona Radiación Limite",
                "type": "seaport",
                "description": "Limite con Zona Radioactiva",
                "always_available": True,
                "max_taxis": 4,
                "access_types": ["land", "road","water", "port"],
                "vehicle_types": ["auto", "moto", "barco", "hidroavion"]
            },
            
            "stop_seaport_south": {
                "id": "seaport_south", 
                "grid": "Z3",
                "pad": 5,
                "coordinates": "Z3-9",
                "name": "Puerto Marítimo Sur Trader",
                "type": "seaport",
                "description": "Puerto pesquero del sur  Trader Z3",
                "always_available": True,
                "max_taxis": 3,
                "access_types": ["water", "port"],
                "vehicle_types": ["barco", "hidroavion"]
            },
            
            # Paradas terrestres secundarias
            "stop_a0_town": {
                "id": "a0_town",
                "grid": "A0",
                "pad": 8,
                "coordinates": "A0-8", 
                "name": "Parada Pueblo Costero",
                "type": "town_stop",
                "description": "Parada en plaza del pueblo",
                "always_available": False,
                "max_taxis": 3,
                "access_types": ["land", "road","water", "port"],
                "vehicle_types": ["auto", "moto", "Hidroavion", "barco"]
            },
            
            "stop_c3_villa": {
                "id": "c3_villa",
                "grid": "C3",
                "pad": 7,
                "coordinates": "C3-7",
                "name": "Somobor", 
                "type": "town_stop",
                "description": "Parada cerca de Somobor",
                "always_available": False,
                "max_taxis": 2,
                "access_types": ["land", "road"],
                "vehicle_types": ["auto", "moto"]
            },
            
            # Paradas industriales
            "stop_b3_industrial": {
                "id": "b3_industrial",
                "grid": "B3",
                "pad": 6,
                "coordinates": "B3-6",
                "name": "Parada Zona Industrial",
                "type": "industrial_stop", 
                "description": "Parada para trabajadores",
                "always_available": False,
                "max_taxis": 4,
                "access_types": ["land", "road", "offroad"],
                "vehicle_types": ["auto", "moto"]
            },
            
            "stop_a2_mining": {
                "id": "a2_mining",
                "grid": "D0",
                "pad": 7,
                "coordinates": "D0-7",
                "name": "Parada Zona Minera",
                "type": "mining_stop",
                "description": "Parada para mineros",
                "always_available": False,
                "max_taxis": 3,
                "access_types": ["land", "offroad"],
                "vehicle_types": ["auto", "moto"]
            }
        }
        
        # === ZONAS DE DESTINO ===
        self.PVP_ZONES = {
            # === CIUDADES PRINCIPALES (Zonas Seguras) ===
            "city_b2_pad5": {
                "grid": "B2",
                "pad": 5,
                "coordinates": "B2-5",
                "name": "Ciudad Central",
                "type": "city",
                "restriction": "safe_zone",
                "description": "Centro urbano principal - Zona completamente segura",
                "landmarks": ["Ayuntamiento", "Mercado Central", "Hospital"],
                "access_types": ["land", "road"],
                "vehicle_access": ["auto", "moto"]
            },
            
            "city_c0_pad4": {
                "grid": "C0",
                "pad": 4,
                "coordinates": "C0-4",
                "name": "Puerto Este",
                "type": "port",
                "restriction": "safe_zone", 
                "description": "Puerto comercial - Zona de comercio segura",
                "landmarks": ["Muelle", "Almacenes", "Oficina Aduanas"],
                "access_types": ["land", "water", "port"],
                "vehicle_access": ["auto", "moto", "barco", "hidroavion"]
            },
            
            # === ISLAS REMOTAS (Solo Barco/Hidroavión) ===
            "island_z0_pad1": {
                "grid": "Z0",
                "pad": 1,
                "coordinates": "Z0-1",
                "name": "Isla Sur Remote",
                "type": "island",
                "restriction": "neutral",
                "description": "Isla alejada - Accesible por puente, agua o aire",
                "landmarks": ["Playa Desierta", "Cabaña Abandonada", "Puente"],
                "access_types": ["water", "air", "land", "road"],
                "vehicle_access": ["barco", "hidroavion", "auto", "moto"]
            },
            
            "island_a4_pad9": {
                "grid": "A4", 
                "pad": 9,
                "coordinates": "A4-9",
                "name": "Isla Norte Remote",
                "type": "island",
                "restriction": "neutral",
                "description": "Isla del norte - Accesible por puente, agua o aire",
                "landmarks": ["Faro Antiguo", "Rocas", "Puente"],
                "access_types": ["water", "air", "land", "road"],
                "vehicle_access": ["barco", "hidroavion", "auto", "moto"]
            },
            
            # === BASES MILITARES (Sin Taxi) ===
            "military_b2_pad2": {
                "grid": "B2",
                "pad": 2,
                "coordinates": "B2-2",
                "name": "Base Militar Central",
                "type": "military",
                "restriction": "no_taxi",
                "description": "Zona militar restringida - Sin acceso de taxi",
                "landmarks": ["Cuartel General", "Armería", "Torre de Control"]
            },
            
            # === BUNKERS (Zonas de Combate) ===
            "bunker_d1_pad7": {
                "grid": "D1",
                "pad": 7,
                "coordinates": "D1-7",
                "name": "Bunker Noroeste",
                "type": "bunker",
                "restriction": "combat_zone",
                "description": "Bunker abandonado - Zona de alto riesgo",
                "landmarks": ["Entrada Principal", "Torre de Vigilancia"]
            },
            
            "bunker_a1_pad9": {
                "grid": "A1", 
                "pad": 9,
                "coordinates": "A1-9",
                "name": "Bunker Noreste",
                "type": "bunker",
                "restriction": "combat_zone",
                "description": "Complejo militar abandonado - Zona peligrosa",
                "landmarks": ["Helipuerto", "Laboratorio"]
            },
            
            "bunker_a3_pad3": {
                "grid": "A3",
                "pad": 3,
                "coordinates": "A3-3",
                "name": "Bunker Sureste", 
                "type": "bunker",
                "restriction": "combat_zone",
                "description": "Instalación subterránea - Área de combate",
                "landmarks": ["Túneles", "Sala de Comunicaciones"]
            },
            
            "bunker_d3_pad1": {
                "grid": "D3",
                "pad": 1,
                "coordinates": "D3-1",
                "name": "Bunker Suroeste",
                "type": "bunker", 
                "restriction": "combat_zone",
                "description": "Fortaleza abandonada - Zona de conflicto",
                "landmarks": ["Murallas", "Arsenal"]
            },
            
            # === AEROPUERTOS (Zonas Neutrales) ===
            "airport_b4_pad1": {
                "grid": "B4",
                "pad": 1,
                "coordinates": "B4-1",
                "name": "Aeropuerto Principal",
                "type": "airport",
                "restriction": "neutral",
                "description": "Terminal aérea principal - Zona neutral controlada",
                "landmarks": ["Terminal", "Torre de Control", "Hangar"],
                "access_types": ["land", "air", "airstrip"],
                "vehicle_access": ["auto", "moto", "avion"]
            },
            
            # === PUEBLOS Y ASENTAMIENTOS (Zonas Seguras) ===
            "town_a0_pad8": {
                "grid": "A0",
                "pad": 8, 
                "coordinates": "A0-8",
                "name": "Pueblo Costero Norte",
                "type": "town",
                "restriction": "safe_zone",
                "description": "Pequeño asentamiento pesquero - Zona segura",
                "landmarks": ["Muelle Pesquero", "Tienda Local"]
            },
            
            "town_c3_pad4": {
                "grid": "C3",
                "pad": 4,
                "coordinates": "C3-4", 
                "name": "Villa del Sur",
                "type": "town",
                "restriction": "safe_zone",
                "description": "Comunidad rural - Zona protegida",
                "landmarks": ["Plaza Central", "Iglesia", "Mercado"]
            },
            
            # === ZONAS INDUSTRIALES (Neutrales) ===
            "factory_b3_pad1": {
                "grid": "B3",
                "pad": 1,
                "coordinates": "B3-1",
                "name": "Complejo Industrial",
                "type": "industrial",
                "restriction": "neutral",
                "description": "Zona de fábricas - Área neutral con precaución", 
                "landmarks": ["Fábrica Principal", "Almacenes", "Chimeneas"]
            },
            
            "mining_a2_pad7": {
                "grid": "A2",
                "pad": 7,
                "coordinates": "A2-7", 
                "name": "Zona Minera",
                "type": "mining",
                "restriction": "neutral",
                "description": "Área de extracción - Zona de trabajo neutral",
                "landmarks": ["Mina Principal", "Oficinas", "Depósito"]
            },
            
            # === ZONAS FORESTALES (Seguras) ===
            "forest_c1_pad9": {
                "grid": "C1",
                "pad": 9,
                "coordinates": "C1-9",
                "name": "Bosque Central",
                "type": "forest", 
                "restriction": "safe_zone",
                "description": "Área boscosa - Zona segura para campamento",
                "landmarks": ["Lago", "Senderos", "Cabaña de Guardabosques"]
            },
            
            # === ZONAS DE RECURSOS (Neutrales) ===
            "resource_d0_pad5": {
                "grid": "D0",
                "pad": 5,
                "coordinates": "D0-5",
                "name": "Zona de Recursos Norte",
                "type": "resource",
                "restriction": "neutral", 
                "description": "Área de recolección - Zona neutral disputada",
                "landmarks": ["Depósitos Minerales", "Vegetación Densa"]
            }
        }
        
        # === CONFIGURACIÓN DE RESTRICCIONES ===
        self.ZONE_RULES = {
            "no_taxi": {
                "pickup_allowed": False,
                "dropoff_allowed": False,
                "message": "⚠️ Zona militar restringida - Sin servicio de taxi"
            },
            "combat_zone": {
                "pickup_allowed": True,
                "dropoff_allowed": False,  # No se puede dejar en zona de combate
                "message": "⚔️ Zona de combate - Solo recogida de emergencia"
            },
            "safe_zone": {
                "pickup_allowed": True,
                "dropoff_allowed": True,
                "message": "🛡️ Zona segura - Servicio completo disponible"
            },
            "neutral": {
                "pickup_allowed": True,
                "dropoff_allowed": True,
                "message": "🤝 Zona neutral - Servicio disponible"
            },
            "trade_zone": {
                "pickup_allowed": True,
                "dropoff_allowed": True,
                "message": "💼 Zona comercial - Servicio prioritario"
            }
        }
        
        # === CONFIGURACIÓN DE CANALES ===
        self.CHANNEL_CONFIG = {
            "taxi_channel_name": "🚖┃taxi-service",
            "bank_channel_name": "🏦┃bank-service", 
            "welcome_channel_name": "🎉┃welcome-center",
            "logs_channel_name": "📊┃taxi-logs"
        }
        
        
        
        # === NIVELES DE CONDUCTOR ===
        self.DRIVER_LEVELS = {
            0: {"name": "Novato", "emoji": "🟢", "bonus": 0.0},
            10: {"name": "Conductor", "emoji": "🔵", "bonus": 0.05},
            25: {"name": "Experto", "emoji": "🟡", "bonus": 0.10},
            50: {"name": "Veterano", "emoji": "🟠", "bonus": 0.15},
            100: {"name": "Leyenda", "emoji": "🔴", "bonus": 0.25}
        }

    def calculate_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcular distancia entre dos puntos usando coordenadas directas (fallback)"""
        import math
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def grid_to_coordinates(self, grid: str) -> tuple:
        """Convertir grid (ej: 'B2') a coordenadas numéricas para cálculo"""
        # Mapeo de letras a números (D=4, C=3, B=2, A=1, Z=0)
        row_map = {'D': 4, 'C': 3, 'B': 2, 'A': 1, 'Z': 0}
        
        if len(grid) != 2:
            return (0, 0)
        
        row_letter = grid[0].upper()
        col_number = int(grid[1])
        
        if row_letter not in row_map or col_number < 0 or col_number > 4:
            return (0, 0)
        
        return (row_map[row_letter], col_number)
    
    def pad_to_subgrid_coords(self, pad: int) -> tuple:
        """Convertir PAD (1-9) a coordenadas dentro del grid"""
        # PAD Layout: 7-8-9
        #             4-5-6  
        #             1-2-3
        pad_coords = {
            1: (0, 0), 2: (0, 1), 3: (0, 2),
            4: (1, 0), 5: (1, 1), 6: (1, 2),
            7: (2, 0), 8: (2, 1), 9: (2, 2)
        }
        return pad_coords.get(pad, (1, 1))  # Default centro si pad inválido
    
    def calculate_grid_distance(self, origin_grid: str, origin_pad: int, dest_grid: str, dest_pad: int) -> float:
        """Calcular distancia realista entre grids usando caminos del juego"""
        
        # Obtener coordenadas de grids
        origin_coords = self.grid_to_coordinates(origin_grid)
        dest_coords = self.grid_to_coordinates(dest_grid)
        
        # Obtener coordenadas de pads dentro del grid
        origin_subgrid = self.pad_to_subgrid_coords(origin_pad)
        dest_subgrid = self.pad_to_subgrid_coords(dest_pad)
        
        # Coordenadas finales (cada grid = 3km, cada pad = 1km)
        origin_x = origin_coords[1] * 3 + origin_subgrid[1]
        origin_y = origin_coords[0] * 3 + origin_subgrid[0] 
        dest_x = dest_coords[1] * 3 + dest_subgrid[1]
        dest_y = dest_coords[0] * 3 + dest_subgrid[0]
        
        # Calcular distancia Manhattan (más realista para caminos)
        manhattan_distance = abs(dest_x - origin_x) + abs(dest_y - origin_y)
        
        # Aplicar factor de caminos tortuosos (1.4x para simular carreteras no rectas)
        road_factor = 1.4
        
        # Distancia final en kilómetros
        realistic_distance = manhattan_distance * road_factor
        
        return realistic_distance
    
    def calculate_zone_distance(self, origin_zone: dict, dest_zone: dict) -> float:
        """Calcular distancia entre dos zonas usando el sistema de grids"""
        
        # Verificar que ambas zonas tengan información de grid y pad
        if not all(key in origin_zone for key in ['grid', 'pad']):
            return 10.0  # Distancia por defecto
        if not all(key in dest_zone for key in ['grid', 'pad']):
            return 10.0  # Distancia por defecto
        
        origin_grid = origin_zone['grid']
        origin_pad = origin_zone['pad']
        dest_grid = dest_zone['grid']
        dest_pad = dest_zone['pad']
        
        return self.calculate_grid_distance(origin_grid, origin_pad, dest_grid, dest_pad)

    def get_zone_at_location(self, x: float, y: float) -> Dict:
        """Obtener zona en ubicación específica - Busca primero en TAXI_STOPS, luego en PVP_ZONES"""
        
        # MAPEO ESPECÍFICO para coordenadas problemáticas conocidas
        # Esto corrige el problema donde Z0-8 se mapea incorrectamente
        specific_coords = {
            (25000, 250): 'stop_z0_airstrip',  # Z0-8 -> Pista de Aterrizaje Sur
            (750, 3750): 'airport_b4_pad1',   # B4-1 -> Aeropuerto Principal
        }
        
        # Buscar mapeo específico con tolerancia
        for (known_x, known_y), zone_id in specific_coords.items():
            if abs(x - known_x) <= 100 and abs(y - known_y) <= 100:
                # Buscar en TAXI_STOPS
                if zone_id in self.TAXI_STOPS:
                    stop_data = self.TAXI_STOPS[zone_id]
                    return {
                        "zone_id": zone_id,
                        "zone_name": stop_data["name"],
                        "restriction": stop_data.get("restriction", "neutral"),
                        "rules": self.ZONE_RULES.get(stop_data.get("restriction", "neutral"), self.ZONE_RULES["neutral"])
                    }
                # Buscar en PVP_ZONES
                elif zone_id in self.PVP_ZONES:
                    zone_data = self.PVP_ZONES[zone_id]
                    return {
                        "zone_id": zone_id,
                        "zone_name": zone_data["name"],
                        "restriction": zone_data.get("restriction", "neutral"),
                        "rules": self.ZONE_RULES.get(zone_data.get("restriction", "neutral"), self.ZONE_RULES["neutral"])
                    }
        
        min_distance = float('inf')
        closest_zone = None
        
        # PRIMERO: Buscar en TAXI_STOPS (más específicos como aeropuertos)
        for stop_id, stop_data in self.TAXI_STOPS.items():
            # Convertir grid/pad a coordenadas básicas
            grid = stop_data.get('grid', 'B2')
            pad = stop_data.get('pad', 5)
            
            # Grid: A=0, B=1000, C=2000, etc.
            grid_letter = grid[0] if grid else 'B'
            grid_number = grid[1:] if len(grid) > 1 else '2'
            
            zone_x = (ord(grid_letter.upper()) - ord('A')) * 1000
            zone_y = int(grid_number) * 1000 if grid_number.isdigit() else 2000
            
            # PAD offset
            pad_offsets = {
                1: (-250, -250), 2: (0, -250), 3: (250, -250),
                4: (-250, 0),    5: (0, 0),    6: (250, 0),
                7: (-250, 250),  8: (0, 250),  9: (250, 250)
            }
            pad_offset = pad_offsets.get(pad, (0, 0))
            zone_x += pad_offset[0]
            zone_y += pad_offset[1]
            
            distance = self.calculate_distance(x, y, zone_x, zone_y)
            
            # Priorizar TAXI_STOPS (aeropuertos, pistas)
            if distance < min_distance or (distance <= 500 and closest_zone is None):
                min_distance = distance
                closest_zone = {
                    "zone_id": stop_id,
                    "zone_name": stop_data["name"],
                    "restriction": stop_data.get("restriction", "neutral"),
                    "rules": self.ZONE_RULES.get(stop_data.get("restriction", "neutral"), self.ZONE_RULES["neutral"])
                }
        
        # Si encontramos TAXI_STOP cercano (dentro de 500m), usarlo
        if closest_zone and min_distance <= 500:
            return closest_zone
        
        # SEGUNDO: Buscar en PVP_ZONES solo si no hay TAXI_STOP cercano
        for zone_id, zone_data in self.PVP_ZONES.items():
            # Convertir grid/pad a coordenadas básicas
            grid = zone_data.get('grid', 'B2')
            pad = zone_data.get('pad', 5)
            
            # Grid: A=0, B=1000, C=2000, etc.
            grid_letter = grid[0] if grid else 'B'
            grid_number = grid[1:] if len(grid) > 1 else '2'
            
            zone_x = (ord(grid_letter.upper()) - ord('A')) * 1000
            zone_y = int(grid_number) * 1000 if grid_number.isdigit() else 2000
            
            # PAD offset
            pad_offsets = {
                1: (-250, -250), 2: (0, -250), 3: (250, -250),
                4: (-250, 0),    5: (0, 0),    6: (250, 0),
                7: (-250, 250),  8: (0, 250),  9: (250, 250)
            }
            pad_offset = pad_offsets.get(pad, (0, 0))
            zone_x += pad_offset[0]
            zone_y += pad_offset[1]
            
            distance = self.calculate_distance(x, y, zone_x, zone_y)
            
            if distance < min_distance:
                min_distance = distance
                closest_zone = {
                    "zone_id": zone_id,
                    "zone_name": zone_data["name"],
                    "restriction": zone_data.get("restriction", "neutral"),
                    "rules": self.ZONE_RULES.get(zone_data.get("restriction", "neutral"), self.ZONE_RULES["neutral"])
                }
        
        # Si encontramos una zona cercana (dentro de 1000 metros), la usamos
        if closest_zone and min_distance <= 1000:
            return closest_zone
        
        # Si no está en ninguna zona especial, es zona normal
        return {
            "zone_id": "normal",
            "zone_name": "Zona Normal",
            "restriction": "neutral",
            "rules": self.ZONE_RULES["neutral"]
        }

    def can_pickup_at(self, x: float, y: float) -> Tuple[bool, str]:
        """Verificar si se puede recoger en esta ubicación"""
        zone = self.get_zone_at_location(x, y)
        can_pickup = zone["rules"]["pickup_allowed"]
        message = zone["rules"]["message"]
        return can_pickup, message

    def can_dropoff_at(self, x: float, y: float) -> Tuple[bool, str]:
        """Verificar si se puede dejar en esta ubicación"""
        zone = self.get_zone_at_location(x, y)
        can_dropoff = zone["rules"]["dropoff_allowed"]
        message = zone["rules"]["message"]
        return can_dropoff, message

    def calculate_fare(self, distance_km: float, vehicle_type: str = "auto") -> float:
        """Calcular tarifa del viaje (distancia ya en kilómetros)"""
        if not self.TAXI_ENABLED:
            return 0.0
        
        base_fare = self.TAXI_BASE_RATE
        distance_fare = distance_km * self.TAXI_PER_KM_RATE
        
        # Aplicar multiplicador de vehículo
        vehicle_multiplier = self.VEHICLE_TYPES.get(vehicle_type, {}).get("cost_multiplier", 1.0)
        
        total_fare = (base_fare + distance_fare) * vehicle_multiplier
        return round(total_fare, 2)
    
    def calculate_fare_between_zones(self, origin_zone: dict, dest_zone: dict, vehicle_type: str = "auto") -> float:
        """Calcular tarifa entre dos zonas usando distancia realista"""
        distance_km = self.calculate_zone_distance(origin_zone, dest_zone)
        return self.calculate_fare(distance_km, vehicle_type)

    def get_driver_level(self, total_rides: int) -> Dict:
        """Obtener nivel del conductor basado en viajes completados"""
        current_level = 0
        for rides_required, level_data in self.DRIVER_LEVELS.items():
            if total_rides >= rides_required:
                current_level = rides_required
            else:
                break
        
        return self.DRIVER_LEVELS[current_level]

    def save_config_to_db(self, db_path: str):
        """Guardar configuración en base de datos"""
        import sqlite3
        
        config_data = {
            "feature_enabled": self.FEATURE_ENABLED,
            "taxi_enabled": self.TAXI_ENABLED,
            "bank_enabled": self.BANK_ENABLED,
            "welcome_pack_enabled": self.WELCOME_PACK_ENABLED,
            "welcome_bonus": self.WELCOME_BONUS,
            "taxi_base_rate": self.TAXI_BASE_RATE,
            "taxi_per_km_rate": self.TAXI_PER_KM_RATE,
            "driver_commission": self.DRIVER_COMMISSION,
            "pvp_zones": json.dumps(self.PVP_ZONES),
            "zone_rules": json.dumps(self.ZONE_RULES),
            "vehicle_types": json.dumps(self.VEHICLE_TYPES)
        }
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla de configuración si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taxi_config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar/actualizar configuración
        for key, value in config_data.items():
            cursor.execute("""
                INSERT OR REPLACE INTO taxi_config (config_key, config_value)
                VALUES (?, ?)
            """, (key, str(value)))
        
        conn.commit()
        conn.close()

    def load_config_from_db(self, db_path: str):
        """Cargar configuración desde base de datos"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT config_key, config_value FROM taxi_config")
            config_rows = cursor.fetchall()
            conn.close()
            
            for key, value in config_rows:
                if key == "feature_enabled":
                    self.FEATURE_ENABLED = value.lower() == 'true'
                elif key == "taxi_enabled":
                    self.TAXI_ENABLED = value.lower() == 'true'
                elif key == "bank_enabled":
                    self.BANK_ENABLED = value.lower() == 'true'
                elif key == "welcome_pack_enabled":
                    self.WELCOME_PACK_ENABLED = value.lower() == 'true'
                elif key == "welcome_bonus":
                    self.WELCOME_BONUS = float(value)
                elif key == "taxi_base_rate":
                    self.TAXI_BASE_RATE = float(value)
                elif key == "taxi_per_km_rate":
                    self.TAXI_PER_KM_RATE = float(value)
                elif key == "driver_commission":
                    self.DRIVER_COMMISSION = float(value)
                elif key == "pvp_zones":
                    self.PVP_ZONES = json.loads(value)
                elif key == "zone_rules":
                    self.ZONE_RULES = json.loads(value)
                elif key == "vehicle_types":
                    self.VEHICLE_TYPES = json.loads(value)
                    
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            # Usar valores por defecto si falla

    def find_zone_by_name(self, zone_name: str) -> dict:
        """Buscar zona por nombre (búsqueda flexible)"""
        zone_name_lower = zone_name.lower().strip()
        
        # Buscar coincidencia exacta primero
        for zone_id, zone_data in self.PVP_ZONES.items():
            if zone_data['name'].lower() == zone_name_lower:
                return zone_data
        
        # Buscar coincidencia parcial
        for zone_id, zone_data in self.PVP_ZONES.items():
            if zone_name_lower in zone_data['name'].lower() or zone_data['name'].lower() in zone_name_lower:
                return zone_data
        
        # Buscar por coordenadas (ej: "B2-5")
        for zone_id, zone_data in self.PVP_ZONES.items():
            zone_coords = f"{zone_data.get('grid', '')}-{zone_data.get('pad', '')}"
            if zone_coords.lower() == zone_name_lower:
                return zone_data
        
        # Buscar en taxi stops también
        for stop_id, stop_data in self.TAXI_STOPS.items():
            if stop_data['name'].lower() == zone_name_lower:
                # Convertir formato de stop a formato de zone
                return {
                    'name': stop_data['name'],
                    'type': stop_data['type'],
                    'restriction': 'safe_zone',  # Las paradas son seguras por defecto
                    'grid': stop_data.get('grid', 'B2'),
                    'pad': stop_data.get('pad', 5)
                }
            elif zone_name_lower in stop_data['name'].lower():
                return {
                    'name': stop_data['name'],
                    'type': stop_data['type'],
                    'restriction': 'safe_zone',
                    'grid': stop_data.get('grid', 'B2'),
                    'pad': stop_data.get('pad', 5)
                }
        
        return None

    def validate_vehicle_zone(self, zone_id: str, vehicle_type: str) -> Tuple[bool, str]:
        """Validar si un vehículo puede acceder a una zona específica"""
        try:
            # Buscar la zona
            zone_data = None
            if zone_id in self.PVP_ZONES:
                zone_data = self.PVP_ZONES[zone_id]
            elif zone_id in self.TAXI_STOPS:
                zone_data = self.TAXI_STOPS[zone_id]
            
            if not zone_data:
                return False, f"Zona '{zone_id}' no encontrada"
            
            # Obtener información del vehículo
            if vehicle_type not in self.VEHICLE_TYPES:
                return False, f"Tipo de vehículo '{vehicle_type}' no válido"
            
            vehicle_info = self.VEHICLE_TYPES[vehicle_type]
            vehicle_access_types = vehicle_info.get("access_types", [])
            vehicle_restricted_zones = vehicle_info.get("restricted_zones", [])
            
            # Obtener tipos de acceso de la zona
            zone_access_types = zone_data.get("access_types", ["land", "road"])
            zone_vehicle_access = zone_data.get("vehicle_access", [])
            
            # Verificar si el vehículo está explícitamente permitido en la zona
            if zone_vehicle_access and vehicle_type in zone_vehicle_access:
                return True, "Vehículo permitido en esta zona"
            
            # Verificar si hay al menos un tipo de acceso compatible
            compatible_access = any(access_type in vehicle_access_types for access_type in zone_access_types)
            
            if not compatible_access:
                return False, f"El {vehicle_info['name']} no puede acceder a este tipo de zona"
            
            # Verificar restricciones específicas del vehículo
            zone_type = zone_data.get("type", "normal")
            if zone_type in vehicle_restricted_zones:
                return False, f"El {vehicle_info['name']} no puede acceder a zonas de tipo '{zone_type}'"
            
            # Verificar restricciones de zona específicas
            restriction = zone_data.get("restriction", "neutral")
            if restriction == "no_taxi":
                return False, "Esta zona no permite servicio de taxi"
            
            # Validaciones específicas por tipo de vehículo
            if vehicle_type == "avion":
                # Los aviones necesitan pistas de aterrizaje
                if zone_type not in ["airport", "airstrip"] and "air" not in zone_access_types:
                    return False, "Los aviones necesitan aeropuertos o pistas de aterrizaje"
            
            elif vehicle_type == "barco":
                # Los barcos necesitan acceso al agua
                if "water" not in zone_access_types and "port" not in zone_access_types:
                    return False, "Los barcos necesitan puertos o acceso al agua"
            
            elif vehicle_type == "hidroavion":
                # Los hidroaviones pueden usar agua o pistas especiales
                if not any(access in zone_access_types for access in ["water", "air", "seaplane"]):
                    return False, "Los hidroaviones necesitan agua o pistas especiales"
            
            return True, "Acceso permitido"
            
        except Exception as e:
            return False, f"Error validando zona: {str(e)}"

    def coords_to_grid_pad(self, x: float, y: float) -> str:
        """Convertir coordenadas x,y a formato Grid-Pad (ej: D4-5)"""
        try:
            # SCUM Grid system: -25000 to 25000 dividido en 5x5 grids
            # A = -25000 to -15000, B = -15000 to -5000, C = -5000 to 5000, D = 5000 to 15000, E = 15000 to 25000
            # 0 = -25000 to -15000, 1 = -15000 to -5000, 2 = -5000 to 5000, 3 = 5000 to 15000, 4 = 15000 to 25000
            
            # Calcular grid letter (A-Z)
            grid_x_index = int((x + 25000) // 10000)  # 0-4 para A-E
            grid_y_index = int((y + 25000) // 10000)  # 0-4 para 0-4
            
            # Ajustar límites
            grid_x_index = max(0, min(4, grid_x_index))
            grid_y_index = max(0, min(4, grid_y_index))
            
            # Convertir a letras y números
            grid_letter = chr(ord('A') + grid_x_index)
            grid_number = str(grid_y_index)
            
            # Calcular PAD dentro del grid (1-9)
            # Cada grid es 10000x10000, dividido en 3x3 = ~3333x3333 por pad
            local_x = x - (grid_x_index * 10000 - 25000)
            local_y = y - (grid_y_index * 10000 - 25000)
            
            pad_x = int(local_x // 3333.33)  # 0-2
            pad_y = int(local_y // 3333.33)  # 0-2
            
            # Ajustar límites
            pad_x = max(0, min(2, pad_x))
            pad_y = max(0, min(2, pad_y))
            
            # Convertir a PAD number (1-9)
            # Layout: 7-8-9
            #         4-5-6
            #         1-2-3
            pad_number = (2 - pad_y) * 3 + pad_x + 1
            
            return f"{grid_letter}{grid_number}-{pad_number}"
            
        except Exception as e:
            print(f"Error convirtiendo coordenadas a Grid-Pad: {e}")
            return ""

    async def load_server_config(self, guild_id: str):
        """Cargar configuración específica del servidor desde la base de datos"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Buscar configuración específica del servidor
                cursor = await db.execute("""
                    SELECT * FROM taxi_server_config WHERE guild_id = ?
                """, (guild_id,))
                server_config = await cursor.fetchone()
                
                if server_config:
                    # Mapear columnas a valores
                    columns = [desc[0] for desc in cursor.description]
                    config_dict = dict(zip(columns, server_config))
                    
                    # Aplicar configuración del servidor
                    self._apply_server_config(config_dict)
                    print(f"Configuración cargada para servidor {guild_id}")
                else:
                    # No hay configuración específica, crear una nueva con defaults
                    await self._create_default_server_config(guild_id)
                    print(f"Configuración por defecto creada para servidor {guild_id}")
                    
        except Exception as e:
            print(f"Error cargando configuración del servidor {guild_id}: {e}")
            # Continuar con configuración por defecto
    
    def _apply_server_config(self, config_dict: dict):
        """Aplicar configuración de servidor a las propiedades de la clase"""
        try:
            # Configuración general
            if config_dict.get('feature_enabled') is not None:
                self.FEATURE_ENABLED = bool(config_dict['feature_enabled'])
            if config_dict.get('taxi_enabled') is not None:
                self.TAXI_ENABLED = bool(config_dict['taxi_enabled'])
            if config_dict.get('bank_enabled') is not None:
                self.BANK_ENABLED = bool(config_dict['bank_enabled'])
            if config_dict.get('welcome_pack_enabled') is not None:
                self.WELCOME_PACK_ENABLED = bool(config_dict['welcome_pack_enabled'])
            
            # Configuración económica
            if config_dict.get('welcome_bonus') is not None:
                self.WELCOME_BONUS = float(config_dict['welcome_bonus'])
            if config_dict.get('taxi_base_rate') is not None:
                self.TAXI_BASE_RATE = float(config_dict['taxi_base_rate'])
            if config_dict.get('taxi_per_km_rate') is not None:
                self.TAXI_PER_KM_RATE = float(config_dict['taxi_per_km_rate'])
            if config_dict.get('taxi_wait_rate') is not None:
                self.TAXI_WAIT_RATE = float(config_dict['taxi_wait_rate'])
            if config_dict.get('driver_commission') is not None:
                self.DRIVER_COMMISSION = float(config_dict['driver_commission'])
            if config_dict.get('platform_fee') is not None:
                self.PLATFORM_FEE = float(config_dict['platform_fee'])
            
            # Configuración JSON
            if config_dict.get('vehicle_types'):
                self.VEHICLE_TYPES = json.loads(config_dict['vehicle_types'])
            if config_dict.get('taxi_stops'):
                self.TAXI_STOPS = json.loads(config_dict['taxi_stops'])
            if config_dict.get('pvp_zones'):
                self.PVP_ZONES = json.loads(config_dict['pvp_zones'])
            if config_dict.get('driver_levels'):
                self.DRIVER_LEVELS = json.loads(config_dict['driver_levels'])
                
        except Exception as e:
            print(f"Error aplicando configuración del servidor: {e}")
    
    async def _create_default_server_config(self, guild_id: str, guild_name: str = None):
        """Crear configuración por defecto para un nuevo servidor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insertar configuración por defecto
                await db.execute("""
                    INSERT OR REPLACE INTO taxi_server_config 
                    (guild_id, guild_name, vehicle_types, driver_levels, taxi_stops, pvp_zones, last_modified_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    guild_id,
                    guild_name or f"Servidor {guild_id}",
                    json.dumps(self.VEHICLE_TYPES, ensure_ascii=False),
                    json.dumps(self.DRIVER_LEVELS, ensure_ascii=False),
                    json.dumps(self.TAXI_STOPS, ensure_ascii=False),
                    json.dumps(self.PVP_ZONES, ensure_ascii=False),
                    'system_auto'
                ))
                await db.commit()
                
        except Exception as e:
            print(f"Error creando configuración por defecto: {e}")
    
    async def save_server_config(self, guild_id: str, guild_name: str = None, modified_by: str = None):
        """Guardar configuración actual del servidor en la base de datos"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO taxi_server_config 
                    (guild_id, guild_name, feature_enabled, taxi_enabled, bank_enabled, welcome_pack_enabled,
                     welcome_bonus, taxi_base_rate, taxi_per_km_rate, taxi_wait_rate, driver_commission, platform_fee,
                     vehicle_types, taxi_stops, pvp_zones, driver_levels, updated_at, last_modified_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    guild_id,
                    guild_name or f"Servidor {guild_id}",
                    self.FEATURE_ENABLED,
                    self.TAXI_ENABLED,
                    self.BANK_ENABLED,
                    self.WELCOME_PACK_ENABLED,
                    self.WELCOME_BONUS,
                    self.TAXI_BASE_RATE,
                    self.TAXI_PER_KM_RATE,
                    self.TAXI_WAIT_RATE,
                    self.DRIVER_COMMISSION,
                    self.PLATFORM_FEE,
                    json.dumps(self.VEHICLE_TYPES, ensure_ascii=False),
                    json.dumps(self.TAXI_STOPS, ensure_ascii=False),
                    json.dumps(self.PVP_ZONES, ensure_ascii=False),
                    json.dumps(self.DRIVER_LEVELS, ensure_ascii=False),
                    modified_by or 'system'
                ))
                await db.commit()
                print(f"Configuración guardada para servidor {guild_id}")
                
        except Exception as e:
            print(f"Error guardando configuración del servidor: {e}")
    
    @classmethod
    async def create_for_guild(cls, guild_id: str, guild_name: str = None):
        """Método estático para crear configuración para un guild específico"""
        config = cls()
        config.guild_id = guild_id
        await config.load_server_config(guild_id)
        return config
    
    @classmethod
    def get_default_config(cls):
        """Obtener configuración por defecto sin base de datos"""
        return cls()

# Instancia global con configuración por defecto
taxi_config = TaxiConfig()
