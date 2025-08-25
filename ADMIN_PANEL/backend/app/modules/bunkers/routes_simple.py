"""
Bunkers module routes - Simplified (No Auth)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

# Database path - main database from root directory
DB_PATH = "../../scum_main.db"

# Simplified models for no-auth version
class ServerInfo(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    max_bunkers: int
    is_active: bool
    total_bunkers: int
    active_bunkers: int

class SectorInfo(BaseModel):
    id: int
    sector: str
    name: str
    coordinates: Optional[str]
    description: Optional[str]
    default_duration_hours: int
    notification_enabled: bool
    is_active: bool
    total_registrations: int
    active_registrations: int

class BunkerRegistration(BaseModel):
    id: int
    sector: str
    name: str
    server_name: str
    registered_time: str
    expiry_time: str
    registered_by: str
    last_updated: str
    status: str
    time_remaining: Optional[str]
    expired_minutes_ago: Optional[int]

class CreateServerRequest(BaseModel):
    guild_id: str
    name: str
    display_name: str
    description: Optional[str] = None
    max_bunkers: int = 100

class CreateSectorRequest(BaseModel):
    guild_id: str
    sector: str
    name: str
    coordinates: Optional[str] = None
    description: Optional[str] = None
    default_duration_hours: int = 24

class RegisterBunkerRequest(BaseModel):
    guild_id: str
    server_name: str
    sector: str
    hours: int
    minutes: int = 0
    registered_by: str

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# SERVERS MANAGEMENT
@router.get("/servers", response_model=List[ServerInfo])
async def get_servers(guild_id: str = Query("DEFAULT_GUILD", description="Guild ID")):
    """Get all servers for a guild"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT s.*, 
                   COUNT(DISTINCT b.id) as total_bunkers,
                   COUNT(DISTINCT CASE WHEN b.expiry_time > datetime('now') THEN b.id END) as active_bunkers
            FROM admin_bunker_servers s
            LEFT JOIN bunkers b ON b.server_name = s.name AND b.discord_guild_id = s.guild_id
            WHERE s.guild_id = ?
            GROUP BY s.id
            ORDER BY s.created_at ASC
        """
        
        cursor.execute(query, (guild_id,))
        servers_data = cursor.fetchall()
        
        servers = []
        for server in servers_data:
            servers.append(ServerInfo(
                id=server['id'],
                name=server['name'],
                display_name=server['display_name'],
                description=server['description'],
                max_bunkers=server['max_bunkers'],
                is_active=bool(server['is_active']),
                total_bunkers=server['total_bunkers'] or 0,
                active_bunkers=server['active_bunkers'] or 0
            ))
        
        return servers

@router.post("/servers", response_model=ServerInfo)
async def create_server(server_data: CreateServerRequest):
    """Create a new server"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if server name already exists
        cursor.execute(
            "SELECT id FROM admin_bunker_servers WHERE guild_id = ? AND name = ?",
            (server_data.guild_id, server_data.name)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Server name already exists")
        
        # Insert new server
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO admin_bunker_servers 
            (guild_id, name, display_name, description, max_bunkers, is_active, created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            server_data.guild_id, server_data.name, server_data.display_name,
            server_data.description, server_data.max_bunkers, now, now, "admin"
        ))
        
        server_id = cursor.lastrowid
        conn.commit()
        
        return ServerInfo(
            id=server_id,
            name=server_data.name,
            display_name=server_data.display_name,
            description=server_data.description,
            max_bunkers=server_data.max_bunkers,
            is_active=True,
            total_bunkers=0,
            active_bunkers=0
        )

@router.delete("/servers/{server_id}")
async def delete_server(server_id: int, guild_id: str = Query("DEFAULT_GUILD")):
    """Delete a server and all its bunkers"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get server name first
        cursor.execute(
            "SELECT name FROM admin_bunker_servers WHERE id = ? AND guild_id = ?",
            (server_id, guild_id)
        )
        server = cursor.fetchone()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        server_name = server['name']
        
        # Delete all bunkers for this server
        cursor.execute(
            "DELETE FROM bunkers WHERE server_name = ? AND discord_guild_id = ?",
            (server_name, guild_id)
        )
        
        # Delete the server
        cursor.execute("DELETE FROM admin_bunker_servers WHERE id = ?", (server_id,))
        
        conn.commit()
        
        return {"message": f"Server {server_name} and all its bunkers deleted successfully"}

# SECTORS MANAGEMENT
@router.get("/sectors", response_model=List[SectorInfo])
async def get_sectors(guild_id: str = Query("DEFAULT_GUILD", description="Guild ID")):
    """Get all bunker sectors for a guild"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT s.*, 
                   COUNT(DISTINCT b.id) as total_registrations,
                   COUNT(DISTINCT CASE WHEN b.expiry_time > datetime('now') THEN b.id END) as active_registrations
            FROM admin_bunker_sectors s
            LEFT JOIN bunkers b ON b.sector = s.sector AND b.discord_guild_id = s.guild_id
            WHERE s.guild_id = ?
            GROUP BY s.id
            ORDER BY s.sector ASC
        """
        
        cursor.execute(query, (guild_id,))
        sectors_data = cursor.fetchall()
        
        sectors = []
        for sector in sectors_data:
            sectors.append(SectorInfo(
                id=sector['id'],
                sector=sector['sector'],
                name=sector['name'],
                coordinates=sector['coordinates'],
                description=sector['description'],
                default_duration_hours=sector['default_duration_hours'],
                notification_enabled=bool(sector['notification_enabled']),
                is_active=bool(sector['is_active']),
                total_registrations=sector['total_registrations'] or 0,
                active_registrations=sector['active_registrations'] or 0
            ))
        
        return sectors

@router.post("/sectors", response_model=SectorInfo)
async def create_sector(sector_data: CreateSectorRequest):
    """Create a new bunker sector"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if sector already exists
        cursor.execute(
            "SELECT id FROM admin_bunker_sectors WHERE guild_id = ? AND sector = ?",
            (sector_data.guild_id, sector_data.sector.upper())
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Sector already exists")
        
        # Insert new sector
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO admin_bunker_sectors 
            (guild_id, sector, name, coordinates, description, default_duration_hours, 
             notification_enabled, is_active, created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?)
        """, (
            sector_data.guild_id, sector_data.sector.upper(), sector_data.name,
            sector_data.coordinates, sector_data.description, sector_data.default_duration_hours,
            now, now, "admin"
        ))
        
        sector_id = cursor.lastrowid
        conn.commit()
        
        return SectorInfo(
            id=sector_id,
            sector=sector_data.sector.upper(),
            name=sector_data.name,
            coordinates=sector_data.coordinates,
            description=sector_data.description,
            default_duration_hours=sector_data.default_duration_hours,
            notification_enabled=True,
            is_active=True,
            total_registrations=0,
            active_registrations=0
        )

@router.delete("/sectors/{sector_id}")
async def delete_sector(sector_id: int, guild_id: str = Query("DEFAULT_GUILD")):
    """Delete a sector and all its bunker registrations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get sector info first
        cursor.execute(
            "SELECT sector FROM admin_bunker_sectors WHERE id = ? AND guild_id = ?",
            (sector_id, guild_id)
        )
        sector = cursor.fetchone()
        if not sector:
            raise HTTPException(status_code=404, detail="Sector not found")
        
        sector_name = sector['sector']
        
        # Delete all bunker registrations for this sector
        cursor.execute(
            "DELETE FROM bunkers WHERE sector = ? AND discord_guild_id = ?",
            (sector_name, guild_id)
        )
        
        # Delete the sector
        cursor.execute("DELETE FROM admin_bunker_sectors WHERE id = ?", (sector_id,))
        
        conn.commit()
        
        return {"message": f"Sector {sector_name} and all its registrations deleted successfully"}

# BUNKER REGISTRATIONS
@router.get("/registrations", response_model=List[BunkerRegistration])
async def get_registrations(
    guild_id: str = Query("DEFAULT_GUILD", description="Guild ID"),
    server_name: Optional[str] = Query(None, description="Filter by server"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return")
):
    """Get bunker registrations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build query
        where_conditions = ["discord_guild_id = ?"]
        params = [guild_id]
        
        if server_name:
            where_conditions.append("server_name = ?")
            params.append(server_name)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM bunkers
            {where_clause}
            ORDER BY 
                CASE WHEN expiry_time > datetime('now') THEN 1 ELSE 2 END,
                expiry_time DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        bunkers_data = cursor.fetchall()
        
        bunkers = []
        for bunker in bunkers_data:
            # Calculate status and time remaining
            now = datetime.now()
            expiry_time = datetime.fromisoformat(bunker['expiry_time']) if bunker['expiry_time'] else None
            
            if not expiry_time:
                status = "unknown"
                time_remaining = None
                expired_minutes_ago = None
            elif expiry_time > now:
                time_diff = expiry_time - now
                if time_diff.total_seconds() <= 1800:  # 30 minutes
                    status = "near_expiry"
                else:
                    status = "active"
                
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_remaining = f"{hours}h {minutes}m"
                expired_minutes_ago = None
            else:
                status = "expired"
                time_remaining = None
                expired_minutes_ago = int((now - expiry_time).total_seconds() / 60)
            
            bunkers.append(BunkerRegistration(
                id=bunker['id'],
                sector=bunker['sector'],
                name=bunker['name'],
                server_name=bunker['server_name'],
                registered_time=bunker['registered_time'],
                expiry_time=bunker['expiry_time'] or "",
                registered_by=bunker['registered_by'] or "",
                last_updated=bunker['last_updated'] or bunker['registered_time'],
                status=status,
                time_remaining=time_remaining,
                expired_minutes_ago=expired_minutes_ago
            ))
        
        return bunkers

@router.post("/registrations/manual")
async def register_bunker_manual(registration: RegisterBunkerRequest):
    """Manually register a bunker"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if sector exists and is active
        cursor.execute(
            "SELECT id FROM admin_bunker_sectors WHERE guild_id = ? AND sector = ? AND is_active = 1",
            (registration.guild_id, registration.sector.upper())
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail=f"Sector {registration.sector} not found or inactive"
            )
        
        # Check if server exists and is active
        cursor.execute(
            "SELECT id FROM admin_bunker_servers WHERE guild_id = ? AND name = ? AND is_active = 1",
            (registration.guild_id, registration.server_name)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Server {registration.server_name} not found or inactive"
            )
        
        now = datetime.now()
        expiry_time = now + timedelta(hours=registration.hours, minutes=registration.minutes)
        
        # Insert or update bunker registration
        cursor.execute("""
            INSERT OR REPLACE INTO bunkers 
            (sector, name, server_name, discord_guild_id, registered_time, expiry_time, 
             registered_by, discord_user_id, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            registration.sector.upper(), registration.sector.upper(), registration.server_name,
            registration.guild_id, now.isoformat(), expiry_time.isoformat(),
            registration.registered_by, "admin", now.isoformat()
        ))
        
        conn.commit()
        
        return {
            "message": f"Bunker {registration.sector} registered successfully",
            "sector": registration.sector.upper(),
            "server": registration.server_name,
            "expiry_time": expiry_time.isoformat(),
            "duration": f"{registration.hours}h {registration.minutes}m"
        }

@router.delete("/registrations/{bunker_id}")
async def cancel_bunker_registration(bunker_id: int, guild_id: str = Query("DEFAULT_GUILD")):
    """Cancel/delete a bunker registration"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if bunker exists and belongs to guild
        cursor.execute(
            "SELECT sector FROM bunkers WHERE id = ? AND discord_guild_id = ?",
            (bunker_id, guild_id)
        )
        bunker = cursor.fetchone()
        if not bunker:
            raise HTTPException(status_code=404, detail="Bunker registration not found")
        
        # Delete the registration
        cursor.execute("DELETE FROM bunkers WHERE id = ?", (bunker_id,))
        conn.commit()
        
        return {"message": f"Bunker registration {bunker['sector']} cancelled successfully"}

# STATISTICS
@router.get("/stats/overview")
async def get_bunkers_overview(guild_id: str = Query("DEFAULT_GUILD")):
    """Get bunkers overview statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get various counts
        stats = {}
        
        # Total servers
        cursor.execute("SELECT COUNT(*) as count FROM admin_bunker_servers WHERE guild_id = ?", (guild_id,))
        stats['total_servers'] = cursor.fetchone()['count']
        
        # Total sectors
        cursor.execute("SELECT COUNT(*) as count FROM admin_bunker_sectors WHERE guild_id = ?", (guild_id,))
        stats['total_sectors'] = cursor.fetchone()['count']
        
        # Total registrations
        cursor.execute("SELECT COUNT(*) as count FROM bunkers WHERE discord_guild_id = ?", (guild_id,))
        stats['total_registrations'] = cursor.fetchone()['count']
        
        # Active registrations
        cursor.execute(
            "SELECT COUNT(*) as count FROM bunkers WHERE discord_guild_id = ? AND expiry_time > datetime('now')",
            (guild_id,)
        )
        stats['active_registrations'] = cursor.fetchone()['count']
        
        # Registrations today
        cursor.execute(
            "SELECT COUNT(*) as count FROM bunkers WHERE discord_guild_id = ? AND DATE(registered_time) = DATE('now')",
            (guild_id,)
        )
        stats['registrations_today'] = cursor.fetchone()['count']
        
        # Most active sector
        cursor.execute("""
            SELECT sector, COUNT(*) as count FROM bunkers 
            WHERE discord_guild_id = ? AND registered_time >= datetime('now', '-7 days')
            GROUP BY sector ORDER BY count DESC LIMIT 1
        """, (guild_id,))
        most_active = cursor.fetchone()
        stats['most_active_sector'] = most_active['sector'] if most_active else None
        
        return {
            "guild_id": guild_id,
            "stats": stats,
            "health": "healthy" if stats['active_registrations'] > 0 else "warning"
        }