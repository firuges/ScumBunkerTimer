"""
Bunkers module routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import json
from datetime import datetime, timedelta

from app.core.database import db_manager
from app.auth.routes import get_current_user, require_permission
from app.auth.models import UserProfile
from .models import (
    ServerCreate, ServerUpdate, ServerResponse,
    BunkerSectorCreate, BunkerSectorUpdate, BunkerSectorResponse,
    NotificationConfigCreate, NotificationConfigUpdate, NotificationConfigResponse,
    BunkerRegistration, BunkerRegistrationList, BunkerStats, BunkerSystemStats,
    BunkerServerConfig, BunkerAlert, BunkerAlertList, BunkerUsageStats,
    BunkerManualRegister, BunkerBulkAction, BunkerExportRequest,
    BunkerStatus, NotificationType
)

router = APIRouter()

# SERVERS MANAGEMENT
@router.get("/servers", response_model=List[ServerResponse])
async def get_servers(
    guild_id: str = Query(..., description="Guild ID"),
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Get all servers for a guild"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
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
    
    servers_data = await db_manager.execute_query(query, (guild_id,))
    
    servers = []
    for server in servers_data:
        default_channels = []
        if server['default_notification_channels']:
            default_channels = json.loads(server['default_notification_channels'])
        
        servers.append(ServerResponse(
            id=server['id'],
            guild_id=server['guild_id'],
            name=server['name'],
            display_name=server['display_name'],
            description=server['description'],
            max_bunkers=server['max_bunkers'],
            is_active=bool(server['is_active']),
            default_notification_channels=default_channels,
            created_at=datetime.fromisoformat(server['created_at']),
            updated_at=datetime.fromisoformat(server['updated_at']),
            created_by=server['created_by'],
            total_bunkers=server['total_bunkers'] or 0,
            active_bunkers=server['active_bunkers'] or 0
        ))
    
    return servers

@router.post("/servers", response_model=ServerResponse)
async def create_server(
    guild_id: str = Query(..., description="Guild ID"),
    server_data: ServerCreate = ...,
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Create a new server"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if server name already exists
    existing_query = "SELECT id FROM admin_bunker_servers WHERE guild_id = ? AND name = ?"
    existing = await db_manager.execute_query(existing_query, (guild_id, server_data.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server name already exists"
        )
    
    now = datetime.now().isoformat()
    default_channels_json = json.dumps(server_data.default_notification_channels) if server_data.default_notification_channels else None
    
    insert_query = """
        INSERT INTO admin_bunker_servers 
        (guild_id, name, display_name, description, max_bunkers, is_active, 
         default_notification_channels, created_at, updated_at, created_by)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
    """
    
    result = await db_manager.execute_query(
        insert_query, 
        (guild_id, server_data.name, server_data.display_name, server_data.description,
         server_data.max_bunkers, default_channels_json, now, now, current_user.username)
    )
    
    # Get the created server
    server_id = result  # This should be the lastrowid
    get_query = "SELECT * FROM admin_bunker_servers WHERE id = ?"
    server_row = await db_manager.execute_query(get_query, (server_id,))
    
    if not server_row:
        raise HTTPException(status_code=500, detail="Failed to create server")
    
    server = server_row[0]
    default_channels = []
    if server['default_notification_channels']:
        default_channels = json.loads(server['default_notification_channels'])
    
    return ServerResponse(
        id=server['id'],
        guild_id=server['guild_id'],
        name=server['name'],
        display_name=server['display_name'],
        description=server['description'],
        max_bunkers=server['max_bunkers'],
        is_active=bool(server['is_active']),
        default_notification_channels=default_channels,
        created_at=datetime.fromisoformat(server['created_at']),
        updated_at=datetime.fromisoformat(server['updated_at']),
        created_by=server['created_by'],
        total_bunkers=0,
        active_bunkers=0
    )

@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    guild_id: str = Query(..., description="Guild ID"),
    server_data: ServerUpdate = ...,
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Update a server"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check server exists and belongs to guild
    check_query = "SELECT id FROM admin_bunker_servers WHERE id = ? AND guild_id = ?"
    server_exists = await db_manager.execute_query(check_query, (server_id, guild_id))
    if not server_exists:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    if server_data.name is not None:
        update_fields.append("name = ?")
        params.append(server_data.name)
    if server_data.display_name is not None:
        update_fields.append("display_name = ?")
        params.append(server_data.display_name)
    if server_data.description is not None:
        update_fields.append("description = ?")
        params.append(server_data.description)
    if server_data.max_bunkers is not None:
        update_fields.append("max_bunkers = ?")
        params.append(server_data.max_bunkers)
    if server_data.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(1 if server_data.is_active else 0)
    if server_data.default_notification_channels is not None:
        update_fields.append("default_notification_channels = ?")
        params.append(json.dumps(server_data.default_notification_channels))
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(server_id)
    
    update_query = f"""
        UPDATE admin_bunker_servers 
        SET {', '.join(update_fields)}
        WHERE id = ?
    """
    
    await db_manager.execute_query(update_query, tuple(params))
    
    # Return updated server
    return await get_server_by_id(server_id, guild_id, current_user)

@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: int,
    guild_id: str = Query(..., description="Guild ID"),
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Delete a server and all its bunkers"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check server exists
    check_query = "SELECT name FROM admin_bunker_servers WHERE id = ? AND guild_id = ?"
    server_data = await db_manager.execute_query(check_query, (server_id, guild_id))
    if not server_data:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server_name = server_data[0]['name']
    
    # Delete all bunkers for this server
    delete_bunkers_query = "DELETE FROM bunkers WHERE server_name = ? AND discord_guild_id = ?"
    await db_manager.execute_query(delete_bunkers_query, (server_name, guild_id))
    
    # Delete the server
    delete_server_query = "DELETE FROM admin_bunker_servers WHERE id = ?"
    await db_manager.execute_query(delete_server_query, (server_id,))
    
    return {"message": f"Server {server_name} and all its bunkers deleted successfully"}

# BUNKER SECTORS MANAGEMENT
@router.get("/sectors", response_model=List[BunkerSectorResponse])
async def get_bunker_sectors(
    guild_id: str = Query(..., description="Guild ID"),
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Get all bunker sectors for a guild"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
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
    
    sectors_data = await db_manager.execute_query(query, (guild_id,))
    
    sectors = []
    for sector in sectors_data:
        sectors.append(BunkerSectorResponse(
            id=sector['id'],
            guild_id=sector['guild_id'],
            sector=sector['sector'],
            name=sector['name'],
            coordinates=sector['coordinates'],
            description=sector['description'],
            default_duration_hours=sector['default_duration_hours'],
            notification_enabled=bool(sector['notification_enabled']),
            is_active=bool(sector['is_active']),
            created_at=datetime.fromisoformat(sector['created_at']),
            updated_at=datetime.fromisoformat(sector['updated_at']),
            created_by=sector['created_by'],
            total_registrations=sector['total_registrations'] or 0,
            active_registrations=sector['active_registrations'] or 0
        ))
    
    return sectors

@router.post("/sectors", response_model=BunkerSectorResponse)
async def create_bunker_sector(
    guild_id: str = Query(..., description="Guild ID"),
    sector_data: BunkerSectorCreate = ...,
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Create a new bunker sector"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if sector already exists
    existing_query = "SELECT id FROM admin_bunker_sectors WHERE guild_id = ? AND sector = ?"
    existing = await db_manager.execute_query(existing_query, (guild_id, sector_data.sector.upper()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sector already exists"
        )
    
    now = datetime.now().isoformat()
    
    insert_query = """
        INSERT INTO admin_bunker_sectors 
        (guild_id, sector, name, coordinates, description, default_duration_hours, 
         notification_enabled, is_active, created_at, updated_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    """
    
    result = await db_manager.execute_query(
        insert_query, 
        (guild_id, sector_data.sector.upper(), sector_data.name, sector_data.coordinates,
         sector_data.description, sector_data.default_duration_hours,
         1 if sector_data.notification_enabled else 0, now, now, current_user.username)
    )
    
    # Return created sector
    sector_id = result
    get_query = "SELECT * FROM admin_bunker_sectors WHERE id = ?"
    sector_row = await db_manager.execute_query(get_query, (sector_id,))
    
    if not sector_row:
        raise HTTPException(status_code=500, detail="Failed to create sector")
    
    sector = sector_row[0]
    return BunkerSectorResponse(
        id=sector['id'],
        guild_id=sector['guild_id'],
        sector=sector['sector'],
        name=sector['name'],
        coordinates=sector['coordinates'],
        description=sector['description'],
        default_duration_hours=sector['default_duration_hours'],
        notification_enabled=bool(sector['notification_enabled']),
        is_active=bool(sector['is_active']),
        created_at=datetime.fromisoformat(sector['created_at']),
        updated_at=datetime.fromisoformat(sector['updated_at']),
        created_by=sector['created_by'],
        total_registrations=0,
        active_registrations=0
    )

# BUNKER REGISTRATIONS
@router.get("/registrations", response_model=BunkerRegistrationList)
async def get_bunker_registrations(
    guild_id: str = Query(..., description="Guild ID"),
    server_name: Optional[str] = Query(None, description="Filter by server"),
    status_filter: Optional[BunkerStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Get bunker registrations with filters and pagination"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Build query conditions
    where_conditions = ["discord_guild_id = ?"]
    params = [guild_id]
    
    if server_name:
        where_conditions.append("server_name = ?")
        params.append(server_name)
    
    where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as count FROM bunkers {where_clause}"
    count_result = await db_manager.execute_query(count_query, tuple(params))
    total = count_result[0]['count']
    
    # Get bunkers with pagination
    offset = (page - 1) * page_size
    query = f"""
        SELECT * FROM bunkers
        {where_clause}
        ORDER BY 
            CASE WHEN expiry_time > datetime('now') THEN 1 ELSE 2 END,
            expiry_time DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    
    bunkers_data = await db_manager.execute_query(query, tuple(params))
    
    bunkers = []
    active = 0
    expired = 0
    near_expiry = 0
    
    for bunker in bunkers_data:
        # Calculate status and time remaining
        now = datetime.now()
        expiry_time = datetime.fromisoformat(bunker['expiry_time']) if bunker['expiry_time'] else None
        
        if not expiry_time:
            status = BunkerStatus.UNKNOWN
            time_remaining = None
            expired_minutes_ago = None
        elif expiry_time > now:
            time_diff = expiry_time - now
            if time_diff.total_seconds() <= 1800:  # 30 minutes
                status = BunkerStatus.NEAR_EXPIRY
                near_expiry += 1
            else:
                status = BunkerStatus.ACTIVE
                active += 1
            
            hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            time_remaining = f"{hours}h {minutes}m"
            expired_minutes_ago = None
        else:
            status = BunkerStatus.EXPIRED
            expired += 1
            time_remaining = None
            expired_minutes_ago = int((now - expiry_time).total_seconds() / 60)
        
        bunkers.append(BunkerRegistration(
            id=bunker['id'],
            guild_id=bunker['discord_guild_id'],
            sector=bunker['sector'],
            name=bunker['name'],
            server_name=bunker['server_name'],
            registered_time=datetime.fromisoformat(bunker['registered_time']),
            expiry_time=expiry_time,
            registered_by=bunker['registered_by'],
            discord_user_id=bunker['discord_user_id'],
            last_updated=datetime.fromisoformat(bunker['last_updated']),
            status=status,
            time_remaining=time_remaining,
            expired_minutes_ago=expired_minutes_ago
        ))
    
    # Apply status filter if specified
    if status_filter:
        bunkers = [b for b in bunkers if b.status == status_filter]
    
    return BunkerRegistrationList(
        bunkers=bunkers,
        total=total,
        active=active,
        expired=expired,
        near_expiry=near_expiry,
        page=page,
        page_size=page_size
    )

@router.post("/registrations/manual")
async def register_bunker_manual(
    guild_id: str = Query(..., description="Guild ID"),
    registration: BunkerManualRegister = ...,
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Manually register a bunker"""
    if guild_id not in current_user.guilds and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this guild"
        )
    
    # Check if sector exists in admin config
    sector_query = "SELECT id FROM admin_bunker_sectors WHERE guild_id = ? AND sector = ? AND is_active = 1"
    sector_exists = await db_manager.execute_query(sector_query, (guild_id, registration.sector.upper()))
    if not sector_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sector {registration.sector} not found or inactive"
        )
    
    # Check if server exists
    server_query = "SELECT id FROM admin_bunker_servers WHERE guild_id = ? AND name = ? AND is_active = 1"
    server_exists = await db_manager.execute_query(server_query, (guild_id, registration.server_name))
    if not server_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server {registration.server_name} not found or inactive"
        )
    
    now = datetime.now()
    expiry_time = now + timedelta(hours=registration.hours, minutes=registration.minutes)
    
    # Update or insert bunker registration
    upsert_query = """
        INSERT OR REPLACE INTO bunkers 
        (sector, name, server_name, discord_guild_id, registered_time, expiry_time, 
         registered_by, discord_user_id, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    await db_manager.execute_query(
        upsert_query,
        (registration.sector.upper(), registration.sector.upper(), registration.server_name,
         guild_id, now.isoformat(), expiry_time.isoformat(), registration.registered_by,
         current_user.user_id, now.isoformat())
    )
    
    return {
        "message": f"Bunker {registration.sector} registered successfully",
        "sector": registration.sector.upper(),
        "server": registration.server_name,
        "expiry_time": expiry_time.isoformat(),
        "duration": f"{registration.hours}h {registration.minutes}m"
    }

# STATISTICS
@router.get("/stats/system", response_model=BunkerSystemStats)
async def get_bunker_system_stats(
    current_user: UserProfile = Depends(require_permission("bunkers"))
):
    """Get global bunker system statistics"""
    if current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    # Get total counts
    stats_queries = {
        "total_servers": "SELECT COUNT(*) as count FROM admin_bunker_servers",
        "total_sectors": "SELECT COUNT(*) as count FROM admin_bunker_sectors", 
        "total_registrations": "SELECT COUNT(*) as count FROM bunkers",
        "active_registrations": "SELECT COUNT(*) as count FROM bunkers WHERE expiry_time > datetime('now')",
        "total_guilds": "SELECT COUNT(DISTINCT discord_guild_id) as count FROM bunkers",
        "registrations_today": "SELECT COUNT(*) as count FROM bunkers WHERE DATE(registered_time) = DATE('now')"
    }
    
    stats = {}
    for key, query in stats_queries.items():
        result = await db_manager.execute_query(query, ())
        stats[key] = result[0]['count']
    
    # Get top servers
    top_servers_query = """
        SELECT s.display_name, s.guild_id, COUNT(b.id) as bunker_count
        FROM admin_bunker_servers s
        LEFT JOIN bunkers b ON b.server_name = s.name AND b.discord_guild_id = s.guild_id
        GROUP BY s.id
        ORDER BY bunker_count DESC
        LIMIT 10
    """
    top_servers_data = await db_manager.execute_query(top_servers_query, ())
    top_servers = [{"name": row["display_name"], "guild_id": row["guild_id"], "bunkers": row["bunker_count"]} for row in top_servers_data]
    
    # Get recent activity
    recent_activity_query = """
        SELECT sector, server_name, registered_time
        FROM bunkers
        WHERE registered_time >= datetime('now', '-24 hours')
        ORDER BY registered_time DESC
        LIMIT 20
    """
    recent_data = await db_manager.execute_query(recent_activity_query, ())
    recent_activity = [{"sector": row["sector"], "server": row["server_name"], "time": row["registered_time"]} for row in recent_data]
    
    # Determine system health
    health = "healthy"
    if stats["active_registrations"] == 0:
        health = "warning"
    elif stats["registrations_today"] == 0:
        health = "warning"
    
    return BunkerSystemStats(
        total_servers=stats["total_servers"],
        total_sectors=stats["total_sectors"],
        total_registrations=stats["total_registrations"],
        active_registrations=stats["active_registrations"],
        total_guilds=stats["total_guilds"],
        registrations_today=stats["registrations_today"],
        system_health=health,
        top_servers=top_servers,
        recent_activity=recent_activity
    )

# Helper functions
async def get_server_by_id(server_id: int, guild_id: str, current_user: UserProfile) -> ServerResponse:
    """Get server by ID with stats"""
    query = """
        SELECT s.*, 
               COUNT(DISTINCT b.id) as total_bunkers,
               COUNT(DISTINCT CASE WHEN b.expiry_time > datetime('now') THEN b.id END) as active_bunkers
        FROM admin_bunker_servers s
        LEFT JOIN bunkers b ON b.server_name = s.name AND b.discord_guild_id = s.guild_id
        WHERE s.id = ? AND s.guild_id = ?
        GROUP BY s.id
    """
    
    server_data = await db_manager.execute_query(query, (server_id, guild_id))
    if not server_data:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = server_data[0]
    default_channels = []
    if server['default_notification_channels']:
        default_channels = json.loads(server['default_notification_channels'])
    
    return ServerResponse(
        id=server['id'],
        guild_id=server['guild_id'],
        name=server['name'],
        display_name=server['display_name'],
        description=server['description'],
        max_bunkers=server['max_bunkers'],
        is_active=bool(server['is_active']),
        default_notification_channels=default_channels,
        created_at=datetime.fromisoformat(server['created_at']),
        updated_at=datetime.fromisoformat(server['updated_at']),
        created_by=server['created_by'],
        total_bunkers=server['total_bunkers'] or 0,
        active_bunkers=server['active_bunkers'] or 0
    )