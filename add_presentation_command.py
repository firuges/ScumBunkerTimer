#!/usr/bin/env python3
"""
Código para agregar al BunkerAdvice_V2.py para mostrar la presentación
"""

# AGREGAR ESTE IMPORT AL INICIO DEL ARCHIVO BunkerAdvice_V2.py
# from bot_presentation import BotPresentationView

# AGREGAR ESTE COMANDO ANTES DE "# === INICIAR BOT ==="

@bot.tree.command(name="bot_presentacion", description="🎉 Ver presentación completa del bot")
async def show_bot_presentation(interaction: discord.Interaction):
    """Mostrar presentación completa del bot con navegación"""
    try:
        await interaction.response.defer()
        
        # Crear la vista de presentación
        view = BotPresentationView()
        embed = view.create_overview_embed()
        
        # Mensaje de introducción
        intro_text = """
🎉 **¡Descubre todo lo que puede hacer nuestro bot!**

Este es el bot más completo para servidores de SCUM. Navega por las **7 páginas** usando los botones de abajo para conocer todas las funcionalidades.

✨ **Lo que encontrarás:**
• 🤖 **Vista General** - Estadísticas y características
• 🚖 **Sistema de Taxi** - 5 vehículos y 20+ zonas  
• 🏦 **Sistema Bancario** - Economía optimizada
• 🏠 **Bunkers** - Monitoreo automático de 4 bunkers
• ⚙️ **Administración** - Panel de control avanzado
• 💎 **Economía** - Mejoras recientes (+58% más rápido)
• 📊 **Estadísticas** - Números y tecnologías

⬇️ **Usa los botones para navegar**
        """
        
        await interaction.followup.send(content=intro_text, embed=embed, view=view)
        
    except Exception as e:
        logger.error(f"Error en presentación: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Hubo un error mostrando la presentación. Intenta nuevamente.",
            color=discord.Color.red()
        )
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)


# TAMBIÉN AGREGAR ESTAS CLASES AL FINAL DEL ARCHIVO (ANTES DE # === INICIAR BOT ===)

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
        
        embed.set_footer(text="Página 1/7 • Usa los botones para navegar")
        
        return embed
    
    # [RESTO DE MÉTODOS AQUÍ - COPIAR DESDE bot_presentation.py]
    # create_taxi_embed, create_banking_embed, etc.


print("=" * 60)
print("INSTRUCCIONES PARA AGREGAR LA PRESENTACIÓN")
print("=" * 60)
print()
print("1. Copia el comando 'bot_presentacion' a BunkerAdvice_V2.py")
print("2. Copia la clase BotPresentationView completa")
print("3. Copia todos los métodos create_*_embed desde bot_presentation.py")
print("4. Reinicia el bot")
print("5. Usa /bot_presentacion en cualquier canal")
print()
print("ALTERNATIVAS MÁS FÁCILES:")
print("- Abre bot_presentation.html en un navegador")
print("- Toma screenshots de la página HTML")
print("- Sube las imágenes a Discord")
print()
print("=" * 60)