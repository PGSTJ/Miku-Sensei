from discord.ext import commands
import discord
from typing import Optional, Set

class HelpCog(commands.Cog, name="Help"):
    """Shows help info about commands"""
    def __init__(self, bot:commands.Bot):
        self._original_help_command = bot.help_command
        bot.help_command = MyHelp()
        bot.help_command.cog = self

    def cog_unload(self, bot:commands.Bot):
        bot.help_command = self._original_help_command

class MyHelp(commands.HelpCommand):
    def __init__(self, **options):
        self.clean_prefix = 'wb.'
        super().__init__(**options)

    def get_command_signature(self, command:commands.Command):
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}"

    async def _help_embed(self, title: str, description: Optional[str] = None, mapping: Optional[str] = None, command_set: Optional[Set[commands.Command]] = None):
        embed = discord.Embed(title =title, colour=discord.Colour.from_rgb(34,225,197))
        if description:
            embed.description = description
        if command_set:
            # show help about all cmds in the set
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.help, inline=False)
        elif mapping:
            # add a short description of commands in each cog
            for cog, commands in mapping.items():
                filtered  = await self.filter_commands(commands, sort=True)
                if not filtered:
                    continue
                name = cog.qualified_name if cog else "Other"
                cmd_list = "\u2002".join(
                    f"`{self.clean_prefix}{cmd.name}`" for cmd in filtered
                )
                value = (
                    f"{cog.description}\n{cmd_list}"
                    if cog and cog.description
                    else cmd_list
                )
                embed.add_field(name=name, value=value)
        return embed
    
    async def send_bot_help(self, mapping: dict):
        embed = await self._help_embed(
            title="~Help Desk~",
            description="To get help about a specific command category, type !help <category>.",
            mapping=mapping
        )
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = await self._help_embed(
            title=command.qualified_name,
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None
        )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog:commands.Cog):
        embed = await self._help_embed(
            title=cog.qualified_name,   
            description=cog.description,
            command_set=cog.get_commands()
        )
        await self.get_destination().send(embed=embed)
