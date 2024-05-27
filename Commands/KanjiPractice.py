import datetime
import traceback

import discord
from discord.ext import commands

from KanjiPractice import profile, kanji, submit
from Background.ServerUtils import current_time
from Leveling import utils as lvl


class JapanesePractice(commands.Cog, name="JapanesePractice"):
    """Practice Japanese kanji and grammar structure"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sb')
    async def submit(self, ctx:commands.Context, answer:str):
        """submit half hourly kanji answers up to three times"""
        try:
            user = ctx.author

            # need to get current info and pass into Submission init
            
            submission_report = submit.Submission(user.name, answer, current_time())
            if not submission_report.valid_submission:
                return await ctx.send('You\'ve reached your submission limit for now, senpai! Take a breather and let the melodies of the next kanji inspire you. Miku will be right here, cheering you on for the next challenge') # TODO consider alternate response for previous correct
            
            presentation = submit.KanjiSubmission(user, submission_report.accuracy)
            embed, file = presentation.send_embed()
            return await ctx.send(file=file, embed=embed, view=kanji.SubmissionMenu()) 
        except Exception:
            traceback.print_exc()

    @commands.command(name='sp')
    async def show_profile(self, ctx:commands.Context, user:discord.Member = None):
        """shows profile of author, unless user specified"""
        if user:
            show = user
        else:
            show = ctx.author

        valid = profile.validation(show.name)

        if valid:
            pfl = profile.profile_embed(show)
            return await ctx.send(embed=pfl)
        elif not valid:
            return await ctx.send('This profile does not exist. Make sure to include an @ before specifying a user or check spelling.')
            

    @commands.command(name="cp")
    async def create_profile(self, ctx:commands.Context):
        """Creates profile for author"""
        user = ctx.author.name
        valid = profile.validation(user)
        lvl.LevelInfo(user)

        if valid:
            return await ctx.send('Profile already exists. See your profile with command \'!sp\' ')
        elif not valid:
            profile.create_profile(user)
            return await ctx.send(f'Profile created for {user}')
        

    @commands.command(name="dp")
    async def delete_profile(self, ctx:commands.Context):
        """Delets profile for author"""
        user = ctx.author.name
        valid = profile.validation(user)
        li = lvl.LevelInfo(user)

        em = discord.Embed(title='Are you sure?', description='All of your stats will be lost')

        if valid:
            li.delete_DB_profile()
            return await ctx.send(embed=em, view=profile.DeleteProfile(user))
        elif not valid:
            return await ctx.send(f'Profile for {user} does not exist')


    @commands.command(name="ck")
    async def current_kanji(self, ctx:commands.Context):
        """See the current kanji"""
        curr_kan = kanji.current_kanji()
        print(f'current info: {curr_kan}')
        
        em = discord.Embed(title='Current Kanji', description=curr_kan[0])
        return await ctx.send(embed=em)


    @commands.command(name='ge')
    async def give_exp(self, ctx:commands.Context, amount:int):
        """Give specified amount of XP to self"""
        user = ctx.author.name
        update = lvl.LevelInfoUpdater(user, submission=False, extra_xp=amount)
        
        level, rank = update.profile_display()
        profile._update_level_rank(user, level, rank)
        print(f'new level: {level} | new rank: {rank}')
        
        return await ctx.send(f'{amount} XP deposited')
        

    

async def setup(bot:commands.Bot):
    await bot.add_cog(JapanesePractice(bot))