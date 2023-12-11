import datetime
import traceback

import discord
from discord.ext import commands

from KanjiPractice import profile, kanji, submit
from Background.ServerUtils import current_time


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
            profil = profile.profile_embed(show)
            await ctx.send(embed=profil)
        elif not valid:
            await ctx.send('This profile does not exist. Make sure to include an @ before specifying a user or check spelling.')
            

    @commands.command(name="cp")
    async def create_profile(self, ctx:commands.Context):
        """Creates profile for author"""
        user = ctx.author.name
        valid = profile.validation(user)

        if valid:
            await ctx.send('Profile already exists. See your profile with command \'!sp\' ')
        elif not valid:
            profile.create_profile(user)
            await ctx.send(f'Profile created for {user}')
        

    @commands.command(name="dp")
    async def delete_profile(self, ctx:commands.Context):
        """Delets profile for author"""
        user = ctx.author.name
        valid = profile.validation(user)

        em = discord.Embed(title='Are you sure?', description='All of your stats will be lost')

        if valid:
            await ctx.send(embed=em, view=profile.DeleteProfile(user))
        elif not valid:
            await ctx.send(f'Profile for {user} does not exist')


    @commands.command(name="ck")
    async def current_kanji(self, ctx:commands.Context):
        """See the current kanji"""
        curr_kan = kanji.current_kanji()
        
        em = discord.Embed(title='Current Kanji', description=curr_kan[0])
        await ctx.send(embed=em)

        

    

async def setup(bot:commands.Bot):
    await bot.add_cog(JapanesePractice(bot))