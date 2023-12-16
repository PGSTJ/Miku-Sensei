import json
import os
import random
import datetime

import discord
from discord.ext import commands

from .bot import bot


SERVER_NAME = 'Bot Tests'


def member_info() -> bool: #TODO: should happen on startup
    """ Uploads members from discord server into a json for DB upload """
    # if bot is in multiple servers, allows for modulation and choosing which specific server you want
    # grabs name and id to insert into DB table as initial row values - rankId and worm amount are filled later
    svr_nm = "Bot Tests"
    guild_members = [guild.members for guild in bot.guilds if guild.name == svr_nm]
    info = {members.id: members.name for members in guild_members[0]}

    # print(info)


    with open('Database\\data\\_members.json', 'w') as mjf:
        json.dump(info, mjf)

    return True

def roles_info() -> bool:
    """ Uploads roles from discord server into a json for DB upload """
    # if bot is in multiple servers, allows for modulation and choosing which specific server you want
    guild_roles = [guild.roles for guild in bot.guilds if guild.name == SERVER_NAME]
    info = {roles.id: roles.name for roles in guild_roles[0]}

    # print(info)

    with open('Database\\data\\_roles.json', 'w') as rjf:
        json.dump(info, rjf)

    return True
    
def bot_init():
    """ Update member and role jsons if different """
    if not member_info():
        return False
    if not roles_info():
        return False
    return True

async def assign_role(role_key:int, uid:discord.Member):
    """
    Assigns a specified role to a specified user
      
    :param role_key: role id as int
    :param uid: id of member as int
    :return: none
    """
    svr = await get_server()
    mem = svr.get_member(uid)
    role = svr.get_role(role_key)
    await mem.add_roles(role)


async def get_mem(uid:discord.Member) -> discord.Member:
    """
    Get discord.Member objects easier
    
    :param uid: id of member as int
    :return: member as discord object
    """
    svr = await get_server()
    mem = svr.get_member(uid)
    return mem


async def get_highest_role(member_id:discord.Member) -> discord.Role:
    """
    Get current user role according to worm specific roles
    
    :param member_id: member int id as a Member object
    :return: the highest worm role
    """
    svr = await get_server()
    member = svr.get_member(member_id)
    
    with open('worm_roles.json', 'r') as wr:
        worm_roles = json.load(wr)
    # roles are ordered by importance with index via enumerating worm_role dct
    role_importance = [int(ob[1]) for ob in enumerate(worm_roles)]
    # creates an easily comprehended list of roles to compare to
    memb_rls = [role for role in member.roles]
    # iterates through worm roles id to find a match and return the name
    for roles in role_importance:
        if svr.get_role(roles) in memb_rls:
            return svr.get_role(roles)
            



async def announcement_creation(file_list, folder, order_dct, order_list):
    """
    Creates lists and extracts order of msg to prepare for announcement formatting
        
    :param file_list: the list that will hold the names of all the files -- for easy access to filenames
    :param folder: the destination folder containing msg txt files -- must include \ at the start
    :param order_dct: the msg txt files formatted in correct presentation derived from first line of txt file; k:v is order_number:filename 
    :param order_list: contains the names in correct order derived from order_dct
    :return: none
    """
    # searches through Announcements folder at specified directory
    directory = os.fsencode(f"Announcements{folder}")
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        # creates list to easily refer to later when constructing announcement embed    
        if filename.endswith(".txt"):
            file_list.append(filename)
            # with the exception of the intro.txt, orders all msg txt files into correct presentation via dictionary
            with open(f"Announcements{folder}\{filename}") as f:
                if filename != "intro.txt":
                    ord = f.readline().strip()
                    order_dct[int(ord)] = filename
    
    # automatically creates order of message based on numbering in individual txt files
    # intro.txt should be number 1, so start at 2 to ignore intro file
    for x in range(2, len(order_dct)+2):
        order_list.append(order_dct[x])



async def announcement_format(file_list, folder, order_list):
    """
    Creates actual embed for announcement and formats fields 
    
    :param file_list: the list that will hold the names of all the files -- for easy access to filenames
    :param folder: the destination folder containing msg txt files -- must include \ at the start
    :param order_list: contains the names in correct order derived from order_dct
    :return: final embed
    """
    # formats intro.txt first -- intro.txt is a REQUIREMENT for each announcements folder
    with open(f"Announcements{folder}\intro.txt") as i:
        # creates embed message
        title = i.readline()
        msg = discord.Embed(title=title, colour=discord.Colour.from_rgb(34,225,197))
        # needed variables; content will be value of embed field
        lne = []
        cnt = ""
        

        # puts lines into list to extract name from [0] then create msg cnt from rest of list
        for line in i:
            lne.append(line)
        nme = lne[0]
        lne.remove(nme)
        # creates msg cnt
        for line1 in lne:
            cnt += line1
        # add to embed
        msg.add_field(name = nme, value=cnt)

    # refers back to file list as mentioned prior
    for txt in order_list:
        if txt in file_list:
            with open(f"Announcements{folder}\{txt}") as i:
                # needed variables; content will be value of embed field                    
                lne1 = []                
                cnt1 = ""            
                # puts lines into list to extract name from [0] then create msg cnt from rest of list
                for line2 in i:
                    lne1.append(line2)
                nme1 = lne1[1]
                lne1.remove(nme1)
                lne1.remove(lne1[0])
                # creates msg cnt
                for line3 in lne1:
                    cnt1 += line3
                # add to embed
                msg.add_field(name = nme1, value=cnt1, inline=False)
    return msg


async def get_server():
    """ Gets server with server id """
    svr = bot.get_guild(412125368363909140)
    return svr


def current_time():
    """ Gets current time and returns as Y-M-D H:M:S """
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')


def time_check(self, minutes: int, timestamp: datetime) -> bool:
        """
        Verify a log being within a certain time provided by minutes parameter

        :param minutes: int of how many minutes to look back (ie 10 or 30)
        :param timestamp: datetime object of timestamp to verify
        :return: bool verification
        """
        current_time = datetime.datetime.now()
        x_minutes_ago = current_time - datetime.timedelta(minutes=minutes)

        if timestamp > x_minutes_ago:
            return True
        else:
            return False