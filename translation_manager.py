#!/usr/bin/env python3
"""
Sistema de Traducciones para Bot SCUM
Maneja múltiples idiomas con archivos JSON
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TranslationManager:
    def __init__(self):
        self.translations: Dict[str, Dict] = {}
        self.default_language = 'es'
        self.supported_languages = ['es', 'en']
        self.translations_path = Path(__file__).parent / 'translations'
        
        # Cargar traducciones al inicializar
        self.load_all_translations()
    
    def load_all_translations(self):
        """Cargar todas las traducciones desde archivos JSON"""
        try:
            if not self.translations_path.exists():
                logger.warning(f"Carpeta de traducciones no encontrada: {self.translations_path}")
                return
            
            for lang in self.supported_languages:
                translation_file = self.translations_path / f"{lang}.json"
                
                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                    logger.info(f"✅ Traducciones cargadas para idioma: {lang}")
                else:
                    logger.warning(f"❌ Archivo de traducción no encontrado: {translation_file}")
            
            logger.info(f"🌍 Sistema de traducciones iniciado: {len(self.translations)} idiomas")
            
        except Exception as e:
            logger.error(f"Error cargando traducciones: {e}")
            # Crear traducciones básicas de emergencia
            self._create_fallback_translations()
    
    def _create_fallback_translations(self):
        """Crear traducciones básicas en caso de error"""
        self.translations = {
            'es': {
                'common': {
                    'error': 'Error',
                    'success': 'Éxito',
                    'loading': 'Cargando...'
                }
            },
            'en': {
                'common': {
                    'error': 'Error', 
                    'success': 'Success',
                    'loading': 'Loading...'
                }
            }
        }
        logger.warning("Usando traducciones de emergencia básicas")
    
    def get_text(self, key_path: str, language: str = None, **kwargs) -> str:
        """
        Obtener texto traducido
        
        Args:
            key_path: Ruta de la clave (ej: "welcome.title", "banking.transfer_money")
            language: Idioma (si no se especifica, usa el predeterminado)
            **kwargs: Variables para formatear el texto
            
        Returns:
            Texto traducido y formateado
        """
        if language is None:
            language = self.default_language
        
        # Validar idioma
        if language not in self.supported_languages:
            language = self.default_language
        
        try:
            # Dividir la ruta de la clave
            keys = key_path.split('.')
            
            # Buscar en el idioma solicitado
            text = self._get_nested_value(self.translations.get(language, {}), keys)
            
            # Si no se encuentra, intentar con idioma predeterminado
            if text is None and language != self.default_language:
                text = self._get_nested_value(self.translations.get(self.default_language, {}), keys)
            
            # Si aún no se encuentra, devolver la clave
            if text is None:
                logger.warning(f"Traducción no encontrada: {key_path} (idioma: {language})")
                return key_path
            
            # Formatear con variables si las hay
            if kwargs:
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error formateando traducción '{key_path}': {e}")
                    return text
            
            return text
            
        except Exception as e:
            logger.error(f"Error obteniendo traducción '{key_path}': {e}")
            return key_path
    
    def _get_nested_value(self, data: Dict, keys: list) -> Optional[str]:
        """Obtener valor anidado de un diccionario usando lista de claves"""
        try:
            for key in keys:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    return None
            return data if isinstance(data, str) else None
        except:
            return None
    
    def get_language_options(self) -> list:
        """Obtener lista de opciones de idioma para selectores"""
        options = []
        
        language_info = {
            'es': {'name': 'Español', 'emoji': '🇪🇸', 'flag': 'ES'},
            'en': {'name': 'English', 'emoji': '🇺🇸', 'flag': 'EN'}
        }
        
        for lang in self.supported_languages:
            if lang in self.translations:
                info = language_info.get(lang, {'name': lang.upper(), 'emoji': '🌐', 'flag': lang.upper()})
                options.append({
                    'value': lang,
                    'label': f"{info['emoji']} {info['name']}",
                    'description': f"Switch to {info['name']}",
                    'emoji': info['emoji']
                })
        
        return options
    
    def reload_translations(self):
        """Recargar traducciones desde archivos (útil para actualizaciones en vivo)"""
        logger.info("🔄 Recargando traducciones...")
        self.translations.clear()
        self.load_all_translations()
    
    def get_supported_languages(self) -> list:
        """Obtener lista de idiomas soportados"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language: str) -> bool:
        """Verificar si un idioma está soportado"""
        return language in self.supported_languages and language in self.translations
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del sistema de traducciones"""
        stats = {
            'languages_loaded': len(self.translations),
            'supported_languages': self.supported_languages,
            'default_language': self.default_language
        }
        
        # Contar claves por idioma
        for lang, translations in self.translations.items():
            stats[f'{lang}_keys'] = self._count_nested_keys(translations)
        
        return stats
    
    def _count_nested_keys(self, data: Dict, count: int = 0) -> int:
        """Contar claves recursivamente en diccionario anidado"""
        for value in data.values():
            if isinstance(value, dict):
                count = self._count_nested_keys(value, count)
            else:
                count += 1
        return count

# Instancia global del manager de traducciones
translation_manager = TranslationManager()

# Función de conveniencia para uso rápido
def t(key_path: str, language: str = None, **kwargs) -> str:
    """
    Función rápida para obtener traducciones
    
    Uso:
        t("welcome.title")  # Usa idioma predeterminado
        t("welcome.title", "en")  # Inglés específico
        t("welcome.welcome_desc", name="Juan")  # Con variables
    """
    return translation_manager.get_text(key_path, language, **kwargs)

# Función para obtener idioma de usuario desde la base de datos
async def get_user_language(user_id: int) -> str:
    """
    Obtener idioma preferido del usuario desde la base de datos
    """
    try:
        from taxi_database import taxi_db
        return await taxi_db.get_user_language(user_id)
        
    except Exception as e:
        logger.warning(f"Error obteniendo idioma de usuario {user_id}: {e}")
        return 'es'

# Función para obtener idioma por Discord ID
async def get_user_language_by_discord_id(discord_id: str, guild_id: str = None) -> str:
    """
    Obtener idioma preferido del usuario por Discord ID
    """
    try:
        from taxi_database import taxi_db
        return await taxi_db.get_user_language_by_discord_id(discord_id, guild_id)
        
    except Exception as e:
        logger.warning(f"Error obteniendo idioma de usuario Discord {discord_id}: {e}")
        return 'es'

# Función para establecer idioma de usuario
async def set_user_language(user_id: int, language: str) -> bool:
    """
    Establecer idioma preferido del usuario en la base de datos
    """
    try:
        if not translation_manager.is_language_supported(language):
            return False
        
        from taxi_database import taxi_db
        return await taxi_db.update_user_language(user_id, language)
        
    except Exception as e:
        logger.error(f"Error estableciendo idioma de usuario {user_id}: {e}")
        return False

if __name__ == "__main__":
    # Test básico
    tm = TranslationManager()
    
    print("=== TEST DEL SISTEMA DE TRADUCCIONES ===")
    print(f"Estadísticas: {tm.get_stats()}")
    print()
    
    # Test de traducciones
    print("Español:", tm.get_text("welcome.title", "es"))
    print("Inglés:", tm.get_text("welcome.title", "en"))
    print("Con variable:", tm.get_text("welcome.welcome_desc", "es", name="TestUser"))
    print()
    
    # Test función rápida
    print("Función t():", t("banking.transfer_money", "en"))
    print("Opciones de idioma:", tm.get_language_options())