import datetime 
import traceback
import logging
from typing import Tuple

from . import profile as pf, kanji as kn
from Database.utils import curs, conn, submission_profile_upsert, _sp_update
from Background.ServerUtils import current_time


logger = logging.getLogger('JPGen')
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

        self.current_info = kn.current_kanji() # package order: kanji, translation, pronunciation, verb, time set ck 
        
        self.submission_profile_verification(self.current_info[0])
        
        slv = self.submission_limit_verification()
        if slv:
            self.valid_submission = True
        else:
            self.valid_submission = False

        
        if not self.answer_verification():
            print('erorr with answer verification')

        self.update_db()
            

    def recent_submissions(self) -> list | bool:
        """ 
        Creates list of current answering status of a user for a submission profile/period 
        
        :returns: 
        - a list with set order- [correct, first_incorrect, second_incorrect, third_incorrect]
        - False if brand new user and no prior submissions have been made
        """
        try:
            submits = [info for info in curs.execute('SELECT correct, first_incorrect, second_incorrect, third_incorrect FROM submissionProfile WHERE user=? AND period=?', (self.user, 'current'))][0]
            # ttl.warning(f'recent submissions: submits - {submits}')

            return list(submits)
        except IndexError:
            return False 
        except Exception:
            traceback.print_exc()

    def submission_limit_verification(self) -> bool | Tuple[bool, int]:
        """
        Checks for previously correct answers or whether guesses have been maxed based on index

        :returns True: if submission limit has not been reached
        """
        sub_group = self.recent_submissions()
        # ttl.warning(f'sub group - {sub_group}')
        print(f'sub answer group: {sub_group}')
        
        answered = [sub for sub in sub_group if sub == 1]
        print(f'recent subs: {answered}')
        if len(answered) < 1:
            self.first_submission = True

        if not sub_group:
            ttl.warning('T - brand new user')
            return True

        # first check if user has already answered correctly
        elif sub_group[0] is True:
            ttl.warning('F - previous correct answer in SP')
            return False 
        else:
            # removes correct value and focuses incorrect statuses
            incorrect_amount = len([values for values in sub_group[1:] if values == 1])
            # ttl.warning(incorrect_amount)

            if incorrect_amount < 3:
                return True, incorrect_amount
                # 'okay to proceed' 
            elif incorrect_amount == 3:
                self.maxed = True
                return False
            else:
                return False
                # 'maxed out guesses; wait for next kanji'
        
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
            return _sp_update(self.user, self.accuracy, self.timestamp)
        else:
            ica = self._all_incorrects()
            return _sp_update(self.user, self.accuracy, self.timestamp, ica)

        

    def _all_incorrects(self) -> int:
        """ Determine number of incorrects for the current submission period"""
        db_ica = [info for info in curs.execute('SELECT first_incorrect, second_incorrect, third_incorrect FROM submissionProfile WHERE user=? AND period =?', (self.user, 'current'))][0]
        return len([amt for amt in db_ica if amt == 1])

    def answer_verification(self) -> bool:
        """
        Compares user given answer to chosen kanji in kanji DB

        :param answer: str of user answer
        :return: bool 
        """
        if not self.current_info:
            print('issue with current info')
            return False
        if self.answer in self.current_info:
            self.accuracy = True
            return True

        elif self.answer not in self.current_info:
            self.accuracy = False
            return True
        
        logger.info(f'{self.user} submitted')
        # extras={'user':self.user, 'answer':self.answer, 'accuracy':self.accuracy, 'correct answer':self.current_info}
           
