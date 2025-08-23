"""
Database configuration and connection management
"""

import aiosqlite
import sqlite3
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import get_database_url, settings
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    get_database_url().replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.DEBUG,
    future=True,
    connect_args={"check_same_thread": False}
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI routes
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class DatabaseManager:
    """
    Direct database access manager for shared database
    Compatible with bot's existing database structure
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_URL
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> aiosqlite.Connection:
        """Establish database connection"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute SELECT query and return results"""
        conn = await self.connect()
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE command and return affected rows"""
        conn = await self.connect()
        cursor = await conn.execute(command, params)
        await conn.commit()
        return cursor.rowcount
    
    async def execute_many(self, command: str, params_list: list) -> int:
        """Execute command with multiple parameter sets"""
        conn = await self.connect()
        cursor = await conn.executemany(command, params_list)
        await conn.commit()
        return cursor.rowcount

    async def get_table_info(self, table_name: str) -> list:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return await self.execute_query(query)
    
    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = await self.execute_query(query, (table_name,))
        return len(result) > 0

    async def init_admin_tables(self):
        """Initialize admin panel specific tables"""
        try:
            # Read and execute admin panel tables SQL
            import os
            sql_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "..", "..", "create_admin_panel_tables.sql"
            )
            
            if os.path.exists(sql_file):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                conn = await self.connect()
                await conn.executescript(sql_content)
                await conn.commit()
                logger.info("✅ Admin panel tables initialized successfully")
            else:
                logger.warning(f"⚠️ Admin tables SQL file not found: {sql_file}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing admin tables: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize database with admin tables"""
    try:
        await db_manager.init_admin_tables()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def close_database():
    """Close database connections"""
    try:
        await db_manager.disconnect()
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")