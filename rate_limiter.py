#!/usr/bin/env python3
"""
Sistema de Rate Limiting - Versión Mínima que NO interfiere con el registro
"""

import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.user_commands = defaultdict(lambda: defaultdict(lambda: defaultdict(deque)))
        self.guild_commands = defaultdict(lambda: defaultdict(deque))
        self.lock = asyncio.Lock()
        
        self.command_limits = {
            # === SISTEMA BANCARIO ===
            'banco_balance': {'user_rate': (10, 60), 'guild_rate': (50, 60), 'cooldown': 5},
            'banco_transferir': {'user_rate': (5, 300), 'guild_rate': (20, 60), 'cooldown': 15},
            'banco_historial': {'user_rate': (8, 60), 'guild_rate': (30, 60), 'cooldown': 8},
            
            # === SISTEMA DE BUNKERS ===
            'ba_check_bunker': {'user_rate': (15, 60), 'guild_rate': (80, 60), 'cooldown': 2},
            'ba_status_all': {'user_rate': (8, 60), 'guild_rate': (30, 60), 'cooldown': 5},
            'ba_my_usage': {'user_rate': (6, 60), 'guild_rate': (20, 60), 'cooldown': 8},
            'ba_help': {'user_rate': (5, 300), 'guild_rate': (15, 60), 'cooldown': 15},
            'ba_bot_status': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            'ba_suscripcion': {'user_rate': (3, 300), 'guild_rate': (12, 60), 'cooldown': 20},
            'ba_add_server': {'user_rate': (5, 300), 'guild_rate': (8, 300), 'cooldown': 30},
            'ba_remove_server': {'user_rate': (3, 600), 'guild_rate': (5, 300), 'cooldown': 15},
            'ba_list_servers': {'user_rate': (10, 60), 'guild_rate': (40, 60), 'cooldown': 3},
            
            # === COMANDOS ADMIN DE BUNKERS ===
            'ba_admin_status': {'user_rate': (10, 60), 'guild_rate': (30, 60), 'cooldown': 5},
            'ba_admin_upgrade': {'user_rate': (3, 600), 'guild_rate': (5, 600), 'cooldown': 60},
            'ba_admin_cancel': {'user_rate': (3, 600), 'guild_rate': (5, 600), 'cooldown': 60},
            'ba_admin_resync': {'user_rate': (5, 300), 'guild_rate': (8, 300), 'cooldown': 30},
            'ba_admin_shutdown': {'user_rate': (2, 3600), 'guild_rate': (2, 3600), 'cooldown': 300},
            
            # === SISTEMA DE MECÁNICO Y SEGUROS ===
            'seguro_solicitar': {'user_rate': (5, 300), 'guild_rate': (30, 60), 'cooldown': 30},
            'seguro_consultar': {'user_rate': (10, 60), 'guild_rate': (40, 60), 'cooldown': 5},
            'mechanic_notifications': {'user_rate': (5, 300), 'guild_rate': (15, 300), 'cooldown': 30},
            'mechanic_admin_register': {'user_rate': (10, 60), 'guild_rate': (20, 60), 'cooldown': 5},
            'mechanic_admin_remove': {'user_rate': (5, 300), 'guild_rate': (10, 300), 'cooldown': 30},
            'mechanic_admin_list': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            'mechanic_admin_config_pvp': {'user_rate': (8, 300), 'guild_rate': (12, 300), 'cooldown': 20},
            'mechanic_admin_set_price': {'user_rate': (10, 300), 'guild_rate': (20, 300), 'cooldown': 15},
            'mechanic_admin_list_prices': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            'mechanic_admin_set_limit': {'user_rate': (8, 300), 'guild_rate': (15, 300), 'cooldown': 20},
            'mechanic_admin_list_limits': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            
            # === SISTEMA DE ESCUADRONES ===
            'squadron_admin_config_limits': {'user_rate': (6, 600), 'guild_rate': (10, 600), 'cooldown': 60},
            'squadron_admin_view_config': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            'squadron_admin_remove_member': {'user_rate': (8, 300), 'guild_rate': (15, 300), 'cooldown': 20},
            'squadron_admin_view_member': {'user_rate': (10, 60), 'guild_rate': (30, 60), 'cooldown': 5},
            'squadron_admin_cleanup': {'user_rate': (3, 600), 'guild_rate': (5, 600), 'cooldown': 120},
            
            # === SISTEMA DE TAXI ===
            'taxi_solicitar': {'user_rate': (5, 300), 'guild_rate': (25, 60), 'cooldown': 30},
            'taxi_status': {'user_rate': (10, 60), 'guild_rate': (40, 60), 'cooldown': 3},
            'taxi_cancelar': {'user_rate': (5, 300), 'guild_rate': (20, 60), 'cooldown': 5},
            'taxi_zonas': {'user_rate': (8, 300), 'guild_rate': (25, 60), 'cooldown': 15},
            'taxi_tarifas': {'user_rate': (8, 300), 'guild_rate': (25, 60), 'cooldown': 15},
            'ba_reset_alerts': {'user_rate': (5, 300), 'guild_rate': (15, 300), 'cooldown': 30},
            'taxi_admin_stats': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            'taxi_admin_tarifa': {'user_rate': (8, 300), 'guild_rate': (15, 300), 'cooldown': 20},
            'taxi_admin_refresh': {'user_rate': (5, 300), 'guild_rate': (10, 300), 'cooldown': 30},
            'taxi_admin_expiration': {'user_rate': (5, 600), 'guild_rate': (8, 600), 'cooldown': 60},
            'taxi_admin_leaderboard': {'user_rate': (8, 60), 'guild_rate': (25, 60), 'cooldown': 5},
            
            # === SISTEMA PREMIUM/SHOP ===
            'ba_plans': {'user_rate': (8, 300), 'guild_rate': (25, 60), 'cooldown': 15},
            'ba_admin_subs': {'user_rate': (8, 300), 'guild_rate': (15, 300), 'cooldown': 20},
            'ba_stats': {'user_rate': (10, 60), 'guild_rate': (35, 60), 'cooldown': 5},
            'ba_notifications': {'user_rate': (8, 300), 'guild_rate': (20, 300), 'cooldown': 20},
            'ba_check_notifications': {'user_rate': (8, 60), 'guild_rate': (30, 60), 'cooldown': 8},
            'ba_export': {'user_rate': (5, 600), 'guild_rate': (15, 600), 'cooldown': 60},
            'debug_shop_stock': {'user_rate': (8, 60), 'guild_rate': (20, 60), 'cooldown': 8},
            
            # === SISTEMA DE PRUEBAS ===
            'rate_limit_test': {'user_rate': (5, 60), 'guild_rate': (15, 60), 'cooldown': 3},
            
            # === CONFIGURACIÓN POR DEFECTO ===
            'default': {'user_rate': (15, 60), 'guild_rate': (60, 60), 'cooldown': 3}
        }

    async def check_and_record(self, interaction: discord.Interaction, command_name: str) -> bool:
        """
        Verificar rate limiting y registrar uso si es permitido
        Retorna True si el comando debe continuar, False si debe ser bloqueado
        """
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        user_id = str(interaction.user.id)
        
        try:
            async with self.lock:
                now = datetime.now()
                config = self.command_limits.get(command_name, self.command_limits['default'])
                
                # Limpiar timestamps antiguos
                self._cleanup_old_timestamps(guild_id, user_id, command_name, now, config)
                
                # Verificar cooldown
                user_queue = self.user_commands[guild_id][user_id][command_name]
                if user_queue:
                    time_since_last = (now - user_queue[-1]).total_seconds()
                    if time_since_last < config['cooldown']:
                        retry_after = config['cooldown'] - time_since_last
                        await self._send_rate_limit_message(interaction, "cooldown", int(retry_after))
                        return False
                
                # Verificar límite por usuario
                user_rate_limit, user_time_window = config['user_rate']
                if len(user_queue) >= user_rate_limit:
                    oldest = user_queue[0]
                    if now < oldest + timedelta(seconds=user_time_window):
                        retry_after = (oldest + timedelta(seconds=user_time_window) - now).total_seconds()
                        await self._send_rate_limit_message(interaction, "user_limit", int(retry_after))
                        return False
                
                # Verificar límite por servidor
                guild_queue = self.guild_commands[guild_id][command_name]
                guild_rate_limit, guild_time_window = config['guild_rate']
                if len(guild_queue) >= guild_rate_limit:
                    oldest = guild_queue[0]
                    if now < oldest + timedelta(seconds=guild_time_window):
                        retry_after = (oldest + timedelta(seconds=guild_time_window) - now).total_seconds()
                        await self._send_rate_limit_message(interaction, "guild_limit", int(retry_after))
                        return False
                
                # Registrar uso
                user_queue.append(now)
                guild_queue.append(now)
                return True
                
        except Exception as e:
            logger.error(f"Error en rate limiting para {command_name}: {e}")
            return True  # En caso de error, permitir el comando

    def _cleanup_old_timestamps(self, guild_id: str, user_id: str, command_name: str, now: datetime, config: dict):
        """Limpiar timestamps antiguos"""
        user_queue = self.user_commands[guild_id][user_id][command_name]
        guild_queue = self.guild_commands[guild_id][command_name]
        
        user_cutoff = now - timedelta(seconds=config['user_rate'][1])
        guild_cutoff = now - timedelta(seconds=config['guild_rate'][1])
        
        while user_queue and user_queue[0] < user_cutoff:
            user_queue.popleft()
        while guild_queue and guild_queue[0] < guild_cutoff:
            guild_queue.popleft()

    async def _send_rate_limit_message(self, interaction: discord.Interaction, reason: str, retry_after: int):
        """Enviar mensaje de rate limiting"""
        try:
            embed = discord.Embed(
                title="⏳ Límite de Uso",
                description=f"Espera **{retry_after}** segundos antes de usar este comando nuevamente.",
                color=0xff6b6b
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            pass

# Instancia global
rate_limiter = RateLimiter()

# Decorador que NO modifica la función
def rate_limit(command_name: str):
    """Decorador que NO interfiere con el registro del comando"""
    def decorator(func):
        # Agregar un atributo a la función para identificarla
        func._rate_limit_command_name = command_name
        func._rate_limit_enabled = True
        
        # Devolver la función original sin modificar
        return func
    return decorator

# Funciones de compatibilidad
async def get_rate_limit_stats(guild_id: str, user_id: str) -> Dict:
    return {}

async def clear_user_limits(guild_id: str, user_id: str, command_name: Optional[str] = None):
    pass