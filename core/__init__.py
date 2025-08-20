"""
Módulo core del sistema SCUM Bot
Contiene funcionalidades centralizadas y compartidas por todos los módulos.
"""

from .user_manager import UserManager, user_manager

__all__ = ['UserManager', 'user_manager']