"""
Sistema de Pool de Conexiones para SQLite
Mejora la gestión de conexiones de base de datos para mayor escalabilidad
"""

import aiosqlite
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncContextManager
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import threading
from queue import Queue, Empty
import weakref

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Wrapper para conexión de base de datos con metadata"""
    
    def __init__(self, connection: aiosqlite.Connection, db_path: str):
        self.connection = connection
        self.db_path = db_path
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.in_use = False
        self.use_count = 0

    async def execute(self, query: str, parameters: tuple = ()):
        """Ejecutar query manteniendo estadísticas"""
        self.last_used = datetime.now()
        self.use_count += 1
        return await self.connection.execute(query, parameters)
    
    async def executemany(self, query: str, parameters):
        """Ejecutar query múltiple manteniendo estadísticas"""
        self.last_used = datetime.now()
        self.use_count += 1
        return await self.connection.executemany(query, parameters)
    
    async def commit(self):
        """Commit con estadísticas"""
        return await self.connection.commit()
    
    async def close(self):
        """Cerrar conexión"""
        if self.connection:
            await self.connection.close()

class DatabasePool:
    """Pool de conexiones para SQLite con gestión automática"""
    
    def __init__(self, db_path: str, max_connections: int = 10, max_idle_time: int = 300):
        self.db_path = db_path
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        
        # Pool de conexiones disponibles
        self.available_connections: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        # Conexiones activas (en uso)
        self.active_connections: Dict[int, DatabaseConnection] = {}
        # Lock para operaciones thread-safe
        self.lock = asyncio.Lock()
        
        # Estadísticas
        self.stats = {
            'total_created': 0,
            'total_requests': 0,
            'active_count': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
        # Tarea de limpieza automática
        self.cleanup_task: Optional[asyncio.Task] = None
        self.closed = False

    async def initialize(self):
        """Inicializar el pool con conexiones base"""
        try:
            # Crear conexiones iniciales (25% del máximo)
            initial_connections = max(1, self.max_connections // 4)
            
            for _ in range(initial_connections):
                conn = await self._create_connection()
                if conn:
                    await self.available_connections.put(conn)
            
            # Iniciar tarea de limpieza
            if not self.cleanup_task:
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info(f"Pool de DB inicializado: {initial_connections} conexiones para {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error inicializando pool de DB: {e}")

    async def _create_connection(self) -> Optional[DatabaseConnection]:
        """Crear nueva conexión a la base de datos"""
        try:
            sqlite_conn = await aiosqlite.connect(
                self.db_path,
                timeout=30.0,
                isolation_level=None  # Autocommit mode for better concurrency
            )
            
            # Optimizaciones para concurrencia en SQLite
            await sqlite_conn.execute("PRAGMA journal_mode=WAL")
            await sqlite_conn.execute("PRAGMA synchronous=NORMAL")
            await sqlite_conn.execute("PRAGMA cache_size=10000")
            await sqlite_conn.execute("PRAGMA temp_store=MEMORY")
            await sqlite_conn.execute("PRAGMA busy_timeout=30000")
            
            db_conn = DatabaseConnection(sqlite_conn, self.db_path)
            self.stats['total_created'] += 1
            
            return db_conn
            
        except Exception as e:
            logger.error(f"Error creando conexión DB: {e}")
            return None

    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[DatabaseConnection]:
        """Obtener conexión del pool (context manager)"""
        connection = None
        
        try:
            self.stats['total_requests'] += 1
            
            async with self.lock:
                # Intentar obtener conexión del pool
                try:
                    connection = await asyncio.wait_for(
                        self.available_connections.get(),
                        timeout=2.0
                    )
                    self.stats['pool_hits'] += 1
                except asyncio.TimeoutError:
                    # Pool vacío, crear nueva conexión si no hemos alcanzado el máximo
                    if len(self.active_connections) < self.max_connections:
                        connection = await self._create_connection()
                        self.stats['pool_misses'] += 1
                    else:
                        # Esperar más tiempo por una conexión
                        connection = await self.available_connections.get()
                        self.stats['pool_hits'] += 1
                
                if not connection:
                    raise Exception("No se pudo obtener conexión de la base de datos")
                
                # Marcar como en uso
                connection.in_use = True
                conn_id = id(connection)
                self.active_connections[conn_id] = connection
                self.stats['active_count'] = len(self.active_connections)
            
            yield connection
            
        except Exception as e:
            logger.error(f"Error en get_connection: {e}")
            raise
        
        finally:
            # Devolver conexión al pool
            if connection:
                async with self.lock:
                    connection.in_use = False
                    conn_id = id(connection)
                    
                    # Remover de activas
                    if conn_id in self.active_connections:
                        del self.active_connections[conn_id]
                    
                    # Verificar si la conexión sigue siendo válida
                    if await self._is_connection_valid(connection):
                        try:
                            await self.available_connections.put(connection)
                        except asyncio.QueueFull:
                            # Pool lleno, cerrar conexión
                            await connection.close()
                    else:
                        await connection.close()
                    
                    self.stats['active_count'] = len(self.active_connections)

    async def _is_connection_valid(self, connection: DatabaseConnection) -> bool:
        """Verificar si una conexión sigue siendo válida"""
        try:
            # Verificar si la conexión no es muy antigua
            age = datetime.now() - connection.created_at
            if age.total_seconds() > self.max_idle_time * 2:  # 2x el tiempo de idle
                return False
            
            # Test simple de la conexión
            cursor = await connection.connection.execute("SELECT 1")
            await cursor.fetchone()
            await cursor.close()
            return True
            
        except Exception:
            return False

    async def _cleanup_loop(self):
        """Loop de limpieza para conexiones inactivas"""
        while not self.closed:
            try:
                await asyncio.sleep(60)  # Limpiar cada minuto
                await self._cleanup_idle_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_idle_connections(self):
        """Limpiar conexiones inactivas del pool"""
        async with self.lock:
            current_size = self.available_connections.qsize()
            min_connections = max(1, self.max_connections // 4)
            
            if current_size <= min_connections:
                return
            
            connections_to_close = []
            connections_to_keep = []
            cutoff_time = datetime.now() - timedelta(seconds=self.max_idle_time)
            
            # Revisar todas las conexiones disponibles
            while not self.available_connections.empty():
                try:
                    conn = self.available_connections.get_nowait()
                    
                    if conn.last_used < cutoff_time and len(connections_to_keep) >= min_connections:
                        connections_to_close.append(conn)
                    else:
                        connections_to_keep.append(conn)
                        
                except asyncio.QueueEmpty:
                    break
            
            # Devolver conexiones que mantenemos
            for conn in connections_to_keep:
                try:
                    await self.available_connections.put(conn)
                except asyncio.QueueFull:
                    connections_to_close.append(conn)
            
            # Cerrar conexiones inactivas
            for conn in connections_to_close:
                try:
                    await conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión inactiva: {e}")
            
            if connections_to_close:
                logger.info(f"Limpieza DB pool: cerradas {len(connections_to_close)} conexiones inactivas")

    async def close(self):
        """Cerrar el pool y todas las conexiones"""
        self.closed = True
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar conexiones activas
        for conn in list(self.active_connections.values()):
            try:
                await conn.close()
            except Exception:
                pass
        
        # Cerrar conexiones disponibles
        while not self.available_connections.empty():
            try:
                conn = await self.available_connections.get()
                await conn.close()
            except Exception:
                pass
        
        logger.info(f"Pool de DB cerrado para {self.db_path}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del pool"""
        return {
            **self.stats,
            'available_connections': self.available_connections.qsize(),
            'max_connections': self.max_connections,
            'db_path': self.db_path,
            'pool_utilization': len(self.active_connections) / self.max_connections,
            'efficiency': self.stats['pool_hits'] / max(1, self.stats['total_requests'])
        }

class DatabasePoolManager:
    """Gestor global de pools de base de datos"""
    
    def __init__(self):
        self.pools: Dict[str, DatabasePool] = {}
        self.lock = asyncio.Lock()

    async def get_pool(self, db_path: str, max_connections: int = 10) -> DatabasePool:
        """Obtener o crear pool para una base de datos"""
        async with self.lock:
            if db_path not in self.pools:
                pool = DatabasePool(db_path, max_connections)
                await pool.initialize()
                self.pools[db_path] = pool
                logger.info(f"Nuevo pool creado para {db_path}")
            
            return self.pools[db_path]

    async def close_all(self):
        """Cerrar todos los pools"""
        for pool in self.pools.values():
            await pool.close()
        self.pools.clear()

    def get_all_stats(self) -> Dict[str, Dict]:
        """Obtener estadísticas de todos los pools"""
        return {db_path: pool.get_stats() for db_path, pool in self.pools.items()}

# Instancia global del gestor de pools
pool_manager = DatabasePoolManager()