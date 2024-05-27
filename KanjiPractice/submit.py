import datetime 
import traceback
import logging
from typing import Tuple
import os
import random
import json

from . import profile as pf, kanji as kn
from Database.utils import curs, conn, submission_profile_upsert, sp_update
from Background.ServerUtils import current_time
from Leveling import utils as lvl

import discord

logger = logging.getLogger('JPGen')
logger_sub = logging.getLogger('Submission')
ttl = logging.getLogger('TT')


class Submission():
    """ Report object that handles question analysis and updating the database """
    def __init__(self, user:str, answer:str, time:datetime.datetime) -> None:
        self.user = user
        self.answer = answer
        self.timestamp = time
        self.accuracy = None
        self.maxed = False
        self.first_submission = False

        self.current_info = kn.current_kanji() # package order: kanji, translation, pronunciation, verb, time set ck, question type
        
        self.submission_profile_verification(self.current_info[0])
        
        slv = self.submission_limit_verification()
        if not slv:
            self.valid_submission = True
        else:
            self.valid_submission = False

        
        if not self.answer_verification():
            print('erorr with answer verification')

        if not self.update_db():
            print('error with updating to DB')
            

    def recent_submissions(self) -> list | bool:
        """ 
        Creates list of current answering status of a user for a submission profile/period 
        
        :returns: 
        - a list with set order- [correct, first_incorrect, second_incorrect, third_incorrect]
        - False if brand new user and no prior submissions have been made
        """
        try:
            submits = [info for info in curs.execute('SELECT correct, total_incorrect FROM submissionProfile WHERE user=? AND period=?', (self.user, 'current'))][0]
            # ttl.warning(f'recent submissions: submits - {submits}')

            return list(submits)
        except IndexError:
            return False 
        except Exception:
            traceback.print_exc()

    def submission_limit_verification(self) -> bool:
        """
        Checks for previously correct answers or whether guesses have been maxed based on index

        :returns True: if submission limit has not been reached
        """
        sub_group = self.recent_submissions()
        # ttl.warning(f'sub group - {sub_group}')
        # print(f'sub answer group: {sub_group}')

        print(f'subgroup: {sub_group}')

        if sub_group[0] is True:
            limit = True
        elif sub_group[1] >= 3:
            limit = True
        else:
            limit = False

        # first submission of period so not to double count questions answered
        if not sub_group[0] and sub_group[1] == 0:
            self.first_submission = True

        print(f'first sub: {self.first_submission}')
        
        # print(f'limit: {limit}')
        return limit
        
    def submission_profile_verification(self, current_kanji:str) -> bool:
        """ Determines if user has a prior submission profile and will create if not """

        existing_users = [info[0] for info in curs.execute('SELECT user FROM submissionProfile')]
        if self.user in existing_users:
            if self._verify_current_period(current_kanji):
                return True
            else:
                # reset submission profile in DB with current submission group data
                submission_profile_upsert(self.user, 'update', current_kanji)
                logger.info(f'Submission Profile reset for {self.user}')
        elif self.user not in existing_users:
            # create new submission profile in DB
            submission_profile_upsert(self.user, 'insert', current_kanji)
            logger.info(f'Submission Profile created for {self.user}')
        else:
            logger.error(f'Unable to verify submission profile query or handle creation for user: {self.user}')
            return False
        return True
    
    def _verify_current_period(self, ck:str):
        """ Determines whether a new current period needs to be created """
        curr_per_kan = [info[0] for info in curs.execute('SELECT kanji FROM submissionProfile WHERE period=?', ('current',))][0]
        if ck == curr_per_kan:
            return True
        else:
            return False
    
    def update_db(self):
        """ Updates submission profile in the DB """
        if self.first_submission:
            pf.update_value(self.user, ['total_answered'])

        if self.accuracy:
            upd_db = sp_update(self.user, self.accuracy, self.timestamp)
        else:
            ica = [info[0] for info in curs.execute('SELECT total_incorrect FROM submissionProfile WHERE user=?', (self.user,))][0]
            upd_db = sp_update(self.user, self.accuracy, self.timestamp, ica)
        return upd_db

    def answer_verification(self) -> bool:
        """
        Compares user given answer to chosen kanji in kanji DB

        :param answer: str of user answer
        :return: bool 
        """
        if not self.current_info:
            print('issue with current info')
            return False
        
        # extracts specific answer based on question type (ie, if asking for translation, will extract correct translation)
        answer_key = self.current_info[self.current_info[5]]

        print(f'answer: {self.answer}')
        print(f'anskwer key: {answer_key}')
    
        
        if self.answer in answer_key:
            self.accuracy = True
        elif self.answer not in answer_key:
            self.accuracy = False
        
        logger.info(f'{self.user} submitted | accuracy: {self.accuracy}')
        # extras={'user':self.user, 'answer':self.answer, 'accuracy':self.accuracy, 'correct answer':self.current_info}
        return True
           

class KanjiSubmission():
    """Responsible for embed creation and coordination"""
    MIKU_FOLDER = 'photos\\miku'

    def __init__(self, user:discord.Member, accuracy:bool, force_show:bool=False, **kwargs) -> None: 
        self.user = user
        self.accuracy = accuracy
        self.force_show = force_show
        self.msg = self.message()

        if self.accuracy:
            pf.update_value(self.user.name, ['total_correct', 'streak'])
        elif not self.accuracy:
            pf.update_value(self.user.name, ['total_incorrect', 'resetStreak'])

        # update profile data in both DBs
        self.level_exit_sequence(user.name)

    def send_embed(self) -> discord.Embed:
        """ Sends embed from constructor function """ 
        embed = discord.Embed(title='Embed', color=discord.Colour.from_rgb(34,225,197))
        embed.title = f'Kanji Practice - {self.user.name}'
        embed.add_field(name=self.accuracy, value=self.msg)

        file, selected_miku = self.miku_selecter()
        embed.set_image(url=f'attachment://{selected_miku}')

        return embed, file

    def message(self) -> str:
        """
        Determines which message variant to send after submission: congrats or deny

        :param submitLevel: int corresponding to adjusted submission number (submission number - 1); required for submitLevel specific messages
        :return: congrats/try again message as str
        """
        if self.accuracy:
            type = 'congratulators'
        elif not self.accuracy:
            type = 'encouragers'

        with open(f'KanjiPractice\\{type}.json', 'r') as fn:
            msgs = json.load(fn)

        data = [info for info in curs.execute('SELECT correct, first_incorrect, second_incorrect, third_incorrect FROM submissionProfile WHERE user=? AND period=?', (self.user.name, 'current'))][0]
        # print(f'sub statuses: {data}')
        submissions = len([sub for sub in data if sub == 1])

        response_set = msgs[str(submissions)]
        return random.choice(response_set)

    def level_exit_sequence(self, user:str):
        # obtain streak and awarded XP amounts
        streak = pf.get_attribute(user, ['streak'])[0]
        updater = lvl.LevelInfoUpdater(user, streak=streak, accuracy=self.accuracy)
        level, rank = updater.profile_display()
        # update level and rank of profile DB accordingly 
        pf._update_level_rank(user, level, rank)

        return True #TODO consider error catching / create info chokepoint -> all updates must be successful else an error raised


    def miku_selecter(self):
        """ Randomly selects a Miku Variant for message thumbnails """
        all = os.listdir(self.MIKU_FOLDER)
        selected = random.choice(all)
        path = os.path.join(self.MIKU_FOLDER, selected)
        file = discord.File(path, selected)
        return file, selected
        
        