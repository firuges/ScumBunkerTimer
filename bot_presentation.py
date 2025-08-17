#!/usr/bin/env python3
"""
Sistema de Presentación del Bot para Discord
Genera embeds profesionales para mostrar todas las funcionalidades
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class BotPresentationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.current_page = 0
        self.pages = [
            self.create_overview_embed,
            self.create_taxi_embed,
            self.create_banking_embed,
            self.create_bunker_embed,
            self.create_admin_embed,
            self.create_economy_embed,
            self.create_stats_embed
        ]
    
    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Página anterior"""
        self.current_page = (self.current_page - 1) % len(self.pages)
        embed = self.pages[self.current_page]()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🏠 Inicio", style=discord.ButtonStyle.primary)
    async def home_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Volver al inicio"""
        self.current_page = 0
        embed = self.pages[self.current_page]()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="▶️ Siguiente", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Página siguiente"""
        self.current_page = (self.current_page + 1) % len(self.pages)
        embed = self.pages[self.current_page]()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❓ Ayuda", style=discord.ButtonStyle.success)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar ayuda rápida"""
        embed = self.create_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def create_overview_embed(self):
        """Página 1: Vista general del bot"""
        embed = discord.Embed(
            title="🤖 SCUM Bunker Timer Bot - Vista General",
            description="**El bot más completo para servidores de SCUM**\n\n*Sistema integrado de gestión de bunkers, taxi, economía y administración*",
            color=0x00ff88
        )
        
        embed.add_field(
            name="🎯 **Funcionalidades Principales**",
            value="""
            🏠 **Sistema de Bunkers** - Monitoreo automático de 4 bunkers
            🚖 **Sistema de Taxi** - Transporte inteligente con múltiples vehículos
            🏦 **Sistema Bancario** - Economía completa con transferencias
            📊 **Monitoreo de Servidores** - Estado en tiempo real
            ⚙️ **Administración Avanzada** - Control total del bot
            """,
            inline=False
        )
        
        embed.add_field(
            name="📈 **Estadísticas del Bot**",
            value="```yaml\nComandos Disponibles: 45+\nSistemas Integrados: 7\nCanales Configurables: 6\nVehículos de Taxi: 5\nZonas del Mapa: 20+```",
            inline=True
        )
        
        embed.add_field(
            name="🚀 **Características Únicas**",
            value="```diff\n+ Persistencia automática\n+ Notificaciones inteligentes\n+ Multi-servidor\n+ Sistema económico balanceado\n+ Interfaz con botones\n+ Actualizaciones en tiempo real```",
            inline=True
        )
        
        embed.add_field(
            name="🎮 **¿Por qué elegir nuestro bot?**",
            value="• **Fácil de usar** - Comandos intuitivos y botones interactivos\n• **Completo** - Todo lo que necesitas en un solo bot\n• **Confiable** - Sistema robusto con respaldos automáticos\n• **Actualizado** - Mejoras constantes y nuevas funciones",
            inline=False
        )
        
        embed.set_footer(text="Página 1/7 • Usa los botones para navegar • /help para comandos")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/placeholder/bot_logo.png")
        
        return embed
    
    def create_taxi_embed(self):
        """Página 2: Sistema de Taxi"""
        embed = discord.Embed(
            title="🚖 Sistema de Taxi Inteligente",
            description="**Transporte completo con múltiples vehículos y zonas del mapa**",
            color=0xffaa00
        )
        
        embed.add_field(
            name="🚗 **Vehículos Disponibles**",
            value="""
            🚗 **Automóvil** - Transporte terrestre estándar (4 pasajeros)
            🏍️ **Motocicleta** - Rápido y ágil (+30% velocidad, 2 pasajeros)
            ✈️ **Avión** - Transporte aéreo (+200% velocidad, requiere pistas)
            🛩️ **Hidroavión** - Aterrizaje en agua (+150% velocidad)
            🚢 **Barco** - Transporte marítimo (4 pasajeros, acceso a islas)
            """,
            inline=False
        )
        
        embed.add_field(
            name="💰 **Economía Optimizada**",
            value="```yaml\nTarifa Base: $15\nPor Kilómetro: $3.50\nComisión Conductor: 85%\nComisión Plataforma: 15%\n\nEjemplo (5km):\nTarifa Total: $32.50\nGanancia Conductor: $27.62```",
            inline=True
        )
        
        embed.add_field(
            name="🗺️ **Zonas del Mapa**",
            value="```diff\n+ Zonas Seguras: Servicio completo\n~ Zonas Neutrales: Servicio normal\n! Zonas de Combate: Solo recogida\n- Zonas Militares: Sin servicio\n\nParadas: 12 ubicaciones\nAeropuertos: 4 pistas\nPuertos: 3 marítimos```",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Comandos de Usuario**",
            value="• `/taxi_solicitar` - Pedir taxi a destino\n• `/taxi_conductor_registro` - Registrarse como conductor\n• `/taxi_conductor_online` - Activar/desactivar servicio\n• `/taxi_zonas` - Ver zonas disponibles\n• `/taxi_balance` - Ver ganancias como conductor",
            inline=False
        )
        
        embed.add_field(
            name="👨‍✈️ **Sistema de Conductores**",
            value="• **Niveles**: Novato → Conductor → Experto → Veterano → Leyenda\n• **Bonificaciones**: Hasta +25% extra por nivel\n• **Calificaciones**: Sistema de reputación\n• **Flexibilidad**: Online/Offline cuando quieras",
            inline=False
        )
        
        embed.set_footer(text="Página 2/7 • Sistema de transporte más avanzado de SCUM")
        
        return embed
    
    def create_banking_embed(self):
        """Página 3: Sistema Bancario"""
        embed = discord.Embed(
            title="🏦 Sistema Bancario Completo",
            description="**Economía avanzada con transferencias, historial y canje diario**",
            color=0x0088ff
        )
        
        embed.add_field(
            name="💳 **Funcionalidades Bancarias**",
            value="""
            💰 **Consultar Saldo** - Balance actual en tiempo real
            💸 **Transferir Dinero** - Envíos seguros entre jugadores
            📊 **Historial Completo** - Todas tus transacciones
            📈 **Estadísticas** - Análisis de tu actividad financiera
            🎁 **Canje Diario** - $500 gratis cada día (¡NUEVO!)
            """,
            inline=False
        )
        
        embed.add_field(
            name="🎁 **Sistema de Ingresos**",
            value="```yaml\nWelcome Bonus: $7,500\nCanje Diario: $500\nVia Taxi (5km): ~$27.62\nVia Transfers: Ilimitado\n\nTiempo a $10K: 5 días\nTiempo a $20K: 25 días\nTiempo a $30K: 45 días```",
            inline=True
        )
        
        embed.add_field(
            name="🛡️ **Seguridad Bancaria**",
            value="```diff\n+ Transacciones registradas\n+ Balance protegido\n+ Historial completo\n+ Anti-fraude activo\n+ Respaldos automáticos\n+ Comisiones transparentes```",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Comandos Bancarios**",
            value="• `/banco_balance` - Ver tu saldo actual\n• `/banco_transferir` - Enviar dinero a usuarios\n• `/banco_historial` - Ver transacciones recientes\n• **Botones interactivos** en el canal bancario",
            inline=False
        )
        
        embed.add_field(
            name="📊 **Progresión Económica Optimizada**",
            value="**Solo canje diario:**\n• $10K en 5 días ⚡\n• $20K en 25 días ⚡\n• $30K en 45 días ⚡\n\n**Con actividad de taxi:**\n• 2-3 viajes/día = 50% menos tiempo\n• 5+ viajes/día = 60% menos tiempo",
            inline=False
        )
        
        embed.set_footer(text="Página 3/7 • Economía optimizada para progresión rápida")
        
        return embed
    
    def create_bunker_embed(self):
        """Página 4: Sistema de Bunkers"""
        embed = discord.Embed(
            title="🏠 Sistema de Bunkers Abandonados",
            description="**Monitoreo automático de los 4 bunkers principales de SCUM**",
            color=0xff6600
        )
        
        embed.add_field(
            name="🗺️ **Bunkers Monitoreados**",
            value="""
            🏠 **Bunker D1** - Zona Noroeste (D1-7)
            🏠 **Bunker C4** - Zona Central (C4-5) 
            🏠 **Bunker A1** - Zona Noreste (A1-9)
            🏠 **Bunker A3** - Zona Sureste (A3-3)
            """,
            inline=False
        )
        
        embed.add_field(
            name="🔔 **Sistema de Alertas**",
            value="```yaml\nEstados Monitoreados:\n🔴 Registrado - Bunker tomado\n🟢 Activo - En uso actualmente\n🟡 Expirado - Disponible\n⚫ No Registrado - Estado unknown\n\nNotificaciones:\n• Cambios de estado\n• Recordatorios de expiración\n• Alertas de disponibilidad```",
            inline=True
        )
        
        embed.add_field(
            name="⏰ **Configuración de Horarios**",
            value="```yaml\nZonas Horarias: Automático\nAlertas Personalizadas:\n• 30 min antes\n• 1 hora antes\n• 2 horas antes\n• 24 horas antes\n\nFrecuencia: Cada 15 minutos```",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Comandos de Bunkers**",
            value="• `/ba_registrar` - Registrar bunker con coordenadas\n• `/ba_status` - Ver estado actual de bunkers\n• `/ba_alertas_config` - Configurar notificaciones\n• `/ba_help` - Ayuda completa del sistema",
            inline=False
        )
        
        embed.add_field(
            name="📱 **Características Avanzadas**",
            value="• **Auto-detección** de zona horaria por servidor\n• **Recordatorios inteligentes** antes de expiración\n• **Historial completo** de actividad de bunkers\n• **Panel en tiempo real** con estado actualizado\n• **Multi-servidor** - Cada guild independiente",
            inline=False
        )
        
        embed.set_footer(text="Página 4/7 • Nunca pierdas un bunker por falta de tiempo")
        
        return embed
    
    def create_admin_embed(self):
        """Página 5: Panel de Administración"""
        embed = discord.Embed(
            title="⚙️ Panel de Administración Avanzado",
            description="**Control total del bot con herramientas profesionales**",
            color=0x8800ff
        )
        
        embed.add_field(
            name="🛠️ **Configuración de Canales**",
            value="""
            🚖 `/taxi_admin_setup` - Configurar canal de taxi
            🏦 `/banco_admin_setup` - Configurar canal bancario
            🎉 `/welcome_admin_setup` - Configurar registro
            🛒 `/shop_admin_setup` - Configurar tienda
            📊 `/ba_admin_setup_status` - Estado del bot (admin)
            📢 `/ba_admin_public_status` - Estado público
            """,
            inline=False
        )
        
        embed.add_field(
            name="👑 **Comandos de Super Admin**",
            value="```yaml\nGestión de Suscripciones:\n• /ba_admin_status - Ver suscripción\n• /ba_admin_upgrade - Dar premium\n• /ba_admin_cancel - Quitar premium\n• /ba_admin_list - Listar todos\n\nMantenimiento:\n• /ba_admin_resync - Sincronizar comandos\n• /ba_admin_shutdown - Apagar seguro\n• /ba_admin_guide - Obtener documentación```",
            inline=True
        )
        
        embed.add_field(
            name="🔧 **Herramientas de Debug**",
            value="```yaml\nDiagnóstico:\n• /ba_admin_debug_channels\n• /ba_admin_fix_channels\n• Logs automáticos\n• Reportes de errores\n\nMonitoreo:\n• Estado de conexión\n• Uso de recursos\n• Estadísticas en tiempo real```",
            inline=True
        )
        
        embed.add_field(
            name="🎛️ **Configuración Avanzada**",
            value="• **Persistencia automática** - Configuraciones se guardan\n• **Auto-recreación** - Paneles se restauran al reiniciar\n• **Multi-servidor** - Configuración independiente\n• **Permisos granulares** - Control de acceso detallado\n• **Notificaciones de estado** - Alertas de conexión/desconexión",
            inline=False
        )
        
        embed.add_field(
            name="📊 **Panel de Estado en Tiempo Real**",
            value="**Canal Admin:** Información técnica completa\n**Canal Público:** Estado simplificado para usuarios\n• Uptime del bot\n• Servidores conectados\n• Estado de bunkers globales\n• Top servidores SCUM\n• Estadísticas de uso",
            inline=False
        )
        
        embed.set_footer(text="Página 5/7 • Control profesional con herramientas avanzadas")
        
        return embed
    
    def create_economy_embed(self):
        """Página 6: Economía del Servidor"""
        embed = discord.Embed(
            title="💎 Economía Optimizada del Servidor",
            description="**Sistema económico balanceado para progresión satisfactoria**",
            color=0x00cc88
        )
        
        embed.add_field(
            name="🚀 **Mejoras Recientes (¡NUEVO!)**",
            value="""
            ✨ **Welcome Bonus**: $5,000 → $7,500 (+50%)
            ✨ **Canje Diario**: $250 → $500 (+100%)
            ✨ **Comisión Conductor**: 75% → 85% (+10%)
            """,
            inline=False
        )
        
        embed.add_field(
            name="📈 **Comparativa de Tiempos**",
            value="```yaml\nObjetivo $10,000:\nAntes: 20 días\nAhora: 5 días (-75%)\n\nObjetivo $20,000:\nAntes: 60 días\nAhora: 25 días (-58%)\n\nObjetivo $30,000:\nAntes: 100 días\nAhora: 45 días (-55%)```",
            inline=True
        )
        
        embed.add_field(
            name="💰 **Fuentes de Ingresos**",
            value="```yaml\nPasivo:\n• Welcome Pack: $7,500\n• Canje Diario: $500/día\n\nActivo:\n• Taxi 1km: ~$13.88\n• Taxi 5km: ~$27.62\n• Taxi 10km: ~$48.75\n• Taxi 20km: ~$81.25```",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Objetivos Realistas**",
            value="**Para usuarios casuales (solo canje):**\n• 🥉 $10K - 1 semana\n• 🥈 $20K - 3-4 semanas\n• 🥇 $30K - 6-7 semanas\n\n**Para usuarios activos (2-3 viajes/día):**\n• 🥉 $10K - 3-4 días\n• 🥈 $20K - 2-3 semanas\n• 🥇 $30K - 4-5 semanas",
            inline=False
        )
        
        embed.add_field(
            name="🎮 **Incentivos de Actividad**",
            value="• **Sistema de niveles** para conductores\n• **Bonificaciones** por experiencia (+5% a +25%)\n• **Canje diario** recompensa la constancia\n• **Multiple vehículos** para variedad\n• **Zonas especiales** con tarifas premium",
            inline=False
        )
        
        embed.set_footer(text="Página 6/7 • Economía balanceada para todos los tipos de jugadores")
        
        return embed
    
    def create_stats_embed(self):
        """Página 7: Estadísticas y Características"""
        embed = discord.Embed(
            title="📊 Estadísticas y Características Técnicas",
            description="**Números que demuestran la calidad y robustez del sistema**",
            color=0xff0088
        )
        
        embed.add_field(
            name="🔢 **Estadísticas del Bot**",
            value="```yaml\nComandos Totales: 45+\nComandos de Usuario: 25+\nComandos de Admin: 20+\nSistemas Integrados: 7\nCanales Configurables: 6\nVehículos de Taxi: 5\nZonas del Mapa: 20+\nBunkers Monitoreados: 4```",
            inline=True
        )
        
        embed.add_field(
            name="⚡ **Rendimiento**",
            value="```yaml\nUptime Promedio: 99.9%\nTiempo de Respuesta: <200ms\nBase de Datos: SQLite\nActualizaciones: Automáticas\nRespaldos: Diarios\nNotificaciones: Tiempo real\nRestart: Transparente```",
            inline=True
        )
        
        embed.add_field(
            name="🚀 **Características Únicas**",
            value="""
            🔄 **Persistencia Total** - Nada se pierde al reiniciar
            🤖 **Notificaciones Inteligentes** - Conexión/desconexión
            🌐 **Multi-servidor** - Configuración independiente
            🎨 **Interfaz Moderna** - Botones y embeds interactivos
            📱 **Responsive** - Funciona en mobile y desktop
            🛡️ **Seguro** - Validaciones y protecciones
            """,
            inline=False
        )
        
        embed.add_field(
            name="🔧 **Tecnologías Utilizadas**",
            value="• **Discord.py** - Framework moderno\n• **AsyncIO** - Programación asíncrona\n• **SQLite** - Base de datos robusta\n• **aiohttp** - Servidor web integrado\n• **datetime** - Manejo inteligente de tiempo\n• **Logging** - Sistema de logs completo",
            inline=False
        )
        
        embed.add_field(
            name="📈 **Futuras Actualizaciones**",
            value="🔮 **En desarrollo:**\n• Sistema de misiones\n• Tienda expandida\n• Clanes y grupos\n• Estadísticas avanzadas\n• Integración con APIs externas\n• Dashboard web",
            inline=False
        )
        
        embed.set_footer(text="Página 7/7 • Bot profesional en constante evolución")
        
        return embed
    
    def create_help_embed(self):
        """Embed de ayuda rápida"""
        embed = discord.Embed(
            title="❓ Ayuda Rápida",
            description="**Comandos principales para empezar**",
            color=0x00ffff
        )
        
        embed.add_field(
            name="🚀 **Primeros Pasos**",
            value="• `/welcome_registro` - Registrarte y recibir $7,500\n• `/banco_balance` - Ver tu dinero\n• `/taxi_solicitar` - Pedir tu primer taxi",
            inline=False
        )
        
        embed.add_field(
            name="👨‍✈️ **Ser Conductor**",
            value="• `/taxi_conductor_registro` - Registrarte como conductor\n• `/taxi_conductor_online` - Activar servicio\n• Gana hasta $90 por viaje largo",
            inline=False
        )
        
        embed.add_field(
            name="🏠 **Bunkers**",
            value="• `/ba_registrar` - Registrar bunker\n• `/ba_status` - Ver estado actual\n• `/ba_alertas_config` - Configurar notificaciones",
            inline=False
        )
        
        embed.set_footer(text="Usa /help [comando] para ayuda específica")
        
        return embed

# Comando para mostrar la presentación
async def show_presentation(channel):
    """Mostrar la presentación completa del bot"""
    view = BotPresentationView()
    embed = view.create_overview_embed()
    
    # Mensaje inicial
    intro_text = """
🎉 **¡Conoce todas las funcionalidades de nuestro bot!**

Este es el bot más completo para servidores de SCUM. Navega por las páginas usando los botones de abajo para descubrir todo lo que puede hacer por tu servidor.

✨ **¿Por qué elegir nuestro bot?**
• **7 sistemas integrados** en una sola herramienta
• **45+ comandos** para todas las necesidades
• **Economía optimizada** para progresión rápida
• **Interfaz moderna** con botones interactivos
• **Soporte 24/7** y actualizaciones constantes

⬇️ **Usa los botones para navegar por la presentación**
    """
    
    message = await channel.send(content=intro_text, embed=embed, view=view)
    return message

if __name__ == "__main__":
    print("Presentación del bot creada.")
    print("Para usar:")
    print("1. Importa este archivo en tu bot principal")
    print("2. Llama a show_presentation(channel) en el canal deseado")
    print("3. Los usuarios podrán navegar con los botones")