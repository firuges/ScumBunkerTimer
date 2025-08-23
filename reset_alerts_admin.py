#!/usr/bin/env python3
"""
Comandos Administrativos para Sistema de Alertas de Reinicio
Comandos específicos para gestionar horarios de reinicio de servidores
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from taxi_database import taxi_db

logger = logging.getLogger(__name__)

def is_bot_admin():
    """Decorator para verificar si el usuario es admin del bot"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Primero intentar desde variables de entorno (.env)
        admin_ids_env = os.getenv('BOT_ADMIN_IDS', '').split(',')
        admin_ids_from_env = [id.strip() for id in admin_ids_env if id.strip()]
        
        # Si no hay IDs en .env, usar config.py como respaldo
        if not admin_ids_from_env:
            from config import BOT_ADMIN_IDS
            admin_ids_from_config = [str(id) for id in BOT_ADMIN_IDS]
            admin_ids = admin_ids_from_config
        else:
            admin_ids = admin_ids_from_env
        
        user_id = str(interaction.user.id)
        is_admin = user_id in admin_ids
        return is_admin
    return app_commands.check(predicate)

class ResetAlertsAdmin(commands.Cog):
    """Comandos administrativos para alertas de reinicio"""
    
    def __init__(self, bot):
        self.bot = bot

    async def server_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompletado para nombres de servidores en comandos de reset"""
        try:
            # Verificar que estamos en un servidor
            if not interaction.guild:
                return [app_commands.Choice(name="❌ Ejecutar en servidor", value="no_guild")]
            
            from server_database import server_db
            guild_id = str(interaction.guild.id)
            servers = await server_db.get_monitored_servers(guild_id)
            
            # Filtrar servidores que coincidan con la entrada actual
            matching_servers = []
            for server in servers:
                server_name = server['server_name']
                if current.lower() in server_name.lower():
                    matching_servers.append(app_commands.Choice(name=server_name, value=server_name))
            
            # Limitar a 25 resultados (límite de Discord)
            return matching_servers[:25]
            
        except Exception as e:
            logger.error(f"Error en autocompletado de servidores: {e}")
            return []
    
    @app_commands.command(name="ba_admin_resethour_add", description="[ADMIN] Agregar horario de reinicio del servidor")
    @app_commands.describe(
        server_name="Nombre del servidor SCUM",
        reset_time="Hora del reinicio (formato HH:MM, ej: 14:30)",
        timezone="Zona horaria",
        days="Días de la semana (1=Lun, 7=Dom, ej: 1,3,5)"
    )
    @app_commands.choices(timezone=[
        app_commands.Choice(name="🇺🇾 Uruguay (UTC-3)", value="America/Montevideo"),
        app_commands.Choice(name="🇦🇷 Argentina (UTC-3)", value="America/Argentina/Buenos_Aires"),
        app_commands.Choice(name="🇧🇷 Brasil (UTC-3)", value="America/Sao_Paulo"),
        app_commands.Choice(name="🇨🇱 Chile (UTC-3)", value="America/Santiago"),
        app_commands.Choice(name="🇵🇾 Paraguay (UTC-3)", value="America/Asuncion"),
        app_commands.Choice(name="🇺🇸 Estados Unidos Este (UTC-5)", value="America/New_York"),
        app_commands.Choice(name="🇺🇸 Estados Unidos Centro (UTC-6)", value="America/Chicago"),
        app_commands.Choice(name="🇺🇸 Estados Unidos Oeste (UTC-8)", value="America/Los_Angeles"),
        app_commands.Choice(name="🇪🇸 España (UTC+1)", value="Europe/Madrid"),
        app_commands.Choice(name="🇩🇪 Alemania (UTC+1)", value="Europe/Berlin"),
        app_commands.Choice(name="🇬🇧 Reino Unido (UTC+0)", value="Europe/London"),
        app_commands.Choice(name="🌍 UTC (UTC+0)", value="UTC")
    ])
    @app_commands.autocomplete(server_name=server_name_autocomplete)
    @is_bot_admin()
    async def add_reset_schedule(self, interaction: discord.Interaction, 
                               server_name: str, reset_time: str, 
                               timezone: str = "UTC", days: str = "1,2,3,4,5,6,7"):
        """Agregar un horario de reinicio para un servidor"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar formato de hora
            import re
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', reset_time):
                await interaction.followup.send("❌ Formato de hora inválido. Usa HH:MM (ej: 14:30)", ephemeral=True)
                return
            
            # Validar días de la semana
            try:
                days_list = [int(d.strip()) for d in days.split(',')]
                if not all(1 <= d <= 7 for d in days_list):
                    raise ValueError("Días fuera de rango")
            except:
                await interaction.followup.send("❌ Formato de días inválido. Usa números del 1-7 separados por comas (ej: 1,3,5)", ephemeral=True)
                return
            
            # Verificar que el servidor existe en la base de datos
            from server_database import server_db
            guild_id = str(interaction.guild.id)
            servers = await server_db.get_monitored_servers(guild_id)
            server_exists = any(s['server_name'] == server_name for s in servers)
            
            if not server_exists:
                await interaction.followup.send(f"❌ Servidor '{server_name}' no encontrado. Usa `/ba_monitor_add_server` para agregarlo primero.", ephemeral=True)
                return
            
            # Agregar horario
            success = await taxi_db.add_reset_schedule(
                server_name=server_name,
                reset_time=reset_time,
                admin_id=str(interaction.user.id),
                timezone=timezone,
                days_of_week=days
            )
            
            if success:
                days_names = {1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb", 7: "Dom"}
                days_str = ", ".join([days_names[d] for d in sorted(days_list)])
                
                embed = discord.Embed(
                    title="✅ Horario de Reinicio Agregado",
                    description=f"Se configuró un nuevo horario de reinicio para **{server_name}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="🕐 Hora", value=reset_time, inline=True)
                embed.add_field(name="🌍 Zona Horaria", value=timezone, inline=True)
                embed.add_field(name="📅 Días", value=days_str, inline=True)
                
                embed.add_field(
                    name="📢 ¿Qué sigue?",
                    value="• Los usuarios pueden suscribirse con `/ba_reset_alerts`\n• Verifica horarios con `/ba_admin_resethour_info`\n• Las alertas se enviarán automáticamente",
                    inline=False
                )
                
                embed.set_footer(text=f"Configurado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Error agregando el horario de reinicio", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error agregando horario de reinicio: {e}")
            await interaction.followup.send("❌ Error procesando el comando", ephemeral=True)

    @app_commands.command(name="ba_admin_resethour_remove", description="[ADMIN] Eliminar horario de reinicio")
    @app_commands.describe(
        server_name="Nombre del servidor SCUM",
        schedule_id="ID del horario a eliminar (ver con /ba_admin_resethour_info)"
    )
    @app_commands.autocomplete(server_name=server_name_autocomplete)
    @is_bot_admin()
    async def remove_reset_schedule(self, interaction: discord.Interaction, 
                                  server_name: str, schedule_id: int):
        """Eliminar un horario de reinicio"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = await taxi_db.remove_reset_schedule(schedule_id, server_name)
            
            if success:
                embed = discord.Embed(
                    title="✅ Horario Eliminado",
                    description=f"Se eliminó el horario de reinicio para **{server_name}**",
                    color=discord.Color.orange()
                )
                embed.add_field(name="🗑️ ID Eliminado", value=str(schedule_id), inline=True)
                embed.set_footer(text=f"Eliminado por {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ Error eliminando el horario. Verifica que el ID y servidor sean correctos.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error eliminando horario de reinicio: {e}")
            await interaction.followup.send("❌ Error procesando el comando", ephemeral=True)

    @app_commands.command(name="ba_admin_resethour_info", description="[ADMIN] Ver horarios de reinicio configurados")
    @app_commands.describe(server_name="Nombre del servidor (opcional - deja vacío para ver todos)")
    @app_commands.autocomplete(server_name=server_name_autocomplete)
    @is_bot_admin()
    async def view_reset_schedules(self, interaction: discord.Interaction, server_name: str = None):
        """Ver horarios de reinicio configurados"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            schedules = await taxi_db.get_reset_schedules(server_name)
            
            if not schedules:
                if server_name:
                    message = f"No hay horarios configurados para **{server_name}**"
                else:
                    message = "No hay horarios de reinicio configurados"
                
                embed = discord.Embed(
                    title="📅 Horarios de Reinicio",
                    description=message,
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 Cómo agregar horarios",
                    value="• Usa `/ba_admin_resethour_add`\n• Selecciona timezone (incluye Uruguay UTC-3)\n• Formato de hora: HH:MM (ej: 14:30)\n• Días: 1=Lun, 2=Mar, 3=Mié, 4=Jue, 5=Vie, 6=Sáb, 7=Dom",
                    inline=False
                )
                embed.add_field(
                    name="🔔 Para usuarios finales",
                    value="Los usuarios pueden suscribirse a alertas con `/ba_reset_alerts`",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="📅 Horarios de Reinicio Configurados",
                    description=f"Total: **{len(schedules)}** horarios",
                    color=discord.Color.blue()
                )
                
                days_names = {1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb", 7: "Dom"}
                
                for schedule in schedules:
                    # Convertir días de la semana
                    try:
                        days_list = [int(d.strip()) for d in schedule['days_of_week'].split(',')]
                        days_str = ", ".join([days_names[d] for d in sorted(days_list)])
                    except:
                        days_str = schedule['days_of_week']
                    
                    field_value = f"🕐 **Hora:** {schedule['reset_time']}\n"
                    field_value += f"🌍 **Zona:** {schedule['timezone']}\n"
                    field_value += f"📅 **Días:** {days_str}\n"
                    field_value += f"🆔 **ID:** {schedule['id']}"
                    
                    embed.add_field(
                        name=f"🎮 {schedule['server_name']}",
                        value=field_value,
                        inline=True
                    )
                
                # Agregar campo de ayuda cuando hay horarios
                embed.add_field(
                    name="🛠️ Comandos Administrativos",
                    value="• `/ba_admin_resethour_add` - Agregar nuevo horario\n• `/ba_admin_resethour_remove` - Eliminar horario (usa el ID)\n• `/ba_admin_resethour_info` - Ver esta información",
                    inline=False
                )
                embed.add_field(
                    name="⏰ Información de Zonas Horarias",
                    value="🇺🇾 Uruguay: UTC-3 | 🇦🇷 Argentina: UTC-3 | 🇧🇷 Brasil: UTC-3\n🇺🇸 USA Este: UTC-5 | 🇪🇸 España: UTC+1 | 🌍 UTC: UTC+0",
                    inline=False
                )
                embed.set_footer(text="Los usuarios pueden suscribirse con /ba_reset_alerts")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error consultando horarios de reinicio: {e}")
            await interaction.followup.send("❌ Error procesando el comando", ephemeral=True)

    @app_commands.command(name="ba_admin_test_reset_alert", description="[ADMIN] 🧪 Enviar alerta de reset de prueba")
    @app_commands.describe(
        server_name="Nombre del servidor SCUM",
        minutes_before="Minutos antes del reinicio (por defecto 15)"
    )
    @app_commands.autocomplete(server_name=server_name_autocomplete)
    @is_bot_admin()
    async def test_reset_alert(self, interaction: discord.Interaction, 
                              server_name: str, minutes_before: int = 15):
        """Enviar una alerta de reinicio de prueba"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar que el comando se ejecuta en un servidor
            if not interaction.guild:
                await interaction.followup.send("❌ Este comando debe ejecutarse en un servidor, no en DM.", ephemeral=True)
                return
            
            # Verificar que el servidor existe
            from server_database import server_db
            guild_id = str(interaction.guild.id)
            servers = await server_db.get_monitored_servers(guild_id)
            server_exists = any(s['server_name'] == server_name for s in servers)
            
            if not server_exists:
                await interaction.followup.send(f"❌ Servidor '{server_name}' no encontrado.", ephemeral=True)
                return
            
            # Obtener suscriptores de este servidor
            all_subscriptions = await taxi_db.get_users_for_reset_alert(server_name)
            # Filtrar por guild actual
            subscriptions = [sub for sub in all_subscriptions if sub['guild_id'] == guild_id]
            
            if not subscriptions:
                embed = discord.Embed(
                    title="⚠️ No hay suscriptores",
                    description=f"No hay usuarios suscritos a alertas de **{server_name}**",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 Información",
                    value="Los usuarios pueden suscribirse con `/ba_reset_alerts`",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Enviar alertas de prueba
            sent_count = 0
            failed_count = 0
            user_not_found_count = 0
            dm_blocked_count = 0
            failed_details = []
            
            for sub in subscriptions:
                try:
                    user_id = int(sub['user_id'])
                    user = self.bot.get_user(user_id)
                    
                    # Si no está en cache pero es el usuario que ejecuta el comando, usar interaction.user
                    if not user and user_id == interaction.user.id:
                        user = interaction.user
                        logger.info(f"Usando interaction.user como fallback para {user_id}")
                    
                    if user:
                        try:
                            # Crear embed de alerta de prueba
                            alert_embed = discord.Embed(
                                title="🧪 ALERTA DE PRUEBA - Reinicio de Servidor",
                                description=f"**{server_name}** se reiniciará en **{minutes_before} minutos**",
                                color=discord.Color.red()
                            )
                            alert_embed.add_field(
                                name="⚠️ ESTO ES UNA PRUEBA",
                                value="Esta es una alerta de prueba enviada por un administrador",
                                inline=False
                            )
                            alert_embed.add_field(
                                name="⏰ Tiempo estimado",
                                value=f"{minutes_before} minutos",
                                inline=True
                            )
                            alert_embed.add_field(
                                name="🎮 Servidor",
                                value=server_name,
                                inline=True
                            )
                            alert_embed.add_field(
                                name="📅 Configuración",
                                value=f"Alertas: {sub['minutes_before']} min antes",
                                inline=True
                            )
                            alert_embed.set_footer(text="🧪 Alerta de prueba enviada por administrador")
                            alert_embed.timestamp = datetime.now()
                            
                            await user.send(embed=alert_embed)
                            sent_count += 1
                            logger.info(f"✅ Alerta de prueba enviada a {user.display_name} ({user.id})")
                            
                        except discord.Forbidden:
                            dm_blocked_count += 1
                            failed_details.append(f"🔒 {user.display_name} ({user_id}): DMs bloqueados")
                            logger.warning(f"DMs bloqueados para usuario {user.display_name} ({user_id})")
                            
                        except discord.HTTPException as e:
                            failed_count += 1
                            failed_details.append(f"📡 {user.display_name} ({user_id}): Error HTTP")
                            logger.error(f"Error HTTP enviando DM a {user.display_name} ({user_id}): {e}")
                    else:
                        # Intentar obtener el usuario desde el guild como fallback
                        guild = self.bot.get_guild(int(sub['guild_id']))
                        member = guild.get_member(user_id) if guild else None
                        
                        if member:
                            failed_details.append(f"👤 {member.display_name} ({user_id}): Usuario en guild pero no en cache del bot")
                            logger.warning(f"Usuario {member.display_name} ({user_id}) en guild pero no en cache del bot")
                        else:
                            failed_details.append(f"❌ ID {user_id}: Usuario no encontrado")
                            logger.warning(f"Usuario {user_id} no encontrado ni en cache ni en guild")
                        
                        user_not_found_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    failed_details.append(f"⚠️ ID {sub['user_id']}: Error general")
                    logger.error(f"Error enviando alerta de prueba a {sub['user_id']}: {e}")
            
            total_failed = failed_count + user_not_found_count + dm_blocked_count
            
            # Respuesta al administrador
            embed = discord.Embed(
                title="🧪 Prueba de Alertas Completada",
                description=f"Resultados del envío de alertas de prueba para **{server_name}**",
                color=discord.Color.green() if total_failed == 0 else discord.Color.orange()
            )
            
            # Estadísticas principales
            embed.add_field(name="✅ Enviadas", value=str(sent_count), inline=True)
            embed.add_field(name="🔒 DMs Bloqueados", value=str(dm_blocked_count), inline=True)
            embed.add_field(name="❌ No Encontrados", value=str(user_not_found_count), inline=True)
            
            if failed_count > 0:
                embed.add_field(name="⚠️ Otros Errores", value=str(failed_count), inline=True)
            
            embed.add_field(name="📊 Total Suscriptores", value=str(len(subscriptions)), inline=True)
            embed.add_field(name="⏰ Config. Prueba", value=f"{minutes_before} min antes", inline=True)
            
            # Detalles de fallos si los hay
            if failed_details and len(failed_details) <= 10:  # Mostrar máximo 10 para no saturar
                details_text = "\n".join(failed_details[:10])
                if len(failed_details) > 10:
                    details_text += f"\n... y {len(failed_details) - 10} más"
                embed.add_field(
                    name="🔍 Detalles de Fallos",
                    value=f"```{details_text}```",
                    inline=False
                )
            elif total_failed > 0:
                embed.add_field(
                    name="💡 Posibles Causas",
                    value="• DMs desactivados por el usuario\n• Usuario abandonó el servidor\n• Cuenta eliminada/suspendida\n• Bot sin cache del usuario",
                    inline=False
                )
            
            if sent_count > 0:
                embed.add_field(
                    name="🎉 ¡Éxito!",
                    value=f"Se enviaron {sent_count} alertas de prueba correctamente",
                    inline=False
                )
            
            embed.set_footer(text=f"Prueba ejecutada por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en prueba de alertas de reinicio: {e}")
            await interaction.followup.send("❌ Error ejecutando la prueba", ephemeral=True)

    @app_commands.command(name="ba_admin_debug_user_cache", description="[ADMIN] 🔍 Diagnosticar cache del bot para un usuario")
    @app_commands.describe(user_id="ID del usuario a verificar (opcional - usa tu ID si no se especifica)")
    @is_bot_admin()
    async def debug_user_cache(self, interaction: discord.Interaction, user_id: str = None):
        """Diagnosticar problemas de cache del bot con usuarios"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Verificar que el comando se ejecuta en un servidor
            if not interaction.guild:
                await interaction.followup.send("❌ Este comando debe ejecutarse en un servidor, no en DM.", ephemeral=True)
                return
            
            # Usar ID del usuario que ejecuta el comando si no se especifica
            target_user_id = user_id if user_id else str(interaction.user.id)
            
            # Logging para debug
            logger.info(f"Diagnóstico iniciado para usuario {target_user_id} en guild {interaction.guild.id if interaction.guild else 'None'}")
            
            embed = discord.Embed(
                title="🔍 Diagnóstico de Cache del Bot",
                description=f"Verificando acceso al usuario: `{target_user_id}`",
                color=discord.Color.blue()
            )
            
            # 1. Verificar información del usuario que ejecuta el comando
            embed.add_field(
                name="👤 Usuario Ejecutor",
                value=f"**Nombre:** {interaction.user.display_name}\n**ID:** {interaction.user.id}\n**Bot puede verlo:** ✅ (estás ejecutando esto)",
                inline=False
            )
            
            # 2. Intentar obtener el usuario objetivo por ID
            try:
                target_user = self.bot.get_user(int(target_user_id))
                if target_user:
                    embed.add_field(
                        name="✅ Usuario en Cache del Bot",
                        value=f"**Nombre:** {target_user.display_name}\n**ID:** {target_user.id}\n**Creada:** <t:{int(target_user.created_at.timestamp())}:F>",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="❌ Usuario NO en Cache del Bot",
                        value=f"El usuario `{target_user_id}` no está en el cache del bot",
                        inline=False
                    )
            except ValueError:
                embed.add_field(
                    name="⚠️ Error",
                    value=f"ID inválido: `{target_user_id}`",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # 3. Verificar si está en el guild actual
            # Ya validamos que interaction.guild existe arriba, pero asignamos para claridad
            guild = interaction.guild
            
            member = guild.get_member(int(target_user_id))
            if member:
                embed.add_field(
                    name="✅ Miembro del Guild",
                    value=f"**Nombre en servidor:** {member.display_name}\n**Se unió:** <t:{int(member.joined_at.timestamp())}:F>",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ NO es Miembro del Guild",
                    value=f"El usuario `{target_user_id}` no es miembro de este servidor",
                    inline=False
                )
            
            # 4. Verificar suscripciones
            subscriptions = await taxi_db.get_user_reset_subscriptions(target_user_id, str(interaction.guild.id))
            if subscriptions:
                subs_text = []
                for sub in subscriptions[:5]:  # Mostrar máximo 5
                    status = "🔔 Activa" if sub.get('alert_enabled', True) else "🔕 Desactivada"
                    subs_text.append(f"• **{sub['server_name']}** - {status} ({sub['minutes_before']} min antes)")
                
                embed.add_field(
                    name="🔔 Suscripciones a Alertas",
                    value="\n".join(subs_text) + (f"\n... y {len(subscriptions) - 5} más" if len(subscriptions) > 5 else ""),
                    inline=False
                )
            else:
                embed.add_field(
                    name="📭 Sin Suscripciones",
                    value=f"El usuario `{target_user_id}` no tiene suscripciones a alertas de reinicio",
                    inline=False
                )
            
            # 5. Intentar enviar DM de prueba si es el mismo usuario
            if target_user_id == str(interaction.user.id):
                try:
                    test_embed = discord.Embed(
                        title="🧪 Prueba de DM",
                        description="Si recibes este mensaje, el bot puede enviarte DMs correctamente",
                        color=discord.Color.green()
                    )
                    test_embed.set_footer(text="Mensaje de prueba del sistema de diagnóstico")
                    
                    await interaction.user.send(embed=test_embed)
                    
                    embed.add_field(
                        name="✅ Prueba de DM",
                        value="DM de prueba enviado exitosamente. Revisa tus mensajes privados.",
                        inline=False
                    )
                except discord.Forbidden:
                    embed.add_field(
                        name="🔒 DMs Bloqueados",
                        value="No puedes recibir DMs del bot. Verifica tu configuración de privacidad.",
                        inline=False
                    )
                except Exception as dm_error:
                    embed.add_field(
                        name="❌ Error en DM",
                        value=f"Error enviando DM: {str(dm_error)}",
                        inline=False
                    )
            
            # 6. Información técnica
            embed.add_field(
                name="🔧 Información Técnica",
                value=f"• **Guilds del bot:** {len(self.bot.guilds)}\n• **Usuarios en cache:** {len(self.bot.users)}\n• **Latencia:** {round(self.bot.latency * 1000)}ms",
                inline=False
            )
            
            embed.set_footer(text=f"Diagnóstico ejecutado por {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en diagnóstico de cache: {e}")
            await interaction.followup.send("❌ Error ejecutando el diagnóstico", ephemeral=True)

    @app_commands.command(name="ba_admin_migrate_timezones", description="[ADMIN] 🌍 Migrar timezones de usuarios existentes")
    @app_commands.describe(
        target_timezone="Timezone a asignar (por defecto America/Montevideo)",
        dry_run="Solo mostrar lo que se haría, sin hacer cambios (true/false)"
    )
    @app_commands.choices(target_timezone=[
        app_commands.Choice(name="🇺🇾 Uruguay (UTC-3)", value="America/Montevideo"),
        app_commands.Choice(name="🇦🇷 Argentina (UTC-3)", value="America/Argentina/Buenos_Aires"),
        app_commands.Choice(name="🇧🇷 Brasil (UTC-3)", value="America/Sao_Paulo"),
        app_commands.Choice(name="🇺🇸 Estados Unidos Este (UTC-5)", value="America/New_York"),
        app_commands.Choice(name="🇪🇸 España (UTC+1)", value="Europe/Madrid"),
        app_commands.Choice(name="🌍 UTC (UTC+0)", value="UTC")
    ])
    @is_bot_admin()
    async def migrate_user_timezones(self, interaction: discord.Interaction, 
                                   target_timezone: str = "America/Montevideo", 
                                   dry_run: bool = True):
        """Migrar timezones de usuarios existentes que tienen UTC"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            import aiosqlite
            
            # Contar usuarios con UTC
            async with aiosqlite.connect("taxi_system.db") as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE timezone = 'UTC' OR timezone IS NULL
                """)
                utc_count = (await cursor.fetchone())[0]
                
                if utc_count == 0:
                    embed = discord.Embed(
                        title="✅ No Hay Usuarios Para Migrar",
                        description="Todos los usuarios ya tienen timezone configurado correctamente",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="🌍 Migración de Timezones" + (" (VISTA PREVIA)" if dry_run else ""),
                    description=f"Encontrados **{utc_count}** usuarios con timezone UTC",
                    color=discord.Color.blue() if dry_run else discord.Color.orange()
                )
                
                embed.add_field(
                    name="📊 Estadísticas",
                    value=f"• Usuarios a migrar: {utc_count}\n• Timezone destino: {target_timezone}\n• Modo: {'Vista previa' if dry_run else 'Migración real'}",
                    inline=False
                )
                
                if not dry_run:
                    # Ejecutar migración real
                    cursor = await db.execute("""
                        UPDATE users 
                        SET timezone = ? 
                        WHERE timezone = 'UTC' OR timezone IS NULL
                    """, (target_timezone,))
                    
                    await db.commit()
                    affected_rows = cursor.rowcount
                    
                    embed.add_field(
                        name="✅ Migración Completada",
                        value=f"Se actualizaron **{affected_rows}** usuarios exitosamente",
                        inline=False
                    )
                    embed.color = discord.Color.green()
                    
                    logger.info(f"Migración de timezones completada: {affected_rows} usuarios actualizados a {target_timezone}")
                    
                else:
                    # Mostrar algunos ejemplos
                    cursor = await db.execute("""
                        SELECT discord_id, username, discord_guild_id 
                        FROM users 
                        WHERE timezone = 'UTC' OR timezone IS NULL
                        LIMIT 10
                    """)
                    users = await cursor.fetchall()
                    
                    if users:
                        examples = []
                        for user in users[:5]:  # Mostrar máximo 5 ejemplos
                            examples.append(f"• {user[1]} (ID: {user[0][:8]}...)")
                        
                        embed.add_field(
                            name="👥 Ejemplos de Usuarios (primeros 5)",
                            value="\n".join(examples) + (f"\n... y {len(users) - 5} más" if len(users) > 5 else ""),
                            inline=False
                        )
                    
                    embed.add_field(
                        name="🚀 Para Ejecutar la Migración",
                        value=f"Usa el mismo comando con `dry_run:False`\n⚠️ **Esto actualizará {utc_count} usuarios permanentemente**",
                        inline=False
                    )
                
                embed.set_footer(text=f"Ejecutado por {interaction.user.display_name}")
                
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en migración de timezones: {e}")
            await interaction.followup.send("❌ Error ejecutando la migración", ephemeral=True)

    @app_commands.command(name="ba_admin_debug_channels", description="[ADMIN] 🔍 Diagnosticar configuración de canales")
    @is_bot_admin()
    async def debug_channel_configs(self, interaction: discord.Interaction):
        """Diagnosticar y mostrar configuraciones de canales"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            import aiosqlite
            
            # Verificar configuraciones en BD
            async with aiosqlite.connect("taxi_system.db") as db:
                cursor = await db.execute("""
                    SELECT guild_id, channel_type, channel_id, updated_at, updated_by 
                    FROM channel_config 
                    WHERE guild_id = ?
                    ORDER BY channel_type
                """, (str(interaction.guild.id),))
                rows = await cursor.fetchall()
                
                embed = discord.Embed(
                    title="🔍 Diagnóstico de Configuración de Canales",
                    description=f"Configuraciones para este servidor ({interaction.guild.name})",
                    color=discord.Color.blue()
                )
                
                if not rows:
                    embed.add_field(
                        name="❌ Sin Configuraciones",
                        value="No hay configuraciones de canales guardadas para este servidor",
                        inline=False
                    )
                else:
                    # Mostrar configuraciones existentes
                    configs_text = []
                    for row in rows:
                        channel_type = row[1]
                        channel_id = row[2]
                        updated_at = row[3]
                        updated_by = row[4]
                        
                        # Intentar obtener el canal
                        channel = self.bot.get_channel(int(channel_id))
                        channel_info = channel.mention if channel else f"❌ Canal no encontrado (ID: {channel_id})"
                        
                        configs_text.append(f"**{channel_type}**: {channel_info}")
                    
                    embed.add_field(
                        name="📋 Configuraciones en Base de Datos",
                        value="\n".join(configs_text),
                        inline=False
                    )
                    
                    # Verificar qué sistemas están cargados en memoria
                    memory_status = []
                    
                    # Verificar taxi
                    taxi_cog = self.bot.get_cog('TaxiSystem')
                    if taxi_cog and hasattr(taxi_cog, 'taxi_channels'):
                        taxi_loaded = interaction.guild.id in taxi_cog.taxi_channels
                        memory_status.append(f"🚖 **Taxi**: {'✅ Cargado' if taxi_loaded else '❌ No cargado'}")
                    
                    # Verificar banking
                    banking_cog = self.bot.get_cog('BankingSystem')
                    if banking_cog and hasattr(banking_cog, 'bank_channels'):
                        banking_loaded = interaction.guild.id in banking_cog.bank_channels
                        memory_status.append(f"🏦 **Banking**: {'✅ Cargado' if banking_loaded else '❌ No cargado'}")
                    
                    # Verificar welcome
                    welcome_cog = self.bot.get_cog('WelcomePackSystem')
                    if welcome_cog and hasattr(welcome_cog, 'welcome_channels'):
                        welcome_loaded = interaction.guild.id in welcome_cog.welcome_channels
                        memory_status.append(f"🎉 **Welcome**: {'✅ Cargado' if welcome_loaded else '❌ No cargado'}")
                    
                    if memory_status:
                        embed.add_field(
                            name="💾 Estado en Memoria (Bot)",
                            value="\n".join(memory_status),
                            inline=False
                        )
                    
                    # Verificar inconsistencias
                    inconsistencies = []
                    for row in rows:
                        channel_type = row[1]
                        if channel_type == "bank":  # Tipo incorrecto
                            inconsistencies.append(f"⚠️ **bank** debería ser **banking**")
                    
                    if inconsistencies:
                        embed.add_field(
                            name="🔧 Inconsistencias Detectadas",
                            value="\n".join(inconsistencies) + "\n\n💡 **Solución**: Reconfigurar canales con `/ba_admin_channels_setup`",
                            inline=False
                        )
                
                embed.set_footer(text=f"Diagnóstico ejecutado por {interaction.user.display_name}")
                
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en diagnóstico de canales: {e}")
            await interaction.followup.send("❌ Error ejecutando el diagnóstico", ephemeral=True)

    @app_commands.command(name="ba_admin_fix_channels", description="[ADMIN] 🔧 Corregir configuraciones de canales inconsistentes")
    @app_commands.describe(dry_run="Solo mostrar lo que se haría, sin hacer cambios (true/false)")
    @is_bot_admin()
    async def fix_channel_configs(self, interaction: discord.Interaction, dry_run: bool = True):
        """Corregir configuraciones de canales con tipos incorrectos"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            import aiosqlite
            from datetime import datetime
            
            # Buscar configuraciones incorrectas
            async with aiosqlite.connect("taxi_system.db") as db:
                cursor = await db.execute("""
                    SELECT guild_id, channel_type, channel_id, updated_at, updated_by 
                    FROM channel_config 
                    WHERE channel_type = 'bank'
                """)
                incorrect_configs = await cursor.fetchall()
                
                embed = discord.Embed(
                    title="🔧 Corrección de Configuraciones de Canales" + (" (VISTA PREVIA)" if dry_run else ""),
                    description=f"Corrigiendo configuraciones incorrectas",
                    color=discord.Color.blue() if dry_run else discord.Color.orange()
                )
                
                if not incorrect_configs:
                    embed.add_field(
                        name="✅ No Hay Problemas",
                        value="No se encontraron configuraciones de canales incorrectas",
                        inline=False
                    )
                else:
                    fixes_applied = 0
                    
                    for config in incorrect_configs:
                        guild_id = config[0]
                        old_type = config[1]  # "bank"
                        channel_id = config[2]
                        updated_at = config[3]
                        updated_by = config[4]
                        
                        new_type = "banking"  # Corrección
                        
                        if not dry_run:
                            # Aplicar corrección
                            await db.execute("""
                                UPDATE channel_config 
                                SET channel_type = ?, updated_at = ?
                                WHERE guild_id = ? AND channel_type = ? AND channel_id = ?
                            """, (new_type, datetime.now().isoformat(), guild_id, old_type, channel_id))
                            
                            fixes_applied += 1
                    
                    if not dry_run:
                        await db.commit()
                    
                    # Mostrar resultados
                    embed.add_field(
                        name="📊 Configuraciones Encontradas",
                        value=f"**{len(incorrect_configs)}** configuraciones con tipo incorrecto",
                        inline=True
                    )
                    
                    if dry_run:
                        embed.add_field(
                            name="🔍 Correcciones a Aplicar",
                            value=f"• **bank** → **banking** ({len(incorrect_configs)} configuraciones)",
                            inline=False
                        )
                        embed.add_field(
                            name="🚀 Para Aplicar las Correcciones",
                            value="Usa el mismo comando con `dry_run:False`",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="✅ Correcciones Aplicadas",
                            value=f"**{fixes_applied}** configuraciones corregidas exitosamente",
                            inline=True
                        )
                        embed.color = discord.Color.green()
                        
                        embed.add_field(
                            name="🔄 Siguiente Paso",
                            value="Reinicia el bot para que los cambios tomen efecto, o recarga los sistemas de canales",
                            inline=False
                        )
                        
                        logger.info(f"Corregidas {fixes_applied} configuraciones de canales incorrectas")
                
                embed.set_footer(text=f"Corrección ejecutada por {interaction.user.display_name}")
                
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en corrección de canales: {e}")
            await interaction.followup.send("❌ Error ejecutando la corrección", ephemeral=True)

async def setup(bot):
    """Función para cargar el cog"""
    await bot.add_cog(ResetAlertsAdmin(bot))
    logger.info("✅ Comandos de alertas de reinicio cargados exitosamente")