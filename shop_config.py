#!/usr/bin/env python3
"""
Configuración de la Tienda de Supervivencia SCUM
Packs organizados por tiers con cooldowns y limitaciones
"""

from datetime import datetime, timedelta

# === CONFIGURACIÓN DE TIERS ===
TIER_CONFIG = {
    "tier1": {
        "name": "Tier 1 - Básico",
        "emoji": "🟢",
        "cooldown_days": 7,  # 1 semana
        "max_quantity": 5,   # cantidad limitada
        "restock_days": 2,   # se repone cada 2 días
        "description": "Packs básicos para empezar tu aventura de supervivencia"
    },
    "tier2": {
        "name": "Tier 2 - Intermedio", 
        "emoji": "🟡",
        "cooldown_days": 14,  # 2 semanas
        "max_quantity": 3,    # cantidad limitada
        "restock_days": 3,    # se repone cada 3 días
        "description": "Equipamiento avanzado para supervivientes experimentados"
    },
    "tier3": {
        "name": "Tier 3 - Élite",
        "emoji": "🟠", 
        "cooldown_days": 21,  # 3 semanas
        "max_quantity": 3,    # cantidad limitada para autos
        "max_quantity_planes": 2,  # cantidad limitada para aviones
        "restock_days_autos": 14,  # autos se reponen cada 2 semanas
        "restock_days_planes": 7,  # aviones se reponen cada semana
        "description": "Vehículos y equipamiento de élite para los mejores supervivientes"
    }
}

# === PACKS DE SUPERVIVENCIA ===
SHOP_PACKS = {
    # ========== TIER 1 - BÁSICO ==========
    "tier1": {
        "constructor": {
            "name": "Pack del Constructor",
            "description": "Ideal para empezar a construir una base",
            "items": [
                "10x Tablas de madera",
                "50x Clavos", 
                "1x Martillo",
                "1x Sierra"
            ],
            "price_money": 500,
            "price_alt": "1x Rifle básico",
            "stock": 5,
            "category": "construcción"
        },
        "sanitario": {
            "name": "Pack de Sanitario",
            "description": "Ideal para curarse después de un combate",
            "items": [
                "10x Vendas",
                "3x Kits de sutura", 
                "5x Antibióticos",
                "1x Paquete de vitaminas"
            ],
            "price_money": 400,
            "price_alt": "1x Mochila pequeña",
            "stock": 5,
            "category": "médico"
        },
        "explorador": {
            "name": "Pack de Explorador",
            "description": "Ideal para largas expediciones",
            "items": [
                "1x Mochila militar grande",
                "1x Cantimplora",
                "1x Brújula", 
                "1x Par de prismáticos"
            ],
            "price_money": 700,
            "price_alt": "20x Cajas de munición de .22",
            "stock": 5,
            "category": "exploración"
        },
        "asalto_ligero": {
            "name": "Pack de Asalto Ligero",
            "description": "Ideal para combate a corta distancia y defensa de bases",
            "items": [
                "1x Escopeta de doble cañón",
                "30x Cartuchos de escopeta",
                "1x Chaleco táctico"
            ],
            "price_money": 600,
            "price_alt": "2x Garrafas de combustible llenas",
            "stock": 5,
            "category": "combate"
        }
    },
    
    # ========== TIER 2 - INTERMEDIO ==========
    "tier2": {
        "caza": {
            "name": "Pack de Caza",
            "description": "Ideal para proveer de carne y pieles para la base",
            "items": [
                "1x Rifle de caza de un solo tiro",
                "20x Balas de caza",
                "1x Cuchillo de caza",
                "1x Piel de oso"
            ],
            "price_money": 1200,
            "price_alt": "3x Cuchillos de piedra",
            "stock": 3,
            "category": "supervivencia"
        },
        "mecanico": {
            "name": "Pack de Mecánico", 
            "description": "Ideal para poner en marcha un vehículo",
            "items": [
                "1x Kit de reparación de vehículo",
                "1x Garrafa de combustible llena",
                "1x Llave inglesa",
                "1x Batería de coche"
            ],
            "price_money": 1000,
            "price_alt": "1x Rifle de asalto básico",
            "stock": 3,
            "category": "vehículos"
        },
        "ghost": {
            "name": "Pack \"Ghost\" (Furtivo)",
            "description": "Ideal para infiltración silenciosa",
            "items": [
                "1x Pistola silenciada",
                "2x Cargadores de pistola",
                "2x Cajas de munición de pistola",
                "1x Par de binoculares"
            ],
            "price_money": 1500,
            "price_alt": "10x Flechas de caza",
            "stock": 3,
            "category": "sigilo"
        },
        "asalto_pesado": {
            "name": "Pack de Asalto Pesado",
            "description": "Ideal para incursiones contra otros escuadrones",
            "items": [
                "1x Rifle de asalto M16",
                "3x Cargadores de M16", 
                "5x Cajas de munición de 5.56mm"
            ],
            "price_money": 1800,
            "price_alt": "1x Mochila militar grande",
            "stock": 3,
            "category": "combate"
        }
    },
    
    # ========== TIER 3 - ÉLITE ==========
    "tier3": {
        "francotirador": {
            "name": "Pack de Francotirador",
            "description": "Ideal para eliminar amenazas a distancia",
            "items": [
                "1x Rifle de francotirador M1",
                "1x Mira de francotirador 4x",
                "2x Cargadores de M1",
                "2x Cajas de munición de .308"
            ],
            "price_money": 3000,
            "price_alt": "1x Coche todoterreno",
            "stock": 3,
            "category": "precisión"
        },
        "carga_pesada": {
            "name": "Pack de Carga Pesada",
            "description": "Ideal para llevar todo el loot posible",
            "items": [
                "1x Mochila militar grande",
                "1x Mochila de camuflaje",
                "1x Mochila de senderismo"
            ],
            "price_money": 2500,
            "price_alt": "1x Rifle de francotirador",
            "stock": 3,
            "category": "utilidad"
        },
        # === VEHÍCULOS LIMITADOS ===
        "auto_limitado_1": {
            "name": "Vehículo Todoterreno Blindado",
            "description": "Vehículo resistente para territorios hostiles",
            "items": [
                "1x SUV Blindado",
                "Kit de reparación completo",
                "Combustible para 500km",
                "Neumáticos de repuesto"
            ],
            "price_money": 15000,
            "price_alt": "5x Rifles de asalto completos",
            "stock": 3,
            "category": "vehículo_limitado",
            "restock_days": 14
        },
        "auto_limitado_2": {
            "name": "Camión de Transporte Militar",
            "description": "Para transportar equipo pesado y múltiples supervivientes",
            "items": [
                "1x Camión Militar",
                "Kit de blindaje adicional", 
                "Sistema de comunicaciones",
                "Compartimento de almacenamiento"
            ],
            "price_money": 20000,
            "price_alt": "1x Base completa + defensas",
            "stock": 3,
            "category": "vehículo_limitado",
            "restock_days": 14
        },
        # === AVIONES ===
        "avion_comun_1": {
            "name": "Avioneta de Reconocimiento",
            "description": "Para exploración aérea y transporte rápido",
            "items": [
                "1x Avioneta Cessna",
                "Kit de mantenimiento",
                "Combustible para 200km",
                "Equipo de navegación"
            ],
            "price_money": 25000,
            "price_alt": "10x Vehículos terrestres",
            "stock": 2,
            "category": "avion",
            "restock_days": 7
        },
        "avion_comun_2": {
            "name": "Helicóptero de Combate",
            "description": "Superioridad aérea y apoyo de fuego",
            "items": [
                "1x Helicóptero Militar",
                "Sistema de armas integrado",
                "Blindaje reforzado",
                "Combustible para 150km"
            ],
            "price_money": 35000,
            "price_alt": "1x Flota de vehículos completa",
            "stock": 2,
            "category": "avion", 
            "restock_days": 7
        }
    }
}

# === CATEGORÍAS DE PACKS ===
PACK_CATEGORIES = {
    "construcción": {"emoji": "🔨", "name": "Construcción"},
    "médico": {"emoji": "🏥", "name": "Médico"},
    "exploración": {"emoji": "🧭", "name": "Exploración"}, 
    "combate": {"emoji": "⚔️", "name": "Combate"},
    "supervivencia": {"emoji": "🦌", "name": "Supervivencia"},
    "vehículos": {"emoji": "🔧", "name": "Vehículos"},
    "sigilo": {"emoji": "👤", "name": "Sigilo"},
    "precisión": {"emoji": "🎯", "name": "Precisión"},
    "utilidad": {"emoji": "🎒", "name": "Utilidad"},
    "vehículo_limitado": {"emoji": "🚗", "name": "Vehículo Limitado"},
    "avion": {"emoji": "✈️", "name": "Aeronave"}
}

def get_pack_by_id(pack_id: str) -> dict:
    """Obtener un pack específico por su ID"""
    for tier, packs in SHOP_PACKS.items():
        if pack_id in packs:
            pack_data = packs[pack_id].copy()
            pack_data["tier"] = tier
            pack_data["id"] = pack_id
            return pack_data
    return None

def get_packs_by_tier(tier: str) -> dict:
    """Obtener todos los packs de un tier específico"""
    return SHOP_PACKS.get(tier, {})

def get_available_packs(tier: str, user_id: int = None) -> dict:
    """Obtener packs disponibles considerando stock y cooldowns"""
    # Por ahora devuelve todos los packs del tier
    # En el futuro se implementará el sistema de stock y cooldowns
    return get_packs_by_tier(tier)