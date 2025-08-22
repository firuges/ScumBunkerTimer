#!/usr/bin/env python3
"""
Verificar Guild IDs en la base de datos vs servidor actual
"""

import asyncio
import sqlite3

def check_guild_consistency():
    """Verificar consistencia de Guild IDs"""
    print("VERIFICACIÓN DE GUILD IDS")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect("scum_main.db")
        cursor = conn.cursor()
        
        # Guild IDs en tickets
        cursor.execute("SELECT DISTINCT discord_guild_id FROM tickets")
        ticket_guilds = [row[0] for row in cursor.fetchall()]
        
        # Guild IDs en ticket_channels  
        cursor.execute("SELECT DISTINCT guild_id FROM ticket_channels")
        channel_guilds = [row[0] for row in cursor.fetchall()]
        
        # Guild IDs en channel_config
        cursor.execute("SELECT DISTINCT guild_id FROM channel_config")
        config_guilds = [row[0] for row in cursor.fetchall()]
        
        print("Guild IDs encontrados:")
        print(f"  tickets: {ticket_guilds}")
        print(f"  ticket_channels: {channel_guilds}")
        print(f"  channel_config: {config_guilds}")
        
        # Verificar consistencia
        all_guilds = set(ticket_guilds + channel_guilds + config_guilds)
        print(f"\nTodos los Guild IDs únicos: {list(all_guilds)}")
        
        # Verificar tickets activos con detalles
        print("\nTICKETS ACTIVOS:")
        cursor.execute("""
            SELECT ticket_id, ticket_number, discord_guild_id, channel_id, discord_id, status
            FROM tickets 
            WHERE status = 'open'
        """)
        
        active_tickets = cursor.fetchall()
        for ticket in active_tickets:
            print(f"  Ticket #{ticket[1]}: Guild {ticket[2]}, Canal {ticket[3]}, Usuario {ticket[4]}")
        
        # Verificar canales de tickets
        print("\nCANALES DE TICKETS:")
        cursor.execute("""
            SELECT tc.channel_id, tc.guild_id, tc.user_id, t.status
            FROM ticket_channels tc
            LEFT JOIN tickets t ON tc.channel_id = t.channel_id
        """)
        
        ticket_channels = cursor.fetchall()
        for channel in ticket_channels:
            status = channel[3] if channel[3] else "SIN TICKET"
            print(f"  Canal {channel[0]}: Guild {channel[1]}, Usuario {channel[2]}, Status: {status}")
        
        conn.close()
        
        # Verificar que los guild IDs son válidos (enteros de Discord)
        print("\nVERIFICACIÓN DE FORMATO:")
        for guild_id in all_guilds:
            try:
                guild_int = int(guild_id)
                if len(guild_id) >= 17 and len(guild_id) <= 20:  # Discord IDs típicos
                    print(f"  ✅ {guild_id} - Formato válido")
                else:
                    print(f"  ⚠️ {guild_id} - Formato sospechoso (longitud: {len(guild_id)})")
            except ValueError:
                print(f"  ❌ {guild_id} - No es un número válido")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_guild_consistency()