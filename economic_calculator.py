#!/usr/bin/env python3
"""
Calculadora Económica del Sistema de Taxi SCUM
Analiza cuánto tiempo toma llegar a diferentes objetivos monetarios
ACTUALIZADO: Usa el nuevo sistema de distancias realistas basado en grids
"""

from typing import Dict, List, Tuple
import math
import sys
import os

# Agregar el path actual para importar taxi_config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class EconomicCalculator:
    def __init__(self, guild_id: str = None, taxi_config_instance=None):
        # Importar configuración del sistema de taxi real
        self.guild_id = guild_id
        
        # Si se proporciona una instancia de configuración directamente, usarla
        if taxi_config_instance:
            self.taxi_config = taxi_config_instance
        else:
            try:
                if guild_id:
                    # Para uso con guild_id específico, usar configuración por defecto temporalmente
                    # La configuración específica debe ser pasada como taxi_config_instance
                    print(f"ADVERTENCIA: Para guild {guild_id}, usar configuración por defecto. Para usar configuración específica, pasar taxi_config_instance.")
                    from taxi_config import taxi_config
                    self.taxi_config = taxi_config
                else:
                    # Usar configuración por defecto
                    from taxi_config import taxi_config
                    self.taxi_config = taxi_config
            except ImportError:
                print("ADVERTENCIA: No se pudo importar taxi_config, usando valores por defecto")
                self.taxi_config = None
            except Exception as e:
                print(f"ADVERTENCIA: Error cargando configuración: {e}")
                from taxi_config import taxi_config
                self.taxi_config = taxi_config
        
        # Configuración económica actual
        self.WELCOME_BONUS = 7500.0
        self.DAILY_REWARD = 500.0
        
        # Configuración de taxi (desde taxi_config si está disponible)
        if self.taxi_config:
            self.TAXI_BASE_RATE = self.taxi_config.TAXI_BASE_RATE
            self.TAXI_PER_KM_RATE = self.taxi_config.TAXI_PER_KM_RATE
        else:
            self.TAXI_BASE_RATE = 15.0
            self.TAXI_PER_KM_RATE = 3.5
            
        self.DRIVER_COMMISSION = 0.75  # 75% para el conductor
        
        # Objetivos monetarios
        self.TARGETS = [10000, 20000, 30000]
        
        # Rutas típicas del juego basadas en grids reales
        self.TYPICAL_ROUTES = self.define_realistic_routes()
    
    def define_realistic_routes(self) -> Dict[str, Dict]:
        """Definir rutas típicas basadas en el sistema de grids de SCUM"""
        return {
            'local_city': {
                'name': 'Viaje local en ciudad (B2)',
                'origin': {'grid': 'B2', 'pad': 1, 'name': 'Ciudad Sur'},
                'dest': {'grid': 'B2', 'pad': 9, 'name': 'Ciudad Norte'},
                'description': 'Viaje corto dentro de la misma ciudad'
            },
            'adjacent_grids': {
                'name': 'Grids adyacentes (B2 -> C2)',
                'origin': {'grid': 'B2', 'pad': 5, 'name': 'Ciudad Central'},
                'dest': {'grid': 'C2', 'pad': 5, 'name': 'Zona Norte'},
                'description': 'Viaje típico entre zonas cercanas'
            },
            'medium_distance': {
                'name': 'Distancia media (A1 -> C3)',
                'origin': {'grid': 'A1', 'pad': 5, 'name': 'Sur Centro'},
                'dest': {'grid': 'C3', 'pad': 5, 'name': 'Norte Oeste'},
                'description': 'Viaje de distancia moderada'
            },
            'long_distance': {
                'name': 'Viaje largo (B2 -> Z0)',
                'origin': {'grid': 'B2', 'pad': 5, 'name': 'Ciudad Central'},
                'dest': {'grid': 'Z0', 'pad': 5, 'name': 'Extremo Sur'},
                'description': 'Viaje de larga distancia'
            },
            'cross_map': {
                'name': 'Cruzar todo el mapa (D4 -> Z0)',
                'origin': {'grid': 'D4', 'pad': 1, 'name': 'Extremo Noroeste'},
                'dest': {'grid': 'Z0', 'pad': 9, 'name': 'Extremo Sureste'},
                'description': 'Máxima distancia posible en el mapa'
            }
        }
    
    def calculate_realistic_fare(self, route_key: str, vehicle_type: str = "auto") -> Dict[str, float]:
        """Calcular tarifa usando el sistema de grids realista"""
        if not self.taxi_config or route_key not in self.TYPICAL_ROUTES:
            # Fallback al método anterior
            return self.calculate_taxi_fare(10.0)  # 10km por defecto
        
        route = self.TYPICAL_ROUTES[route_key]
        origin_zone = route['origin']
        dest_zone = route['dest']
        
        # Usar el nuevo sistema de cálculo de distancias
        distance_km = self.taxi_config.calculate_zone_distance(origin_zone, dest_zone)
        total_fare = self.taxi_config.calculate_fare(distance_km, vehicle_type)
        driver_earning = total_fare * self.DRIVER_COMMISSION
        
        return {
            'route_name': route['name'],
            'distance_km': round(distance_km, 1),
            'total_fare': round(total_fare, 2),
            'driver_earning': round(driver_earning, 2),
            'platform_fee': round(total_fare - driver_earning, 2),
            'description': route['description']
        }
        
    def calculate_taxi_fare(self, distance_km: float) -> Dict[str, float]:
        """Calcular ganancia de un viaje de taxi"""
        base_fare = self.TAXI_BASE_RATE
        distance_fare = distance_km * self.TAXI_PER_KM_RATE
        total_fare = base_fare + distance_fare
        driver_earning = total_fare * self.DRIVER_COMMISSION
        
        return {
            'total_fare': round(total_fare, 2),
            'driver_earning': round(driver_earning, 2),
            'platform_fee': round(total_fare - driver_earning, 2)
        }
    
    def analyze_taxi_distances(self) -> Dict[str, Dict]:
        """Analizar ganancias por diferentes rutas realistas de taxi"""
        analysis = {}
        
        # Analizar rutas realistas del juego
        for route_key in self.TYPICAL_ROUTES.keys():
            fare_info = self.calculate_realistic_fare(route_key)
            
            # Calcular cuántos viajes se necesitan para objetivos comunes
            driver_earning = fare_info['driver_earning']
            
            analysis[route_key] = {
                'route_name': fare_info['route_name'],
                'distance_km': fare_info['distance_km'],
                'total_fare': fare_info['total_fare'],
                'driver_earning': driver_earning,
                'trips_for_1000': math.ceil(1000 / driver_earning) if driver_earning > 0 else 0,
                'trips_for_5000': math.ceil(5000 / driver_earning) if driver_earning > 0 else 0,
                'trips_for_10000': math.ceil(10000 / driver_earning) if driver_earning > 0 else 0,
                'description': fare_info['description']
            }
        
        # También incluir análisis por tipos de vehículo para la ruta más común
        if self.taxi_config:
            common_route = 'adjacent_grids'  # Ruta típica
            vehicle_analysis = {}
            
            for vehicle_type in ['auto', 'moto', 'avion', 'hidroavion', 'barco']:
                fare_info = self.calculate_realistic_fare(common_route, vehicle_type)
                vehicle_analysis[vehicle_type] = {
                    'total_fare': fare_info['total_fare'],
                    'driver_earning': fare_info['driver_earning'],
                    'distance_km': fare_info['distance_km']
                }
            
            analysis['vehicle_comparison'] = {
                'route_name': f"Comparación de vehículos ({self.TYPICAL_ROUTES[common_route]['name']})",
                'vehicles': vehicle_analysis
            }
        
        return analysis
    
    def calculate_time_to_target(self, target: float, starting_amount: float = 0) -> Dict[str, any]:
        """Calcular tiempo para llegar a un objetivo monetario"""
        remaining = target - starting_amount
        
        if remaining <= 0:
            return {
                'target': target,
                'already_reached': True,
                'excess': abs(remaining)
            }
        
        # Scenario 1: Solo canje diario
        days_daily_only = math.ceil(remaining / self.DAILY_REWARD)
        
        # Scenario 2: Canje diario + taxi promedio (rutas típicas realistas)
        # Usar ruta adyacente como promedio típico
        avg_taxi_earning = self.calculate_realistic_fare('adjacent_grids')['driver_earning']
        
        scenarios = {}
        
        # Diferentes combinaciones de viajes por día
        for trips_per_day in [0, 1, 2, 3, 5, 10]:
            daily_taxi_income = trips_per_day * avg_taxi_earning
            total_daily_income = self.DAILY_REWARD + daily_taxi_income
            days_needed = math.ceil(remaining / total_daily_income)
            
            scenarios[f"{trips_per_day}_trips_per_day"] = {
                'trips_per_day': trips_per_day,
                'daily_taxi_income': round(daily_taxi_income, 2),
                'total_daily_income': round(total_daily_income, 2),
                'days_needed': days_needed,
                'weeks_needed': round(days_needed / 7, 1),
                'months_needed': round(days_needed / 30, 1)
            }
        
        return {
            'target': target,
            'remaining': remaining,
            'starting_amount': starting_amount,
            'scenarios': scenarios
        }
    
    def generate_progression_report(self) -> Dict:
        """Generar reporte completo de progresión económica"""
        taxi_analysis = self.analyze_taxi_distances()
        
        # Calcular para cada objetivo, partiendo del welcome bonus
        progression = {}
        
        for target in self.TARGETS:
            progression[f"target_{target}"] = self.calculate_time_to_target(target, self.WELCOME_BONUS)
        
        return {
            'welcome_bonus': self.WELCOME_BONUS,
            'daily_reward': self.DAILY_REWARD,
            'taxi_analysis': taxi_analysis,
            'progression': progression,
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> Dict[str, str]:
        """Generar recomendaciones para optimizar la economía usando rutas realistas"""
        
        # Obtener ganancias de diferentes tipos de rutas
        local_earning = self.calculate_realistic_fare('local_city')['driver_earning']
        adjacent_earning = self.calculate_realistic_fare('adjacent_grids')['driver_earning']
        medium_earning = self.calculate_realistic_fare('medium_distance')['driver_earning']
        long_earning = self.calculate_realistic_fare('long_distance')['driver_earning']
        cross_earning = self.calculate_realistic_fare('cross_map')['driver_earning']
        
        return {
            'daily_minimum': f"Con solo el canje diario (${self.DAILY_REWARD}), necesitas {math.ceil(5000/self.DAILY_REWARD)} días para $5K adicionales",
            'efficient_routes': f"Rutas más eficientes por tiempo: Locales ${local_earning:.2f}, Adyacentes ${adjacent_earning:.2f}",
            'high_earning_routes': f"Rutas de alta ganancia: Distancia media ${medium_earning:.2f}, Largo ${long_earning:.2f}, Cruz completa ${cross_earning:.2f}",
            'target_10k': f"Para $10K desde welcome bonus: {math.ceil((10000-self.WELCOME_BONUS)/adjacent_earning)} viajes adyacentes o {math.ceil((10000-self.WELCOME_BONUS)/(self.DAILY_REWARD + adjacent_earning))} días con 1 viaje + canje diario",
            'target_20k': f"Para $20K desde $10K: {math.ceil(10000/medium_earning)} viajes de distancia media o {math.ceil(10000/(self.DAILY_REWARD + 2*adjacent_earning))} días con 2 viajes + canje",
            'target_30k': f"Para $30K desde $20K: {math.ceil(10000/long_earning)} viajes largos o {math.ceil(10000/(self.DAILY_REWARD + 3*adjacent_earning))} días con 3 viajes + canje",
            'grid_strategy': "ESTRATEGIA: Combina viajes locales rápidos con algunos viajes largos de alta ganancia para optimizar tiempo vs. beneficio"
        }

# Función principal para generar el reporte
def main():
    # Usar configuración por defecto si no se especifica guild_id
    calculator = EconomicCalculator()
    report = calculator.generate_progression_report()
    
    print("=" * 70)
    print("ANALISIS ECONOMICO DEL SISTEMA DE TAXI SCUM")
    print("BASADO EN GRIDS REALISTAS Y DISTANCIAS DE CAMINOS")
    print("=" * 70)
    
    print(f"\nConfiguracion Economica:")
    print(f"   - Welcome Bonus: ${report['welcome_bonus']:,.0f}")
    print(f"   - Canje Diario: ${report['daily_reward']:,.0f}")
    
    print(f"\nAnalisis de Rutas Realistas de Taxi:")
    for route_key, data in report['taxi_analysis'].items():
        if route_key == 'vehicle_comparison':
            print(f"\n   {data['route_name']}:")
            for vehicle, vehicle_data in data['vehicles'].items():
                print(f"      {vehicle.upper()}: ${vehicle_data['total_fare']:.2f} total, ${vehicle_data['driver_earning']:.2f} conductor")
        else:
            print(f"\n   {data['route_name']} ({data['distance_km']:.1f}km):")
            print(f"      Ganancia conductor: ${data['driver_earning']:.2f}")
            print(f"      Viajes para $1K: {data['trips_for_1000']}")
            print(f"      Viajes para $5K: {data['trips_for_5000']}")
            print(f"      Viajes para $10K: {data['trips_for_10000']}")
    
    print(f"\nTiempo para Alcanzar Objetivos (partiendo desde Welcome Bonus $7,500):")
    for target_key, data in report['progression'].items():
        target = data['target']
        scenarios = data['scenarios']
        print(f"\n   Objetivo: ${target:,.0f}")
        print(f"      Solo canje diario: {scenarios['0_trips_per_day']['days_needed']} dias ({scenarios['0_trips_per_day']['months_needed']} meses)")
        print(f"      Con 2 viajes/dia: {scenarios['2_trips_per_day']['days_needed']} dias ({scenarios['2_trips_per_day']['weeks_needed']} semanas)")
        print(f"      Con 5 viajes/dia: {scenarios['5_trips_per_day']['days_needed']} dias ({scenarios['5_trips_per_day']['weeks_needed']} semanas)")
    
    print(f"\nRecomendaciones Basadas en Grids SCUM:")
    for key, recommendation in report['recommendations'].items():
        print(f"   - {recommendation}")
    
    print("\n" + "=" * 70)
    print("NOTA: Distancias calculadas usando grids 3x3km con factor de caminos 1.4x")
    print("Rutas basadas en el mapa real de SCUM (D4-D3-D2-C2-B2-A1-Z1-Z0)")
    print("=" * 70)

if __name__ == "__main__":
    main()