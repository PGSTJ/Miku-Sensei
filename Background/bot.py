import discord
from discord.ext import commands

from . import help



bot = commands.Bot(intents=discord.Intents.all(), command_prefix="ms.", help_command=help.MyHelp())
