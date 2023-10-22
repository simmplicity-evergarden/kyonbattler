from discord.ext import tasks, commands
from discord import app_commands,ui
import configparser
import re
import os
import discord
import logging
import enum
from random import randint
from typing import Literal
from settings import *
from typing import Optional
from typing import Union

logger = logging.getLogger('bot')

# Individual participant in a battle
class Participant:
    DEFAULT_HEALTH: int = 20
    def __init__(self,member):
        self.member: discord.Member = member 
        self.health = self.DEFAULT_HEALTH
        self.potions = {
                'luck':3,   # Roll 0-7 instead of 1-6
                'crit':3,   # 1.5x roll and use attack
                'iron':3,   # Halve incoming ATK and use defend
                'heal':3    # Heal 1HP + skip turn
            }

    def __str__(self):
        result = ""
        result += f"**Name:** {self.member.display_name}\n"
        result += f"**Health:** {self.health}\n"
        result += "Potions:\n"
        result += f"- Lucky:\t{self.potions['luck']}\n"
        result += f"- Critical:\t{self.potions['crit']}\n"
        result += f"- Iron:\t{self.potions['iron']}\n"
        result += f"- Healing:\t{self.potions['heal']}"
        return result

class Battle:
    players: list[Participant] = []
    channel: discord.TextChannel
    # tuple of (action, value)
    attack_response: (str,int) = None
    defense_response: (str,int) = None
    
    def __init__(self,channel: discord.TextChannel,initiator: discord.Member, acceptor: discord.Member):
        self.channel = channel
        self.players = []
        self.players.append(Participant(initiator))
        self.players.append(Participant(acceptor))

    # Attack turn
    async def attack_turn(self):
        view = Attack_Turn_View(self, self.players[0])
        print(f"{self.players[0].member.display_name}, {self.players[1].member.display_name}, {len(self.players)}")
        await self.channel.send(f'{self.players[0]}\n{self.players[0].member.mention} - it is your turn to attack!',view=view)


    # Defense turn
    async def defense_turn(self, attack_result: Union[Literal["surrender","heal"],int]):
        self.attack_result = attack_result
        
        # Skip to end of game
        if attack_result[0] == "surrender":
            await self.end_of_game(self.players[1])
            return 

        # Skip to end of turn
        elif attack_result[0] == "heal":
            await self.end_of_turn(("heal",1))
            return
        view = Defense_Turn_View(self, self.players[1])
        await self.channel.send(f'{self.players[1]}\n{self.players[1].member.mention} - it is your turn to defend!',view=view)


    async def end_of_turn(self, defense_result):
        self.defense_result = defense_result
        
        turn_results = ""
        turn_damage = 0

        # No defense action on heal
        if self.attack_result[0] == 'heal':
            turn_results = f"{self.players[0].member.display_name} uses a healing potion to recover {self.attack_result[1]} "
            if self.attack_result[1] == 1:
                turn_results += "point "
            else:
                turn_results += "points "
            turn_results += "of health."
        else:
            # Check for evade
            if self.defense_result[0] == 'evade':
                # Successful evade
                if self.defense_result[1] >= self.attack_result[1]:
                    turn_results = f"{self.players[0].member.display_name} attacks [{self.attack_result[1]}], but {self.players[1].member.display_name} evades [{self.defense_result[1]}]!"
                # Unsuccessful evade
                else:
                    turn_results = f"{self.players[1].member.display_name} attempts to dodge[{self.defense_result[1]}], but {self.players[0].member.display_name} hits them anyway [{self.attack_result[1]}]."
                    turn_damage = self.attack_result[1]
            # Defend
            else:
                # Lucky attack is 0
                if self.attack_result[1] == 0:
                    turn_results = f"{self.players[0].member.display_name} has caught some rotten luck and fumbles their attack. {self.players[1].member.display_name} remains unharmed.."
                # Ironskin 
                if 'iron' in self.defense_result[0]:
                    turn_results = f"{self.players[1].member.display_name}'s ironskin potion halves the effect of {self.players[0].member.display_name}'s attack [{self.attack_result[1]}]."
                    turn_damage = int(self.attack_result[1]/2)
                # Lucky block is 0
                elif self.defense_result[1] == 0:
                    turn_results = f"{self.players[1].member.display_name} has caught some rotten luck and gets hit with the full force of {self.players[0].member.display_name}'s attack [{self.attack_result[1]}]."
                    turn_damage = self.attack_result[1]
                # Successful defend (total damage negation)
                else:
                    turn_results = f"{self.players[1].member.display_name} blocks [{self.defense_result[1]}] some of {self.players[0].member.display_name}'s attack [{self.attack_result[1]}]."
                    turn_damage = self.attack_result[1] - self.defense_result[1]
                    if turn_damage < 1:
                        turn_damage = 1;
            if turn_damage != 0:
                turn_results += f"{self.players[1].member.display_name} takes {turn_damage} "
                if turn_damage == 1:
                    turn_results += f"point "
                else:
                    turn_results += f"points "
                turn_results += f"of damage."

        await self.channel.send(turn_results)

        self.players[1].health -= turn_damage

        if self.players[1].health < 1:
            await self.end_of_game(self.players[0])
            return

        # Reset results
        self.attack_result = None
        self.defense_result = None
        # Switch players
        self.players[0],self.players[1] = self.players[1],self.players[0]
        # Restart turn
        await self.attack_turn()

    async def end_of_game(self, winner: Participant):
        await self.channel.send(f"{winner.member.display_name} wins!")

class Defense_Turn_View(ui.View):
    def __init__(self, battle: Battle, participant: discord.Member, *, timeout=180):
        self.battle = battle
        self.participant = participant
        super().__init__(timeout=timeout)
        # Check for out of potions + max health
        for item in self.children:
            if (item.label == "Lucky Defend" and self.participant.potions['luck'] < 1):
                item.disabled = True
            if (item.label == "Iron Defend" and self.participant.potions['crit'] < 1):
                item.disabled = True

    @discord.ui.button(label="Defend",style=discord.ButtonStyle.primary)
    async def attack_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="⚔️",):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        action_roll = randint(1,6)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} chooses to defend [{str(action_roll)}].",view=self)
        await self.battle.end_of_turn(('defend',action_roll))

    @discord.ui.button(label="Lucky Defend",style=discord.ButtonStyle.primary)
    async def luck_potion_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🧪"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        self.participant.potions['luck'] -= 1
        action_roll = randint(0,7)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} tests their luck by drinking a Lucky Potion and defending [{str(action_roll)}].",view=self)
        await self.battle.end_of_turn(('luck_defend',action_roll))

    @discord.ui.button(label="Iron Defend",style=discord.ButtonStyle.primary)
    async def iron_potion_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🧪"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        self.participant.potions['iron'] -= 1
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} increases their defense with an Ironskin Potion as they defend.",view=self)
        await self.battle.end_of_turn(('iron_defend',0))
    
    @discord.ui.button(label="Evade",style=discord.ButtonStyle.primary)
    async def evade_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🧪"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        action_roll = randint(1,6)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} chooses to evade [{str(action_roll)}].",view=self)
        await self.battle.end_of_turn(('evade',action_roll))


    
    # Convenience function to disable all buttons
    async def disable_all_buttons(self):
        for child in self.children:
            child.style = discord.ButtonStyle.gray
            child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the participant may respond
        return interaction.user.id == self.participant.member.id


class Attack_Turn_View(ui.View):
    def __init__(self, battle: Battle, participant: discord.Member, *, timeout=180):
        self.battle = battle
        self.participant = participant
        super().__init__(timeout=timeout)
        # Check for out of potions + max health
        for item in self.children:
            if (item.label == "Lucky Attack" and self.participant.potions['luck'] < 1):
                item.disabled = True
            if (item.label == "Crit Attack" and self.participant.potions['crit'] < 1):
                item.disabled = True
            if (item.label == "Heal" and \
                    (self.participant.potions['heal'] < 1 or self.participant.health >= self.participant.DEFAULT_HEALTH)):
                item.disabled = True

    @discord.ui.button(label="Attack",style=discord.ButtonStyle.primary)
    async def attack_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="⚔️",):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        action_roll = randint(1,6)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} chooses to attack [{str(action_roll)}].",view=self)
        await self.battle.defense_turn(('attack',action_roll))

    @discord.ui.button(label="Lucky Attack",style=discord.ButtonStyle.primary)
    async def luck_potion_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🧪"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        self.participant.potions['luck'] -= 1
        action_roll = randint(0,7)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} tests their luck by drinking a Lucky Potion then attacking [{str(action_roll)}].",view=self)
        await self.battle.defense_turn(('luck_attack',action_roll))

    @discord.ui.button(label="Crit Attack",style=discord.ButtonStyle.primary)
    async def crit_potion_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🧪"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        self.participant.potions['crit'] -= 1
        action_roll = int(randint(1,6)*1.5)
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} drinks a Critial Potion before attacking. [{str(action_roll)}]",view=self)
        await self.battle.defense_turn(('crit_attack',action_roll))
    
    @discord.ui.button(label="Heal",style=discord.ButtonStyle.primary)
    async def heal_potion_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🩹"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        self.participant.health += 1
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} drinks a Healing Potion.",view=self)
        await self.battle.defense_turn(("heal",1))
       
    @discord.ui.button(label="Surrender",style=discord.ButtonStyle.primary)
    async def surrender_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="🆘"):
        await self.disable_all_buttons()
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(content=f"{self.participant.member.display_name} chooses to surrender.",view=self)
        await self.battle.defense_turn(("surrender",0))

    # Convenience function to disable all buttons
    async def disable_all_buttons(self):
        for child in self.children:
            child.style = discord.ButtonStyle.gray
            child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the participant may respond
        return interaction.user.id == self.participant.member.id


class Battle_Challenge_Response(ui.View):
    def __init__(self, initiator: discord.Member, target: discord.Member, *, timeout=180):
        self.initiator = initiator
        self.target = target
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Accept",style=discord.ButtonStyle.primary)
    async def accept_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="⚔️",):
        button.style=discord.ButtonStyle.green
        await self.disable_all_buttons()
        await interaction.response.edit_message(content=f"Battle accepted!",view=self)
        print(f"{self.initiator.display_name}, {self.target.display_name}")
        new_battle = Battle(interaction.channel, self.initiator, self.target)
        await new_battle.attack_turn()


    @discord.ui.button(label="Deny",style=discord.ButtonStyle.primary)
    async def deny_button(self,interaction: discord.Interaction,button: discord.ui.Button,emoji="☮️"):
        button.style=discord.ButtonStyle.red
        await self.disable_all_buttons()
        await interaction.response.edit_message(content=f"Battle denied!",view=self)

    # Convenience function to disable all buttons
    async def disable_all_buttons(self):
        for child in self.children:
            child.disabled=True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the target may respond
        return interaction.user.id == self.target.id



class Battler_Cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        logger.info('Loaded battler')

    # Initiate challenge between two people
    @commands.command(name='battle', description='Start battle with a user', aliases=['b'])
    async def start_battle(self, context: commands.Context, target: Optional[discord.Member]=None):
        if target == None:
            await context.send('No target specified.')
        # Check if the user is targeting themselves
        if target.id == context.author.id:
            await context.send('Stop hitting yourself.')
            return;
        
        # TODO check invalid target

        # Send response
        view = Battle_Challenge_Response(context.author, target)
        await context.send(f'{context.author.display_name} has challenged you to a battle, {target.mention}! Do you accept?',view=view)





