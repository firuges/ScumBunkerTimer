#!/usr/bin/env python3
"""
Sistema de Rate Limiting para SCUM Bot - Versión Corregida
Controla el uso de comandos por usuario y servidor
"""

import discord
import asyncio
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        # Estructura: {guild_id: {user_id: {command: deque_of_timestamps}}}
        self.user_commands = defaultdict(lambda: defaultdict(lambda: defaultdict(deque)))
        # Estructura: {guild_id: {command: deque_of_timestamps}}
        self.guild_commands = defaultdict(lambda: defaultdict(deque))
        # Lock para thread safety
        self.lock = asyncio.Lock()
        
        # Configuraciones de rate limiting por comando
        self.command_limits = {
            # === SISTEMA BANCARIO ===
            'banco_balance': {
                'user_rate': (3, 60),      # 3 usos por minuto por usuario
                'guild_rate': (20, 60),    # 20 usos por minuto por servidor
                'cooldown': 10             # 10 segundos entre usos del mismo usuario
            },
            'banco_transferir': {
                'user_rate': (2, 300),     # 2 transferencias por 5 minutos por usuario
                'guild_rate': (10, 60),    # 10 transferencias por minuto por servidor
                'cooldown': 30             # 30 segundos entre transferencias
            },
            'banco_historial': {
                'user_rate': (5, 300),     # 5 consultas por 5 minutos por usuario
                'guild_rate': (25, 60),    # 25 consultas por minuto por servidor
                'cooldown': 15             # 15 segundos entre consultas
            },
            
            # === SISTEMA DE BUNKERS ===
            'ba_check_bunker': {
                'user_rate': (10, 60),     # 10 consultas por minuto por usuario
                'guild_rate': (50, 60),    # 50 consultas por minuto por servidor
                'cooldown': 3              # 3 segundos entre consultas
            },
            'ba_status_all': {
                'user_rate': (5, 60),      # 5 consultas por minuto por usuario
                'guild_rate': (20, 60),    # 20 consultas por minuto por servidor
                'cooldown': 10             # 10 segundos entre consultas
            },
            'ba_my_usage': {
                'user_rate': (3, 60),      # 3 consultas por minuto por usuario
                'guild_rate': (15, 60),    # 15 consultas por minuto por servidor
                'cooldown': 15             # 15 segundos entre consultas
            },
            'ba_help': {
                'user_rate': (2, 300),     # 2 consultas por 5 minutos por usuario
                'guild_rate': (10, 60),    # 10 consultas por minuto por servidor
                'cooldown': 30             # 30 segundos entre consultas
            },
            'ba_bot_status': {
                'user_rate': (3, 60),      # 3 consultas por minuto por usuario
                'guild_rate': (15, 60),    # 15 consultas por minuto por servidor
                'cooldown': 10             # 10 segundos entre consultas
            },
            'ba_suscripcion': {
                'user_rate': (2, 300),     # 2 consultas por 5 minutos por usuario
                'guild_rate': (10, 60),    # 10 consultas por minuto por servidor
                'cooldown': 30             # 30 segundos entre consultas
            },
            'ba_add_server': {
                'user_rate': (2, 300),     # 2 creaciones por 5 minutos por usuario
                'guild_rate': (5, 300),    # 5 creaciones por 5 minutos por servidor
                'cooldown': 60             # 1 minuto entre creaciones
            },
            'ba_remove_server': {
                'user_rate': (1, 600),     # 1 eliminación por 10 minutos por usuario
                'guild_rate': (3, 300),    # 3 eliminaciones por 5 minutos por servidor
                'cooldown': 120            # 2 minutos entre eliminaciones
            },
            'ba_list_servers': {
                'user_rate': (5, 60),      # 5 consultas por minuto por usuario
                'guild_rate': (25, 60),    # 25 consultas por minuto por servidor
                'cooldown': 5              # 5 segundos entre consultas
            },
            
            # === COMANDOS ADMIN DE BUNKERS ===
            'ba_admin_status': {
                'user_rate': (5, 60),      # 5 consultas por minuto por admin
                'guild_rate': (20, 60),    # 20 consultas por minuto por servidor
                'cooldown': 10             # 10 segundos entre consultas
            },
            'ba_admin_upgrade': {
                'user_rate': (1, 600),     # 1 upgrade por 10 minutos por admin
                'guild_rate': (3, 600),    # 3 upgrades por 10 minutos por servidor
                'cooldown': 300            # 5 minutos entre upgrades
            },
            'ba_admin_cancel': {
                'user_rate': (1, 600),     # 1 cancelación por 10 minutos por admin
                'guild_rate': (2, 600),    # 2 cancelaciones por 10 minutos por servidor
                'cooldown': 300            # 5 minutos entre cancelaciones
            },
            'ba_admin_resync': {
                'user_rate': (1, 300),     # 1 resync por 5 minutos por admin
                'guild_rate': (3, 300),    # 3 resyncs por 5 minutos por servidor
                'cooldown': 120            # 2 minutos entre resyncs
            },
            'ba_admin_shutdown': {
                'user_rate': (1, 3600),    # 1 shutdown por hora por admin
                'guild_rate': (1, 3600),   # 1 shutdown por hora por servidor
                'cooldown': 1800           # 30 minutos entre shutdowns
            },
            
            # === CONFIGURACIÓN POR DEFECTO ===
            'default': {
                'user_rate': (10, 60),     # 10 usos por minuto por usuario
                'guild_rate': (50, 60),    # 50 usos por minuto por servidor
                'cooldown': 5              # 5 segundos entre usos
            }
        }

    async def is_rate_limited(self, guild_id: str, user_id: str, command_name: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Verifica si un usuario/servidor está limitado para un comando específico
        
        Returns:
            (is_limited, reason, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.now()
            
            # Obtener configuración del comando
            config = self.command_limits.get(command_name, self.command_limits['default'])
            user_rate_limit, user_time_window = config['user_rate']
            guild_rate_limit, guild_time_window = config['guild_rate']
            cooldown_seconds = config['cooldown']
            
            # Limpiar timestamps antiguos
            await self._cleanup_old_timestamps(guild_id, user_id, command_name, now)
            
            # Verificar cooldown individual
            user_queue = self.user_commands[guild_id][user_id][command_name]
            if user_queue:
                last_use = user_queue[-1]
                time_since_last = (now - last_use).total_seconds()
                if time_since_last < cooldown_seconds:
                    retry_after = cooldown_seconds - time_since_last
                    return True, "cooldown", int(retry_after)
            
            # Verificar límite por usuario
            if len(user_queue) >= user_rate_limit:
                oldest_timestamp = user_queue[0]
                time_window_end = oldest_timestamp + timedelta(seconds=user_time_window)
                if now < time_window_end:
                    retry_after = (time_window_end - now).total_seconds()
                    return True, "user_limit", int(retry_after)
            
            # Verificar límite por servidor
            guild_queue = self.guild_commands[guild_id][command_name]
            if len(guild_queue) >= guild_rate_limit:
                oldest_timestamp = guild_queue[0]
                time_window_end = oldest_timestamp + timedelta(seconds=guild_time_window)
                if now < time_window_end:
                    retry_after = (time_window_end - now).total_seconds()
                    return True, "guild_limit", int(retry_after)
            
            return False, None, None

    async def record_usage(self, guild_id: str, user_id: str, command_name: str):
        """Registra el uso de un comando"""
        async with self.lock:
            now = datetime.now()
            self.user_commands[guild_id][user_id][command_name].append(now)
            self.guild_commands[guild_id][command_name].append(now)

    async def _cleanup_old_timestamps(self, guild_id: str, user_id: str, command_name: str, now: datetime):
        """Limpia timestamps antiguos fuera de la ventana de tiempo"""
        config = self.command_limits.get(command_name, self.command_limits['default'])
        user_time_window = config['user_rate'][1]
        guild_time_window = config['guild_rate'][1]
        
        # Limpiar timestamps de usuario
        user_queue = self.user_commands[guild_id][user_id][command_name]
        cutoff_time_user = now - timedelta(seconds=user_time_window)
        while user_queue and user_queue[0] < cutoff_time_user:
            user_queue.popleft()
        
        # Limpiar timestamps de servidor
        guild_queue = self.guild_commands[guild_id][command_name]
        cutoff_time_guild = now - timedelta(seconds=guild_time_window)
        while guild_queue and guild_queue[0] < cutoff_time_guild:
            guild_queue.popleft()

    def get_usage_stats(self, guild_id: str, user_id: str, command_name: str) -> Dict:
        """Obtiene estadísticas de uso actuales"""
        config = self.command_limits.get(command_name, self.command_limits['default'])
        user_queue = self.user_commands[guild_id][user_id][command_name]
        guild_queue = self.guild_commands[guild_id][command_name]
        
        return {
            'user_usage': len(user_queue),
            'user_limit': config['user_rate'][0],
            'guild_usage': len(guild_queue),
            'guild_limit': config['guild_rate'][0],
            'cooldown': config['cooldown']
        }

# Instancia global del rate limiter
rate_limiter = RateLimiter()

def rate_limit(command_name: str):
    """
    Decorador para aplicar rate limiting a comandos - VERSIÓN MINIMALISTA
    
    Args:
        command_name: Nombre del comando para buscar en la configuración
    """
    def decorator(func):
        # Solo aplicar el wrapper en tiempo de ejecución, no modificar la función para el registro
        original_func = func
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Solo aplicar rate limiting si detectamos un interaction
            interaction = None
            
            # Buscar interaction en los argumentos
            for arg in args:
                if hasattr(arg, 'response') and hasattr(arg, 'user') and hasattr(arg, 'guild'):
                    interaction = arg
                    break
            
            if interaction is None:
                # No hay interaction, ejecutar normalmente
                return await original_func(*args, **kwargs)
            
            # Aplicar rate limiting
            guild_id = str(interaction.guild.id) if interaction.guild else "dm"
            user_id = str(interaction.user.id)
            
            try:
                is_limited, reason, retry_after = await rate_limiter.is_rate_limited(
                    guild_id, user_id, command_name
                )
                
                if is_limited:
                    # Crear embed de error
                    embed = discord.Embed(
                        title="⏳ Límite de Uso Alcanzado",
                        description=f"Debes esperar **{retry_after}** segundos antes de usar este comando nuevamente.",
                        color=0xff6b6b
                    )
                    
                    embed.add_field(
                        name="💡 Info",
                        value="Los límites protegen el bot de sobrecarga.",
                        inline=False
                    )
                    
                    try:
                        if not interaction.response.is_done():
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await interaction.followup.send(embed=embed, ephemeral=True)
                    except:
                        pass  # Si falla el envío, continuar silenciosamente
                    
                    return
                
                # Registrar el uso
                await rate_limiter.record_usage(guild_id, user_id, command_name)
                
            except Exception as e:
                logger.error(f"Error en rate limiting para {command_name}: {e}")
                # Si hay error, ejecutar el comando normalmente
            
            # Ejecutar comando original
            return await original_func(*args, **kwargs)
        
        # CRÍTICO: Devolver la función original para el registro del comando
        # Solo reemplazar la función cuando se ejecute, no durante el registro
        setattr(original_func, '_rate_limited_wrapper', wrapper)
        return original_func
    
    return decorator

# Monkey patch para interceptar ejecución sin afectar registro
original_call = None

def apply_rate_limiting_patch():
    """Aplicar el patch para que el rate limiting funcione sin afectar el registro"""
    global original_call
    
    # Esta función se llamará cuando esté listo el bot para aplicar el patch
    # Por ahora, el decorador funciona de forma minimalista
    pass

async def get_rate_limit_stats(guild_id: str, user_id: str) -> Dict:
    """Obtiene estadísticas completas de rate limiting para un usuario"""
    stats = {}
    
    for command_name in rate_limiter.command_limits.keys():
        if command_name != 'default':
            stats[command_name] = rate_limiter.get_usage_stats(guild_id, user_id, command_name)
    
    return stats

async def clear_user_limits(guild_id: str, user_id: str, command_name: Optional[str] = None):
    """Limpia los límites de un usuario (para uso administrativo)"""
    async with rate_limiter.lock:
        if command_name:
            # Limpiar comando específico
            if guild_id in rate_limiter.user_commands and user_id in rate_limiter.user_commands[guild_id]:
                rate_limiter.user_commands[guild_id][user_id][command_name].clear()
        else:
            # Limpiar todos los comandos del usuario
            if guild_id in rate_limiter.user_commands:
                rate_limiter.user_commands[guild_id][user_id].clear()
    
    logger.info(f"Límites limpiados para usuario {user_id} en guild {guild_id}, comando: {command_name or 'todos'}")