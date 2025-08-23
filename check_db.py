import asyncio
import aiosqlite

async def check_db():
    try:
        async with aiosqlite.connect('scum_main.db') as db:
            # Ver tablas
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            print('=== TABLAS EN LA BASE DE DATOS ===')
            for table in tables:
                print(f'Tabla: {table[0]}')
            
            # Ver estructura de taxi_requests
            cursor = await db.execute('PRAGMA table_info(taxi_requests)')
            columns = await cursor.fetchall()
            print('\n=== ESTRUCTURA DE taxi_requests ===')
            for col in columns:
                print(f'{col[1]} ({col[2]})')
            
            # Ver estructura de users 
            cursor = await db.execute('PRAGMA table_info(users)')
            columns = await cursor.fetchall()
            print('\n=== ESTRUCTURA DE users ===')
            for col in columns:
                print(f'{col[1]} ({col[2]})')
            
            # Ver todas las solicitudes recientes
            cursor = await db.execute("SELECT request_id, request_uuid, status, passenger_id FROM taxi_requests ORDER BY created_at DESC LIMIT 5")
            rows = await cursor.fetchall()
            print(f'\n=== ÚLTIMAS SOLICITUDES ===')
            for row in rows:
                print(f'ID: {row[0]}, UUID: {row[1]}, Status: {row[2]}, Passenger: {row[3]}')
            
            # Buscar por UUID
            cursor = await db.execute("SELECT * FROM taxi_requests WHERE request_uuid = '9396b785-3add-4353-9a1d-d631f8326952'")
            row = await cursor.fetchone()
            print(f'\n=== SOLICITUD POR UUID ===')
            if row:
                print(f'Encontrada: request_id={row[0]}, status={row[16]}, passenger_id={row[2]}')
            else:
                print('❌ No encontrada por UUID')
            
            # Ver usuarios
            cursor = await db.execute("SELECT user_id, discord_id, discord_guild_id FROM users WHERE discord_id = '418198613210955776'")
            user_row = await cursor.fetchone()
            print(f'\n=== USUARIO ===')
            if user_row:
                print(f'User ID: {user_row[0]}, Discord: {user_row[1]}, Guild: {user_row[2]}')
                
                # Buscar solicitudes de este usuario
                cursor = await db.execute("SELECT request_id, request_uuid, status FROM taxi_requests WHERE passenger_id = ? ORDER BY created_at DESC", (user_row[0],))
                user_requests = await cursor.fetchall()
                print(f'\n=== SOLICITUDES DEL USUARIO {user_row[0]} ===')
                for req in user_requests:
                    print(f'ID: {req[0]}, UUID: {req[1]}, Status: {req[2]}')
            else:
                print('❌ Usuario no encontrado')
                
                # Ver todos los usuarios para debug
                cursor = await db.execute("SELECT user_id, discord_id, discord_guild_id FROM users")
                all_users = await cursor.fetchall()
                print(f'\n=== TODOS LOS USUARIOS ===')
                for user in all_users:
                    print(f'User ID: {user[0]}, Discord: {user[1]}, Guild: {user[2]}')
                
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(check_db())
