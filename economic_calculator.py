#!/usr/bin/env python3
"""
Calculadora Económica del Sistema de Taxi SCUM
Analiza cuánto tiempo toma llegar a diferentes objetivos monetarios
"""

from typing import Dict, List, Tuple
import math

class EconomicCalculator:
    def __init__(self):
        # Configuración económica actual
        self.WELCOME_BONUS = 5000.0
        self.DAILY_REWARD = 250.0
        
        # Configuración de taxi
        self.TAXI_BASE_RATE = 15.0
        self.TAXI_PER_KM_RATE = 3.5
        self.DRIVER_COMMISSION = 0.75  # 75% para el conductor
        
        # Objetivos monetarios
        self.TARGETS = [10000, 20000, 30000]
        
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
        """Analizar ganancias por diferentes distancias de taxi"""
        distances = [1, 2, 5, 10, 15, 20, 30]  # km
        analysis = {}
        
        for distance in distances:
            fare_info = self.calculate_taxi_fare(distance)
            analysis[f"{distance}km"] = {
                'distance': distance,
                'total_fare': fare_info['total_fare'],
                'driver_earning': fare_info['driver_earning'],
                'trips_for_1000': math.ceil(1000 / fare_info['driver_earning']),
                'trips_for_5000': math.ceil(5000 / fare_info['driver_earning'])
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
        
        # Scenario 2: Canje diario + taxi promedio (viajes de 5km)
        avg_taxi_earning = self.calculate_taxi_fare(5)['driver_earning']  # ~28.75
        
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
        """Generar recomendaciones para optimizar la economía"""
        avg_5km = self.calculate_taxi_fare(5)['driver_earning']
        avg_10km = self.calculate_taxi_fare(10)['driver_earning']
        
        return {
            'daily_minimum': f"Con solo el canje diario (${self.DAILY_REWARD}), necesitas {math.ceil(5000/self.DAILY_REWARD)} días para $5K adicionales",
            'efficient_taxi': f"Viajes de 5-10km son más eficientes: ${avg_5km:.2f} - ${avg_10km:.2f} por viaje",
            'target_10k': "Para llegar a $10K desde $5K: 2-3 viajes de taxi diarios + canje = ~1 semana",
            'target_20k': "Para llegar a $20K desde $10K: 3-5 viajes diarios + canje = ~2-3 semanas",
            'target_30k': "Para llegar a $30K desde $20K: 5+ viajes diarios + canje = ~3-4 semanas"
        }

# Función principal para generar el reporte
def main():
    calculator = EconomicCalculator()
    report = calculator.generate_progression_report()
    
    print("=" * 60)
    print("ANALISIS ECONOMICO DEL SISTEMA DE TAXI SCUM")
    print("=" * 60)
    
    print(f"\nConfiguracion Economica:")
    print(f"   - Welcome Bonus: ${report['welcome_bonus']:,.0f}")
    print(f"   - Canje Diario: ${report['daily_reward']:,.0f}")
    
    print(f"\nAnalisis de Ganancias por Viaje de Taxi:")
    for distance, data in report['taxi_analysis'].items():
        print(f"   - {distance}: ${data['driver_earning']:.2f} por viaje ({data['trips_for_1000']} viajes = $1,000)")
    
    print(f"\nTiempo para Alcanzar Objetivos (partiendo de $5,000):")
    for target_key, data in report['progression'].items():
        target = data['target']
        scenarios = data['scenarios']
        print(f"\n   Objetivo: ${target:,.0f}")
        print(f"      Solo canje diario: {scenarios['0_trips_per_day']['days_needed']} dias ({scenarios['0_trips_per_day']['months_needed']} meses)")
        print(f"      Con 2 viajes/dia: {scenarios['2_trips_per_day']['days_needed']} dias ({scenarios['2_trips_per_day']['weeks_needed']} semanas)")
        print(f"      Con 5 viajes/dia: {scenarios['5_trips_per_day']['days_needed']} dias ({scenarios['5_trips_per_day']['weeks_needed']} semanas)")
    
    print(f"\nRecomendaciones:")
    for key, recommendation in report['recommendations'].items():
        print(f"   - {recommendation}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()