"""
Comandos administrativos para gestionar y monitorear el rate limiting
"""

import discord
from discord import app_commands
from discord.ext import commands
from rate_limiter import rate_limiter, get_rate_limit_stats, clear_user_limits
from config import BOT_ADMIN_IDS
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RateLimitAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, user_id: int) -> bool:
        """Verificar si el usuario es administrador del bot"""
        return user_id in BOT_ADMIN_IDS

    @app_commands.command(name="rate_limit_stats", description="[ADMIN] Ver estadísticas de rate limiting")
    @app_commands.describe(usuario="Usuario específico para ver sus estadísticas (opcional)")
    async def rate_limit_stats(self, interaction: discord.Interaction, usuario: discord.User = None):
        """Ver estadísticas de rate limiting"""
        
        if not self.is_admin(interaction.user.id):
            embed = discord.Embed(
                title="❌ Acceso Denegado",
                description="Este comando es solo para administradores.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        
        try:
            if usuario:
                # Estadísticas de usuario específico
                user_id = str(usuario.id)
                stats = await get_rate_limit_stats(guild_id, user_id)
                
                embed = discord.Embed(
                    title=f"📊 Estadísticas de Rate Limiting - {usuario.display_name}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                if not stats:
                    embed.description = "Este usuario no ha usado ningún comando recientemente."
                else:
                    for command_name, command_stats in stats.items():
                        embed.add_field(
                            name=f"🔹 /{command_name}",
                            value=f"""
                            **Uso Personal:** {command_stats['user_usage']}/{command_stats['user_limit']}
                            **Uso del Servidor:** {command_stats['guild_usage']}/{command_stats['guild_limit']}
                            **Cooldown:** {command_stats['cooldown']}s
                            """,
                            inline=True
                        )
            else:
                # Estadísticas generales del servidor
                embed = discord.Embed(
                    title="📈 Estadísticas Generales de Rate Limiting",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                # Configuración actual
                config_text = ""
                for cmd, config in rate_limiter.command_limits.items():
                    if cmd != 'default':
                        config_text += f"**/{cmd}:**\n"
                        config_text += f"• Usuario: {config['user_rate'][0]} usos / {config['user_rate'][1]}s\n"
                        config_text += f"• Servidor: {config['guild_rate'][0]} usos / {config['guild_rate'][1]}s\n"
                        config_text += f"• Cooldown: {config['cooldown']}s\n\n"
                
                embed.add_field(
                    name="⚙️ Configuración Actual",
                    value=config_text or "No hay configuraciones específicas",
                    inline=False
                )
                
                # Estadísticas de uso del servidor
                guild_usage = 0
                user_count = 0
                
                if guild_id in rate_limiter.user_commands:
                    user_count = len(rate_limiter.user_commands[guild_id])
                    for user_data in rate_limiter.user_commands[guild_id].values():
                        for command_queue in user_data.values():
                            guild_usage += len(command_queue)
                
                embed.add_field(
                    name="📊 Uso del Servidor",
                    value=f"**Usuarios activos:** {user_count}\n**Comandos totales:** {guild_usage}",
                    inline=True
                )
                
            embed.set_footer(text="Rate Limiting System • SCUM Bot")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de rate limiting: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error obteniendo estadísticas: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="rate_limit_reset", description="[ADMIN] Resetear límites de un usuario")
    @app_commands.describe(
        usuario="Usuario cuyos límites resetear",
        comando="Comando específico a resetear (opcional, default: todos)"
    )
    async def rate_limit_reset(self, interaction: discord.Interaction, usuario: discord.User, comando: str = None):
        """Resetear límites de rate limiting de un usuario"""
        
        if not self.is_admin(interaction.user.id):
            embed = discord.Embed(
                title="❌ Acceso Denegado",
                description="Este comando es solo para administradores.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        user_id = str(usuario.id)
        
        try:
            await clear_user_limits(guild_id, user_id, comando)
            
            embed = discord.Embed(
                title="✅ Límites Reseteados",
                description=f"Se han reseteado los límites de **{usuario.display_name}**",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            if comando:
                embed.add_field(
                    name="🎯 Comando Específico",
                    value=f"Solo se reseteó: `/{comando}`",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔄 Reseteo Completo",
                    value="Se resetearon todos los comandos del usuario",
                    inline=False
                )
            
            embed.set_footer(text=f"Ejecutado por {interaction.user.display_name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error reseteando límites: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error reseteando límites: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="rate_limit_test", description="[ADMIN] Probar el sistema de rate limiting")
    async def rate_limit_test(self, interaction: discord.Interaction):
        """Comando de prueba para verificar que el rate limiting funciona"""
        
        if not self.is_admin(interaction.user.id):
            embed = discord.Embed(
                title="❌ Acceso Denegado",
                description="Este comando es solo para administradores.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Manual rate limiting check
        from rate_limiter import rate_limiter
        if not await rate_limiter.check_and_record(interaction, "rate_limit_test"):
            return
        
        embed = discord.Embed(
            title="🧪 Test de Rate Limiting",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🟢 Test Exitoso",
            value="El comando se ejecutó correctamente. El rate limiting está funcionando.",
            inline=False
        )
        
        # Mostrar configuración del comando
        config = rate_limiter.command_limits.get("rate_limit_test", rate_limiter.command_limits['default'])
        embed.add_field(
            name="⚙️ Configuración",
            value=f"""
            **Usuario:** {config['user_rate'][0]} usos / {config['user_rate'][1]}s
            **Servidor:** {config['guild_rate'][0]} usos / {config['guild_rate'][1]}s
            **Cooldown:** {config['cooldown']}s
            """,
            inline=False
        )
        
        embed.set_footer(text="Comando de prueba • Rate Limiting System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RateLimitAdmin(bot))