"""
Configuración central del panel admin
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SCUM Bot Admin Panel"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "../../scum_main.db"  # Shared with bot
    
    # Discord OAuth2
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    DISCORD_BOT_TOKEN: str = ""
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Bot Integration
    BOT_API_URL: Optional[str] = None  # URL del bot si tiene API HTTP
    BOT_WEBHOOK_SECRET: str = "bot-webhook-secret"
    
    # Development
    DEBUG: bool = True
    RELOAD: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Helper functions
def get_database_url() -> str:
    """Get database URL with proper path resolution"""
    if os.path.isabs(settings.DATABASE_URL):
        return f"sqlite:///{settings.DATABASE_URL}"
    
    # Relative path - resolve based on backend directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, settings.DATABASE_URL)
    return f"sqlite:///{db_path}"

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.DEBUG

def get_discord_oauth_url() -> str:
    """Generate Discord OAuth2 URL"""
    base_url = "https://discord.com/api/oauth2/authorize"
    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
    }
    
    from urllib.parse import urlencode
    return f"{base_url}?{urlencode(params)}"