#!/usr/bin/env python3
"""
Propuestas de Optimización Económica para el Sistema de Taxi SCUM
"""

from economic_calculator import EconomicCalculator
import math

class EconomicOptimizer:
    def __init__(self):
        self.current = EconomicCalculator()
        
    def propose_optimizations(self):
        """Proponer optimizaciones a la economía actual"""
        
        print("=" * 70)
        print("PROPUESTAS DE OPTIMIZACION ECONOMICA")
        print("=" * 70)
        
        print("\nPROBLEMAS IDENTIFICADOS:")
        print("1. Progresión muy lenta para objetivos altos ($20K-$30K)")
        print("2. Dependencia excesiva en viajes de taxi para progresión razonable")
        print("3. Canje diario muy bajo comparado con el welcome bonus")
        print("4. Falta de incentivos para jugadores activos")
        
        print("\n" + "="*50)
        print("PROPUESTA 1: OPTIMIZACION CONSERVADORA")
        print("="*50)
        
        # Propuesta 1: Optimización conservadora
        opt1 = self.test_optimization_1()
        self.print_optimization_results("Conservadora", opt1)
        
        print("\n" + "="*50)
        print("PROPUESTA 2: OPTIMIZACION BALANCEADA")
        print("="*50)
        
        # Propuesta 2: Optimización balanceada
        opt2 = self.test_optimization_2()
        self.print_optimization_results("Balanceada", opt2)
        
        print("\n" + "="*50)
        print("PROPUESTA 3: OPTIMIZACION AGRESIVA")
        print("="*50)
        
        # Propuesta 3: Optimización agresiva
        opt3 = self.test_optimization_3()
        self.print_optimization_results("Agresiva", opt3)
        
        print("\n" + "="*50)
        print("RECOMENDACION FINAL")
        print("="*50)
        self.print_final_recommendation()
    
    def test_optimization_1(self):
        """Optimización conservadora"""
        config = {
            'welcome_bonus': 5000,  # Sin cambios
            'daily_reward': 350,    # +100 (+40%)
            'taxi_commission': 0.80,  # +5% comisión conductor
            'description': 'Mejora modesta manteniendo balance'
        }
        return self.calculate_with_config(config)
    
    def test_optimization_2(self):
        """Optimización balanceada"""
        config = {
            'welcome_bonus': 7500,   # +2500 (+50%)
            'daily_reward': 500,     # +250 (+100%)
            'taxi_commission': 0.85,   # +10% comisión conductor
            'description': 'Mejora significativa manteniendo incentivos taxi'
        }
        return self.calculate_with_config(config)
    
    def test_optimization_3(self):
        """Optimización agresiva"""
        config = {
            'welcome_bonus': 10000,  # +5000 (+100%)
            'daily_reward': 750,     # +500 (+200%)
            'taxi_commission': 0.90,   # +15% comisión conductor
            'description': 'Progresión rápida, riesgo de inflación'
        }
        return self.calculate_with_config(config)
    
    def calculate_with_config(self, config):
        """Calcular tiempos con configuración específica"""
        welcome = config['welcome_bonus']
        daily = config['daily_reward']
        commission = config['taxi_commission']
        
        # Calcular ganancia de taxi con nueva comisión
        taxi_5km_total = 15 + (5 * 3.5)  # $32.5 total
        taxi_5km_driver = taxi_5km_total * commission
        
        results = {}
        targets = [10000, 20000, 30000]
        
        for target in targets:
            remaining = target - welcome
            
            # Solo canje diario
            days_daily_only = math.ceil(remaining / daily)
            
            # Con 2 viajes/día
            daily_with_2_trips = daily + (2 * taxi_5km_driver)
            days_with_2_trips = math.ceil(remaining / daily_with_2_trips)
            
            # Con 5 viajes/día
            daily_with_5_trips = daily + (5 * taxi_5km_driver)
            days_with_5_trips = math.ceil(remaining / daily_with_5_trips)
            
            results[target] = {
                'daily_only': {
                    'days': days_daily_only,
                    'weeks': round(days_daily_only / 7, 1),
                    'months': round(days_daily_only / 30, 1)
                },
                'with_2_trips': {
                    'days': days_with_2_trips,
                    'weeks': round(days_with_2_trips / 7, 1)
                },
                'with_5_trips': {
                    'days': days_with_5_trips,
                    'weeks': round(days_with_5_trips / 7, 1)
                }
            }
        
        config['results'] = results
        config['taxi_5km_driver'] = round(taxi_5km_driver, 2)
        return config
    
    def print_optimization_results(self, name, config):
        """Imprimir resultados de optimización"""
        print(f"\nConfiguracion {name}:")
        print(f"  - Welcome Bonus: ${config['welcome_bonus']:,} (cambio: {config['welcome_bonus'] - 5000:+,})")
        print(f"  - Canje Diario: ${config['daily_reward']:,} (cambio: {config['daily_reward'] - 250:+,})")
        print(f"  - Comision Conductor: {config['taxi_commission']*100:.0f}% (cambio: {(config['taxi_commission'] - 0.75)*100:+.0f}%)")
        print(f"  - Ganancia Taxi 5km: ${config['taxi_5km_driver']:.2f} (vs ${24.38:.2f} actual)")
        print(f"  - Descripcion: {config['description']}")
        
        print(f"\nTiempos para objetivos:")
        for target, data in config['results'].items():
            print(f"  ${target:,}:")
            print(f"    Solo canje: {data['daily_only']['days']} dias ({data['daily_only']['months']} meses)")
            print(f"    +2 viajes:  {data['with_2_trips']['days']} dias ({data['with_2_trips']['weeks']} semanas)")
            print(f"    +5 viajes:  {data['with_5_trips']['days']} dias ({data['with_5_trips']['weeks']} semanas)")
    
    def print_final_recommendation(self):
        """Imprimir recomendación final"""
        print("\nRECOMENDACION: OPTIMIZACION BALANCEADA")
        print("\nCambios propuestos:")
        print("  * Welcome Bonus: $5,000 -> $7,500 (+50%)")
        print("  * Canje Diario: $250 -> $500 (+100%)")
        print("  * Comision Conductor: 75% -> 85% (+10%)")
        
        print("\nBeneficios:")
        print("  - Progresion mas rapida pero no exagerada")
        print("  - Mantiene incentivos para usar el sistema de taxi")
        print("  - Reduce frustracion de usuarios casuales")
        print("  - Permite llegar a $20K en ~1 mes con actividad moderada")
        
        print("\nImplementacion sugerida:")
        print("  1. Aumentar WELCOME_BONUS de 5000 a 7500 en taxi_config.py")
        print("  2. Cambiar daily_amount de 250 a 500 en banking_system.py") 
        print("  3. Aumentar DRIVER_COMMISSION de 0.75 a 0.85 en taxi_config.py")
        
        print("\nImpacto esperado:")
        print("  - $10K: De 20 dias -> 5 dias (solo canje)")
        print("  - $20K: De 60 dias -> 25 dias (solo canje)")
        print("  - $30K: De 100 dias -> 45 dias (solo canje)")
        print("  - Con 2-3 viajes diarios: objetivos en 50% menos tiempo")

if __name__ == "__main__":
    optimizer = EconomicOptimizer()
    optimizer.propose_optimizations()