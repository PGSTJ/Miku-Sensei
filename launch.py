import asyncio
import datetime
import json
import logging
import os
import traceback

from discord.ext import commands
from dotenv import load_dotenv

from Background.bot import bot
from Background import ServerUtils as su
from KanjiPractice import kanji
from Logging import initialize


load_dotenv()

# commands to (un)load commands by category
async def load(extension):
    await bot.load_extension(f"Commands.{extension}")

"""
@bot.command()
async def unload(extension):
    bot.unload_extension(f"Commands.{extension}") 
"""


@bot.event
async def on_ready():
    # loads all commands within categories
    for filename in os.listdir('./Commands'):
        if filename.endswith('.py'):
            # print(filename[:-3])
            await load(filename[:-3])

    channel = bot.get_channel(1157854490016354414)

    if not su.bot_init():
        traceback.print_exc()
        return False
    
    # initialize loggers
    if not initialize.init():
        return False
    
    # initialize database
    # db_recreate()

    # await su.member_info()

    
    # start sending kanji
    # asyncio.ensure_future(ask_kanji())

    return await channel.send('漢字練習にしてあげる！')

@bot.command(name='sk')
async def kanjiqs(ctx:commands.Context):
    present = kanji.KanjiPresentation()
    embed = present.get_kanji_embed()
    await ctx.send(embed=embed)


async def ask_kanji():
    """Automatically sends kanji after set time - currently 1min"""
    while not bot.is_closed():    
        present = kanji.KanjiPresentation()
        embed, file = present.get_kanji_embed()

        channel = bot.get_channel(997731945221996571)
        await channel.send(embed=embed)
        await asyncio.sleep(60) 



bot.run(os.getenv("TOKEN"))