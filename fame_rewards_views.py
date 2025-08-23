#!/usr/bin/env python3
"""
Vistas de Discord UI para Fame Point Rewards
Maneja botones, selectors y modales para el sistema de fama
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from typing import List, Dict
from core.user_manager import get_user_by_discord_id

logger = logging.getLogger(__name__)

class FameRewardsView(discord.ui.View):
    """Vista principal del panel de Fame Point Rewards"""
    
    def __init__(self, fame_system, fame_values: List[int]):
        super().__init__(timeout=None)
        self.fame_system = fame_system
        self.fame_values = fame_values
        self.message = None
        
        # Crear selector con los valores de fama configurables
        self.add_item(FameAmountSelect(fame_values))
        
    @discord.ui.button(label="Gestión Avanzada", style=discord.ButtonStyle.danger, emoji="⚙️", row=1)
    async def advanced_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Gestión avanzada de Fame Points (Solo Admin)"""
        
        # Verificar si es admin
        is_admin = any(role.permissions.administrator for role in interaction.user.roles)
        
        if not is_admin:
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden acceder a la gestión avanzada.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Obtener valores actuales de fama configurados
            fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
            rewards_config = await self.fame_system.get_rewards_config(str(interaction.guild.id))
            
            # Mostrar vista elegante con selector intuitivo
            await interaction.response.defer(ephemeral=True)
            
            embed = discord.Embed(
                title="⚙️ Gestión Avanzada de Fame Points",
                description="**Niveles actuales configurados:**\n\n",
                color=0xFF6B35  # Color naranja para gestión
            )
            
            # Mostrar niveles actuales
            levels_text = ""
            for fame_amount in sorted(fame_values):
                reward_desc = rewards_config.get(str(fame_amount), "Sin premio configurado")
                levels_text += f"• **{fame_amount:,} FP** → {reward_desc[:60]}{'...' if len(reward_desc) > 60 else ''}\n"
            
            embed.description = f"**Niveles actuales configurados:**\n\n{levels_text}"
            embed.add_field(
                name="🎯 Acciones Disponibles",
                value="• **Seleccionar nivel existente** → Editar o Eliminar\n• **'➕ Crear Nuevo'** → Agregar nuevo nivel",
                inline=False
            )
            embed.set_footer(text=f"Total: {len(fame_values)} niveles configurados")
            
            # Vista con selector intuitivo
            view = AdvancedManagementView(self.fame_system, fame_values, rewards_config)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en gestión avanzada: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo cargar la gestión avanzada.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Ver Premios", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def view_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mostrar premios disponibles por Fame Points"""
        
        try:
            # Verificar si es admin para poder configurar premios
            is_admin = any(role.permissions.administrator for role in interaction.user.roles)
            
            # Obtener configuración actual de premios (si existe)
            rewards_config = await self.fame_system.get_rewards_config(str(interaction.guild.id))
            
            if is_admin:
                # Admin: Mostrar vista elegante directamente (NO modal)
                await interaction.response.defer(ephemeral=True)
                
                # Obtener valores de fama configurados
                fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
                
                # Crear embed elegante con premios actuales
                embed = discord.Embed(
                    title="✨ Sistema de Premios Fame Points",
                    description="**Premios actualmente configurados:**\n\n",
                    color=0xFFD700  # Color dorado elegante
                )
                
                # Mostrar cada premio de forma elegante
                description_text = ""
                for i, fame_amount in enumerate(sorted(fame_values)):
                    reward_desc = rewards_config.get(str(fame_amount), f"🎁 Premio por {fame_amount:,} Fame Points")
                    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
                    description_text += f"{medal} **{fame_amount:,} FP** → {reward_desc}\n"
                
                embed.description = f"**Premios actualmente configurados:**\n\n{description_text}"
                embed.add_field(
                    name="⚙️ Gestión", 
                    value="Usa el selector de abajo para editar un premio específico.",
                    inline=False
                )
                embed.set_footer(text=f"Total: {len(fame_values)} premios • Sistema SCUM Fame Rewards")
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2583/2583329.png")
                
                # Crear vista con selector elegante
                view = SimpleRewardEditView(self.fame_system, fame_values, rewards_config)
                
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                # Usuario normal: defer y mostrar premios
                await interaction.response.defer(ephemeral=True)
                # Usuario normal: Mostrar premios disponibles
                embed = discord.Embed(
                    title="🏆 Premios por Fame Points",
                    description="Estos son los premios disponibles según tus puntos de fama:",
                    color=discord.Color.gold()
                )
                
                # Obtener valores de fama configurados
                fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
                
                for fame_amount in sorted(fame_values):
                    reward_desc = rewards_config.get(str(fame_amount), f"Premio por {fame_amount:,} Fame Points")
                    embed.add_field(
                        name=f"🏅 {fame_amount:,} Fame Points",
                        value=reward_desc,
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Cómo Reclamar",
                    value="Usa el selector de arriba para elegir la cantidad de Fame Points que tienes y reclama tu premio.",
                    inline=False
                )
                
                embed.set_footer(text=f"Premios configurados para {interaction.guild.name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error mostrando premios: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo cargar la información de premios.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class RewardsConfigModal(discord.ui.Modal, title="🏆 Configurar Premios por Fame Points"):
    """Modal para que admins configuren los premios"""
    
    def __init__(self, fame_system, current_config: dict):
        super().__init__()
        self.fame_system = fame_system
        self.current_config = current_config
    
    rewards_config = discord.ui.TextInput(
        label="Configuración de Premios",
        placeholder="100=Kit de Inicio, 500=Set de Armadura, 1000=Vehículo Premium...",
        required=True,
        max_length=2000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar configuración de premios"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parsear configuración del admin
            rewards_dict = {}
            config_lines = self.rewards_config.value.split(',')
            
            for line in config_lines:
                line = line.strip()
                if '=' in line:
                    try:
                        fame_str, reward_desc = line.split('=', 1)
                        fame_amount = int(fame_str.strip())
                        reward_desc = reward_desc.strip()
                        rewards_dict[str(fame_amount)] = reward_desc
                    except ValueError:
                        continue
            
            if not rewards_dict:
                embed = discord.Embed(
                    title="❌ Formato Incorrecto",
                    description="No se pudo parsear la configuración. Usa el formato:\n`100=Kit de Inicio, 500=Set de Armadura`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Guardar configuración
            success = await self.fame_system.save_rewards_config(str(interaction.guild.id), rewards_dict)
            
            if success:
                embed = discord.Embed(
                    title="✅ Premios Configurados",
                    description=f"Se han configurado premios para {len(rewards_dict)} niveles de Fame Points.",
                    color=discord.Color.green()
                )
                
                # Mostrar configuración guardada
                for fame_amount, reward in sorted(rewards_dict.items(), key=lambda x: int(x[0])):
                    embed.add_field(
                        name=f"🏅 {int(fame_amount):,} FP",
                        value=reward,
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo guardar la configuración de premios.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error configurando premios: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al configurar los premios.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class EnhancedRewardsViewModal(discord.ui.Modal, title="🏆 Ver y Configurar Premios"):
    """Modal simple para que admins vean premios actuales"""
    
    def __init__(self, fame_system, current_config: dict):
        super().__init__()
        self.fame_system = fame_system
        self.current_config = current_config
    
    async def on_submit(self, interaction: discord.Interaction):
        """Mostrar vista elegante de premios con selector para editar"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener valores de fama configurados
            fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
            
            # Crear embed elegante con premios actuales
            embed = discord.Embed(
                title="✨ Sistema de Premios Fame Points",
                description="**Premios actualmente configurados:**\n\n",
                color=0xFFD700  # Color dorado elegante
            )
            
            # Mostrar cada premio de forma elegante
            description_text = ""
            for i, fame_amount in enumerate(sorted(fame_values)):
                reward_desc = self.current_config.get(str(fame_amount), f"🎁 Premio por {fame_amount:,} Fame Points")
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
                description_text += f"{medal} **{fame_amount:,} FP** → {reward_desc}\n"
            
            embed.description = f"**Premios actualmente configurados:**\n\n{description_text}"
            embed.add_field(
                name="⚙️ Gestión", 
                value="Usa el selector de abajo para editar un premio específico.",
                inline=False
            )
            embed.set_footer(text=f"Total: {len(fame_values)} premios • Sistema SCUM Fame Rewards")
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2583/2583329.png")
            
            # Crear vista con selector elegante
            view = SimpleRewardEditView(self.fame_system, fame_values, self.current_config)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error mostrando premios: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo cargar los premios.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class SimpleRewardEditView(discord.ui.View):
    """Vista elegante con selector simple para editar premios"""
    
    def __init__(self, fame_system, fame_values: List[int], current_config: dict):
        super().__init__(timeout=300)
        self.fame_system = fame_system
        self.fame_values = sorted(fame_values)
        self.current_config = current_config
        
        # Agregar selector simple
        self.add_item(RewardEditSelect(fame_values, current_config, fame_system))
    
class RewardEditSelect(discord.ui.Select):
    """Selector elegante para elegir qué premio editar"""
    
    def __init__(self, fame_values: List[int], current_config: dict, fame_system):
        self.fame_system = fame_system
        self.current_config = current_config
        
        options = []
        # Limitar a máximo 25 opciones (límite de Discord)
        limited_fame_values = sorted(fame_values)[:25]
        
        for fame_amount in limited_fame_values:
            reward_preview = current_config.get(str(fame_amount), "Sin configurar")[:50]
            if len(reward_preview) == 50:
                reward_preview += "..."
                
            options.append(
                discord.SelectOption(
                    label=f"{fame_amount:,} Fame Points",
                    value=str(fame_amount),
                    description=reward_preview,
                    emoji="🏅"
                )
            )
        
        super().__init__(
            placeholder="🎯 Selecciona el premio que quieres editar...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Abrir modal simple para editar el premio seleccionado"""
        fame_amount = int(self.values[0])
        current_reward = self.current_config.get(str(fame_amount), f"🎁 Premio por {fame_amount:,} Fame Points")
        
        # Modal simple para editar UN premio
        modal = SingleRewardEditModal(self.fame_system, fame_amount, current_reward)
        await interaction.response.send_modal(modal)

class SingleRewardEditModal(discord.ui.Modal, title="✏️ Editar Premio"):
    """Modal simple para editar un solo premio"""
    
    def __init__(self, fame_system, fame_amount: int, current_reward: str):
        super().__init__()
        self.fame_system = fame_system
        self.fame_amount = fame_amount
        self.title = f"✏️ Editar Premio {fame_amount:,} FP"
        
        # Campo de texto con valor actual pre-llenado
        self.reward_description = discord.ui.TextInput(
            label="Descripción del Premio",
            placeholder="Ej: 🎒 Kit de Supervivencia Completo + Armas",
            default=current_reward,
            required=True,
            max_length=200,
            style=discord.TextStyle.short
        )
        self.add_item(self.reward_description)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Guardar el premio editado"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Obtener configuración actual completa
            current_config = await self.fame_system.get_rewards_config(str(interaction.guild.id))
            
            # Actualizar solo el premio editado
            current_config[str(self.fame_amount)] = self.reward_description.value
            
            # Guardar configuración actualizada
            success = await self.fame_system.save_rewards_config(str(interaction.guild.id), current_config)
            
            if success:
                # Respuesta elegante
                embed = discord.Embed(
                    title="✅ Premio Actualizado",
                    description=f"**{self.fame_amount:,} Fame Points**\n\n{self.reward_description.value}",
                    color=0x00FF7F  # Verde elegante
                )
                embed.add_field(
                    name="✨ Estado",
                    value="Premio actualizado exitosamente",
                    inline=True
                )
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/845/845646.png")
                embed.set_footer(text="Sistema Fame Rewards • Actualización completada")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Actualizar panel principal
                await self.fame_system.update_fame_rewards_panel(str(interaction.guild.id))
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo guardar el premio.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error editando premio individual: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al guardar el premio.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

# La clase anterior ha sido reemplazada por SingleRewardEditModal más arriba

class AdvancedManagementView(discord.ui.View):
    """Vista intuitiva para gestión avanzada"""
    
    def __init__(self, fame_system, fame_values: List[int], rewards_config: dict):
        super().__init__(timeout=300)
        self.fame_system = fame_system
        self.fame_values = sorted(fame_values)
        self.rewards_config = rewards_config
        
        # Agregar selector intuitivo
        self.add_item(AdvancedManagementSelect(fame_values, rewards_config, fame_system))

class AdvancedManagementSelect(discord.ui.Select):
    """Selector intuitivo para gestión avanzada"""
    
    def __init__(self, fame_values: List[int], rewards_config: dict, fame_system):
        self.fame_system = fame_system
        self.rewards_config = rewards_config
        
        options = []
        
        # Opción especial para crear nuevo
        options.append(
            discord.SelectOption(
                label="➕ Crear Nuevo Nivel",
                value="CREATE_NEW",
                description="Agregar un nuevo nivel de Fame Points",
                emoji="➕"
            )
        )
        
        # Niveles existentes (máximo 24 para dejar espacio al "Crear Nuevo")
        limited_fame_values = sorted(fame_values)[:24]
        
        for fame_amount in limited_fame_values:
            reward_preview = rewards_config.get(str(fame_amount), "Sin premio")[:40]
            options.append(
                discord.SelectOption(
                    label=f"{fame_amount:,} Fame Points",
                    value=f"EDIT_{fame_amount}",
                    description=f"Editar/Eliminar: {reward_preview}",
                    emoji="🎯"
                )
            )
        
        super().__init__(
            placeholder="🎯 Selecciona una acción...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Manejar selección de gestión avanzada"""
        selection = self.values[0]
        
        if selection == "CREATE_NEW":
            # Crear nuevo nivel
            modal = CreateNewLevelModal(self.fame_system)
            await interaction.response.send_modal(modal)
        
        elif selection.startswith("EDIT_"):
            # Editar nivel existente
            fame_amount = int(selection.replace("EDIT_", ""))
            current_reward = self.rewards_config.get(str(fame_amount), "Sin premio configurado")
            
            # Mostrar botones de Editar/Eliminar
            view = EditOrDeleteView(self.fame_system, fame_amount, current_reward)
            
            embed = discord.Embed(
                title=f"✏️ Gestionar {fame_amount:,} Fame Points",
                description=f"**Premio actual:**\n{current_reward}\n\n**¿Qué deseas hacer?**",
                color=0x4169E1  # Azul para edición
            )
            embed.set_footer(text="Selecciona una acción con los botones de abajo")
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CreateNewLevelModal(discord.ui.Modal, title="➕ Crear Nuevo Nivel"):
    """Modal para crear un nuevo nivel de Fame Points"""
    
    def __init__(self, fame_system):
        super().__init__()
        self.fame_system = fame_system
    
    fame_amount_input = discord.ui.TextInput(
        label="Cantidad de Fame Points",
        placeholder="Ej: 750, 1500, 25000",
        required=True,
        max_length=10,
        style=discord.TextStyle.short
    )
    
    reward_input = discord.ui.TextInput(
        label="Premio/Recompensa",
        placeholder="Ej: 🏰 Base Fortificada Premium + Vehículos",
        required=True,
        max_length=200,
        style=discord.TextStyle.short
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Crear nuevo nivel de Fame Points"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar cantidad
            try:
                new_fame_amount = int(self.fame_amount_input.value.strip())
                if new_fame_amount <= 0:
                    raise ValueError("La cantidad debe ser positiva")
            except ValueError:
                embed = discord.Embed(
                    title="❌ Cantidad Inválida",
                    description="La cantidad de Fame Points debe ser un número positivo válido.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar que no existe
            current_fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
            
            if new_fame_amount in current_fame_values:
                embed = discord.Embed(
                    title="⚠️ Nivel ya existe",
                    description=f"Ya existe un nivel con **{new_fame_amount:,} Fame Points**.\n\nUsa la gestión normal para editarlo.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verificar límite de Discord (25 niveles máximo)
            if len(current_fame_values) >= 25:
                embed = discord.Embed(
                    title="🚫 Límite Alcanzado",
                    description="Ya tienes el máximo de 25 niveles configurados (límite de Discord).\n\nElimina algunos niveles primero.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Agregar nuevo nivel
            new_fame_values = sorted(current_fame_values + [new_fame_amount])
            await self.fame_system.fame_db.set_fame_config(str(interaction.guild.id), new_fame_values)
            
            # Agregar premio
            current_rewards = await self.fame_system.get_rewards_config(str(interaction.guild.id))
            current_rewards[str(new_fame_amount)] = self.reward_input.value
            await self.fame_system.save_rewards_config(str(interaction.guild.id), current_rewards)
            
            # Actualizar panel principal
            await self.fame_system.update_fame_rewards_panel(str(interaction.guild.id))
            
            # Confirmar
            embed = discord.Embed(
                title="✅ Nuevo Nivel Creado",
                description=f"**{new_fame_amount:,} Fame Points**\n\n{self.reward_input.value}",
                color=0x32CD32  # Verde lima
            )
            embed.add_field(
                name="📊 Estado",
                value=f"Total de niveles: {len(new_fame_values)}",
                inline=True
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/190/190411.png")
            embed.set_footer(text="Nuevo nivel agregado exitosamente")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error creando nuevo nivel: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al crear el nuevo nivel.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class EditOrDeleteView(discord.ui.View):
    """Vista con botones para Editar o Eliminar un nivel"""
    
    def __init__(self, fame_system, fame_amount: int, current_reward: str):
        super().__init__(timeout=60)
        self.fame_system = fame_system
        self.fame_amount = fame_amount
        self.current_reward = current_reward
    
    @discord.ui.button(label="✏️ Editar Premio", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Editar premio del nivel"""
        modal = SingleRewardEditModal(self.fame_system, self.fame_amount, self.current_reward)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🗑️ Eliminar Nivel", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Eliminar nivel completo"""
        
        # Confirmación
        embed = discord.Embed(
            title="⚠️ Confirmar Eliminación",
            description=f"¿Estás seguro de que quieres **eliminar completamente** el nivel de **{self.fame_amount:,} Fame Points**?\n\n**Premio actual:**\n{self.current_reward}\n\n**⚠️ Esta acción no se puede deshacer.**",
            color=discord.Color.red()
        )
        
        view = ConfirmDeleteView(self.fame_system, self.fame_amount)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmDeleteView(discord.ui.View):
    """Vista de confirmación para eliminar nivel"""
    
    def __init__(self, fame_system, fame_amount: int):
        super().__init__(timeout=30)
        self.fame_system = fame_system
        self.fame_amount = fame_amount
    
    @discord.ui.button(label="🗑️ Sí, Eliminar", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar eliminación del nivel"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Eliminar de la configuración de Fame Points
            current_fame_values = await self.fame_system.fame_db.get_fame_config(str(interaction.guild.id))
            if self.fame_amount in current_fame_values:
                current_fame_values.remove(self.fame_amount)
                await self.fame_system.fame_db.set_fame_config(str(interaction.guild.id), current_fame_values)
            
            # Eliminar premio asociado
            current_rewards = await self.fame_system.get_rewards_config(str(interaction.guild.id))
            if str(self.fame_amount) in current_rewards:
                del current_rewards[str(self.fame_amount)]
                await self.fame_system.save_rewards_config(str(interaction.guild.id), current_rewards)
            
            # Actualizar panel principal
            await self.fame_system.update_fame_rewards_panel(str(interaction.guild.id))
            
            # Deshabilitar botones
            for item in self.children:
                item.disabled = True
            try:
                await interaction.edit_original_response(view=self)
            except:
                pass
            
            # Confirmar eliminación
            embed = discord.Embed(
                title="🗑️ Nivel Eliminado",
                description=f"El nivel de **{self.fame_amount:,} Fame Points** ha sido eliminado completamente.",
                color=0x808080  # Gris
            )
            embed.add_field(
                name="📊 Estado",
                value=f"Niveles restantes: {len(current_fame_values)}",
                inline=True
            )
            embed.set_footer(text="Eliminación completada")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error eliminando nivel: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al eliminar el nivel.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancelar eliminación"""
        embed = discord.Embed(
            title="✅ Eliminación Cancelada",
            description="El nivel no ha sido eliminado.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Deshabilitar botones
        for item in self.children:
            item.disabled = True
        try:
            await interaction.edit_original_response(view=self)
        except:
            pass

# Mantener modal complejo como fallback (pero oculto)
class AdvancedFameManagementModal(discord.ui.Modal, title="⚙️ Gestión Avanzada de Fame Points"):
    """Modal para gestión avanzada: agregar, editar, eliminar valores de Fame Points"""
    
    def __init__(self, fame_system, current_fame_values: List[int], current_rewards_config: dict):
        super().__init__()
        self.fame_system = fame_system
        self.current_fame_values = sorted(current_fame_values)
        self.current_rewards_config = current_rewards_config
    
    fame_values_input = discord.ui.TextInput(
        label="Valores de Fame Points",
        placeholder="100,400,500,1000,2000,5000,10000,15000",
        required=True,
        max_length=500,
        style=discord.TextStyle.short
    )
    
    management_action = discord.ui.TextInput(
        label="Acción a Realizar",
        placeholder="AGREGAR 450,750 | ELIMINAR 400 | EDITAR 500->600 | REEMPLAZAR (usar valores de arriba)",
        required=True,
        max_length=200,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar gestión avanzada de Fame Points"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            action = self.management_action.value.strip().upper()
            new_fame_values = list(self.current_fame_values)  # Copia de valores actuales
            
            # Parsear valores de entrada
            input_values = []
            for val_str in self.fame_values_input.value.split(','):
                val_str = val_str.strip()
                try:
                    input_values.append(int(val_str))
                except ValueError:
                    continue
            
            changes_made = []
            
            if action.startswith('AGREGAR'):
                # Agregar nuevos valores
                action_values = action.replace('AGREGAR', '').strip()
                if action_values:
                    add_values = [int(x.strip()) for x in action_values.split(',') if x.strip().isdigit()]
                else:
                    add_values = input_values
                
                for val in add_values:
                    if val not in new_fame_values and val > 0:
                        new_fame_values.append(val)
                        changes_made.append(f"+ {val:,}")
            
            elif action.startswith('ELIMINAR'):
                # Eliminar valores existentes
                action_values = action.replace('ELIMINAR', '').strip()
                if action_values:
                    remove_values = [int(x.strip()) for x in action_values.split(',') if x.strip().isdigit()]
                else:
                    remove_values = input_values
                
                for val in remove_values:
                    if val in new_fame_values:
                        new_fame_values.remove(val)
                        changes_made.append(f"- {val:,}")
                        
                        # También eliminar premio asociado
                        if str(val) in self.current_rewards_config:
                            del self.current_rewards_config[str(val)]
            
            elif action.startswith('EDITAR'):
                # Editar valor existente (cambiar un valor por otro)
                edit_part = action.replace('EDITAR', '').strip()
                if '->' in edit_part:
                    old_val, new_val = edit_part.split('->')
                    try:
                        old_val = int(old_val.strip())
                        new_val = int(new_val.strip())
                        
                        if old_val in new_fame_values:
                            # Reemplazar valor
                            index = new_fame_values.index(old_val)
                            new_fame_values[index] = new_val
                            changes_made.append(f"{old_val:,} → {new_val:,}")
                            
                            # Transferir premio si existe
                            if str(old_val) in self.current_rewards_config:
                                self.current_rewards_config[str(new_val)] = self.current_rewards_config[str(old_val)]
                                del self.current_rewards_config[str(old_val)]
                    except ValueError:
                        pass
            
            elif action == 'REEMPLAZAR':
                # Reemplazar todos los valores
                new_fame_values = [val for val in input_values if val > 0]
                changes_made.append(f"Configuración completamente reemplazada")
            
            if not changes_made:
                embed = discord.Embed(
                    title="⚠️ Sin cambios",
                    description="No se realizaron cambios. Verifica tu acción y valores.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Validaciones
            if len(new_fame_values) == 0:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No puedes eliminar todos los valores de Fame Points.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            if len(new_fame_values) > 25:
                embed = discord.Embed(
                    title="❌ Demasiados valores",
                    description="Máximo 25 valores de Fame Points permitidos (limitación de Discord).",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Ordenar y remover duplicados
            new_fame_values = sorted(list(set(new_fame_values)))
            
            # Guardar nueva configuración
            await self.fame_system.fame_db.set_fame_config(str(interaction.guild.id), new_fame_values)
            await self.fame_system.save_rewards_config(str(interaction.guild.id), self.current_rewards_config)
            
            # Actualizar panel
            await self.fame_system.update_fame_rewards_panel(str(interaction.guild.id))
            
            # Confirmar cambios
            embed = discord.Embed(
                title="✅ Gestión Exitosa",
                description=f"Se han aplicado los cambios a la configuración de Fame Points.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📝 Cambios realizados",
                value="\n".join(changes_made[:10]),  # Limitar para no exceder límites
                inline=False
            )
            
            embed.add_field(
                name="📊 Nueva configuración",
                value=f"Valores: {', '.join([f'{v:,}' for v in new_fame_values[:10]])}{'...' if len(new_fame_values) > 10 else ''}",
                inline=False
            )
            
            embed.set_footer(text=f"Total: {len(new_fame_values)} valores configurados")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error en gestión avanzada de Fame Points: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al procesar la gestión avanzada.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class FameAmountSelect(discord.ui.Select):
    """Selector para elegir cantidad de fama a reclamar"""
    
    def __init__(self, fame_values: List[int]):
        options = []
        for value in fame_values:
            # Formatear el valor con separadores de miles
            formatted_value = f"{value:,}"
            options.append(
                discord.SelectOption(
                    label=f"🏆 {formatted_value} Fame Points",
                    value=str(value),
                    description=f"Reclamar premio de {formatted_value} puntos de fama",
                    emoji="⭐"
                )
            )
        
        super().__init__(
            placeholder="🏆 Selecciona la cantidad de fama a reclamar...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona una cantidad de fama"""
        fame_amount = int(self.values[0])
        
        try:
            # Verificar si el usuario está registrado
            user_data = await get_user_by_discord_id(str(interaction.user.id), str(interaction.guild.id))
            
            if not user_data:
                embed = discord.Embed(
                    title="❌ Usuario No Registrado",
                    description="Debes registrarte en el sistema primero usando `/welcome_registro`",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya tiene una reclamación pendiente
            has_pending = await self.view.fame_system.fame_db.has_pending_claim(
                str(user_data['user_id']), str(interaction.guild.id)
            )
            
            if has_pending:
                embed = discord.Embed(
                    title="⏳ Reclamación Pendiente",
                    description="Ya tienes una reclamación de fama pendiente. Espera a que sea procesada antes de hacer otra.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Verificar si ya reclamó esta cantidad específica de fama
            has_claimed_amount = await self.view.fame_system.fame_db.has_claimed_fame_amount(
                str(user_data['user_id']), str(interaction.guild.id), fame_amount
            )
            
            if has_claimed_amount:
                embed = discord.Embed(
                    title="🚫 Ya Reclamado",
                    description=f"Ya has reclamado y obtenido el premio de **{fame_amount:,} Fame Points** anteriormente. No puedes reclamar la misma cantidad de fama dos veces.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Mostrar modal de confirmación
            modal = FameClaimModal(self.view.fame_system, fame_amount, user_data)
            await interaction.response.send_modal(modal)
            
            # Nota: Discord maneja automáticamente la re-selección del selector
            
        except Exception as e:
            logger.error(f"Error en callback de FameAmountSelect: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al procesar tu solicitud.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class FameClaimModal(discord.ui.Modal, title="🏆 Reclamar Premio de Fama"):
    """Modal para confirmar la reclamación de fama"""
    
    def __init__(self, fame_system, fame_amount: int, user_data: dict):
        super().__init__()
        self.fame_system = fame_system
        self.fame_amount = fame_amount
        self.user_data = user_data
        
        # Actualizar título con la cantidad específica
        self.title = f"🏆 Reclamar {fame_amount:,} Fame Points"
    
    reason = discord.ui.TextInput(
        label="Razón de la Reclamación",
        placeholder="Explica brevemente por qué mereces estos puntos de fama...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    evidence = discord.ui.TextInput(
        label="Evidencia (URLs, Screenshots, etc.)",
        placeholder="Enlaces a pruebas, screenshots, videos, etc. (opcional)",
        required=False,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar la reclamación de fama"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Crear reclamación en la base de datos
            claim_id = await self.fame_system.fame_db.create_fame_claim(
                str(self.user_data['user_id']),
                str(interaction.user.id),
                str(interaction.guild.id),
                self.fame_amount
            )
            
            # Enviar notificación a canal de administradores
            notification_sent = await self.fame_system.send_admin_notification(
                interaction.guild, claim_id, interaction.user, self.fame_amount, 
                self.reason.value, self.evidence.value
            )
            
            if notification_sent:
                # Confirmar al usuario
                embed = discord.Embed(
                    title="✅ Reclamación Enviada",
                    description=(
                        f"Tu reclamación de **{self.fame_amount:,} Fame Points** ha sido enviada.\n\n"
                        f"**ID de Reclamación:** #{claim_id:04d}\n"
                        f"**Estado:** Pendiente de revisión\n\n"
                        "Un administrador revisará tu solicitud y la aprobará o rechazará."
                    ),
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Razón proporcionada",
                    value=self.reason.value[:100] + ("..." if len(self.reason.value) > 100 else ""),
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Actualizar el panel principal
                await self.fame_system.update_fame_rewards_panel(interaction.guild.id)
            else:
                # Error enviando notificación
                embed = discord.Embed(
                    title="⚠️ Reclamación Creada con Advertencia",
                    description=(
                        f"Tu reclamación ha sido guardada (ID: #{claim_id:04d}), pero no se pudo "
                        "enviar la notificación a los administradores. "
                        "Contacta directamente con un administrador."
                    ),
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error procesando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="No se pudo procesar tu reclamación. Inténtalo más tarde.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class AdminFameNotificationView(discord.ui.View):
    """Vista para las notificaciones de administradores con botones de confirmación"""
    
    def __init__(self, fame_system, claim_data: dict):
        super().__init__(timeout=None)
        self.fame_system = fame_system
        self.claim_data = claim_data
        self.message = None

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirmar la reclamación de fama"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden confirmar reclamaciones de fama.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Confirmar en base de datos
            success = await self.fame_system.fame_db.confirm_fame_claim(
                self.claim_data['claim_id'], str(interaction.user.id)
            )
            
            if success:
                # Actualizar embed del mensaje de notificación
                original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if original_embed:
                    original_embed.color = discord.Color.green()
                    original_embed.add_field(
                        name="✅ CONFIRMADO",
                        value=f"Por: {interaction.user.mention}\nFecha: <t:{int(datetime.now().timestamp())}:F>",
                        inline=False
                    )
                
                # Deshabilitar botones
                for item in self.children:
                    item.disabled = True
                
                await interaction.edit_original_response(embed=original_embed, view=self)
                
                # Actualizar panel de rankings
                await self.fame_system.update_fame_rewards_panel(self.claim_data['guild_id'])
                
                # Notificar al usuario (si es posible)
                await self.fame_system.notify_user_claim_result(
                    interaction.guild, self.claim_data, "confirmed", interaction.user
                )
                
                logger.info(f"Reclamación de fama #{self.claim_data['claim_id']} confirmada por {interaction.user}")
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo confirmar la reclamación (posiblemente ya fue procesada).",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error confirmando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al confirmar la reclamación.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rechazar la reclamación de fama"""
        
        # Verificar permisos de administrador
        if not any(role.permissions.administrator for role in interaction.user.roles):
            embed = discord.Embed(
                title="❌ Sin permisos",
                description="Solo administradores pueden rechazar reclamaciones de fama.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Mostrar modal para razón del rechazo
        modal = RejectReasonModal(self.fame_system, self.claim_data)
        await interaction.response.send_modal(modal)

class RejectReasonModal(discord.ui.Modal, title="❌ Rechazar Reclamación"):
    """Modal para especificar la razón del rechazo"""
    
    def __init__(self, fame_system, claim_data: dict):
        super().__init__()
        self.fame_system = fame_system
        self.claim_data = claim_data
    
    reason = discord.ui.TextInput(
        label="Razón del Rechazo",
        placeholder="Explica por qué se rechaza esta reclamación...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Procesar el rechazo con razón"""
        await interaction.response.defer()
        
        try:
            # Rechazar en base de datos
            success = await self.fame_system.fame_db.reject_fame_claim(
                self.claim_data['claim_id'], str(interaction.user.id)
            )
            
            if success:
                # Actualizar embed del mensaje de notificación
                original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if original_embed:
                    original_embed.color = discord.Color.red()
                    original_embed.add_field(
                        name="❌ RECHAZADO",
                        value=f"Por: {interaction.user.mention}\nFecha: <t:{int(datetime.now().timestamp())}:F>\nRazón: {self.reason.value}",
                        inline=False
                    )
                
                # Deshabilitar botones de la vista
                view = AdminFameNotificationView(self.fame_system, self.claim_data)
                for item in view.children:
                    item.disabled = True
                
                await interaction.edit_original_response(embed=original_embed, view=view)
                
                # Notificar al usuario (si es posible)
                await self.fame_system.notify_user_claim_result(
                    interaction.guild, self.claim_data, "rejected", interaction.user, self.reason.value
                )
                
                logger.info(f"Reclamación de fama #{self.claim_data['claim_id']} rechazada por {interaction.user}")
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No se pudo rechazar la reclamación (posiblemente ya fue procesada).",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error rechazando reclamación de fama: {e}")
            embed = discord.Embed(
                title="❌ Error interno",
                description="Ocurrió un error al rechazar la reclamación.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)