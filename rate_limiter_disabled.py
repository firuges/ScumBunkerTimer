#!/usr/bin/env python3
"""
Version deshabilitada temporalmente del rate limiter para debugging
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

# Decorador deshabilitado temporalmente para debugging
def rate_limit(command_name: str):
    """
    Decorador DESHABILITADO para debugging - solo pasa through sin rate limiting
    
    Args:
        command_name: Nombre del comando (ignorado en esta versión)
    """
    def decorator(func):
        # Devolver la función original sin modificar
        logger.info(f"Rate limiting DESHABILITADO para comando: {command_name}")
        return func
    return decorator

# Funciones dummy para compatibilidad
async def get_rate_limit_stats(guild_id: str, user_id: str) -> Dict:
    """Función dummy para compatibilidad"""
    return {}

async def clear_user_limits(guild_id: str, user_id: str, command_name: Optional[str] = None):
    """Función dummy para compatibilidad"""
    logger.info(f"Clear limits DESHABILITADO para usuario {user_id}, comando: {command_name}")
    pass