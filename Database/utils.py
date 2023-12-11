import sqlite3 as sl
import logging
import traceback
from typing import Tuple
import uuid

db = 'Database\\kanji-practice.db'
conn = sl.connect(db, check_same_thread=False)
curs = conn.cursor()

db_levels = 'Database\\level-data.db'
conn_lvl = sl.connect(db_levels, check_same_thread=False)
curs_lvl = conn_lvl.cursor()

ttl = logging.getLogger('TT')

VOCAB_DATA = 'Database\\data\\kanji.csv'

PROFILE_ATTRIBUTES = [
    'level',
    'total_correct',
    'total_incorrect',
    'total_answered',
    'streak',
    'achievements',
    'rank',
]

SUB_PRO_DB_IC_COLS = [
    'first_incorrect',
    'second_incorrect',
    'third_incorrect'
]

NUMBER_CONVERSION = {
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
    '十': 10,
}


def submission_profile_upsert(user:str, condition:str, current_kanji:str):   
    """
    Updates/Inserts into DB based on condition

    Options for Condition:
    - update
    - insert
    """
    cid = _spuid_generator(user, 'current')
    if condition == 'update':
        pid = _spuid_generator(user, 'previous')
        curs.execute('DELETE FROM submissionProfile WHERE spuid=?', (pid,))
        curs.execute('UPDATE submissionProfile SET period=?, spuid=? WHERE spuid=?', ('previous', pid, cid))
        curs.execute('INSERT INTO submissionProfile(spuid, user, kanji, correct, correct_time, first_incorrect, first_incorrect_time, second_incorrect, second_incorrect_time, third_incorrect, third_incorrect_time, period) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (cid, user, current_kanji, False, '', False, '', False, '', False, '', 'current'))
    elif condition == 'insert':
        curs.execute('INSERT INTO submissionProfile(spuid, user, kanji, correct, correct_time, first_incorrect, first_incorrect_time, second_incorrect, second_incorrect_time, third_incorrect, third_incorrect_time, period) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (cid, user, current_kanji, False, '', False, '', False, '', False, '', 'current'))

    conn.commit()
    return True


def _spuid_generator(user:str, period:str) -> str:
    """ Generates spuid based on user and period """
    return f'SP.{user[:3].upper()}.{period[:3].upper()}'
    # random_component = str(uuid.uuid4().hex)[:4]
    # return f'{user}_{time}_{random_component}'



def _sp_update(user:str, accuracy:bool, time:str, incorrect_number:int=0):
    """ Updates submission profile in DB table """
    try:
        if accuracy:
            col = 'correct'
        elif not accuracy:
            col = SUB_PRO_DB_IC_COLS[incorrect_number]
            # print(f'corrected ica: {incorrect_number+1}')
            
        curs.execute(f'UPDATE submissionProfile SET {col}=?, {col}_time=? WHERE user=? AND period=?', (True, time, user, 'current'))
        conn.commit()
        return True
    except TypeError:
        ttl.error('SP not updated. Answer was incorrect but no quantifier was provided')
        return False
    except:
        traceback.print_exc()
        return False

class KanjiInfo():
    """ Kanji object instantiated on each line of CSV import file to easily format for DB upload """
    amount = 0

    def __init__(self, csv_line:list, book:int) -> None:
        self.kanji = self._multiple_options_check(csv_line[0])
        self.pronunciation = self._multiple_options_check(csv_line[1])
        self.translation = self._multiple_options_check(csv_line[2])
        self.verb = self._verb_check(csv_line[4])
        self.chapter = self._get_chapter(csv_line[3][1])
        self.book = book

        self.id = self.create_id()

    def get_bd_format(self) -> Tuple[str, str, str, str, str]:
        """ Returns tuple format for DB upload """
        return (self.id, self.kanji, self.translation, self.pronunciation, self.verb)
    
    def get_cd_format(self) -> Tuple[str, int, int, bool, bool, bool, bool, str]:
        """ Returns tuple format for DB upload """
        return (self.id, self.book, self.chapter, False, False, False, False, '')

    def create_id(self):
        amount = len([info[0] for info in curs.execute('SELECT id FROM kanjiBD')])
        return f'{self.book}.{self.chapter}.{amount+1}'
    
    def _get_chapter(self, charcater:str):
        """ Extracts chapter, converting Japanese charater to number """
        try:
            return NUMBER_CONVERSION[charcater]
        except KeyError:
            ttl.error('Number doesn\'t exist. Chapter not found.')
            return False
        
    def _multiple_options_check(self, value:str) -> str:
        """ Checks for multiple options with semicolon delimiter. Returns single choice or list of choices"""
        if ';' in value:
            all_options = ','.join(value.split(';'))
            return all_options
        elif ';' not in value:
            return value
        else:
            print('error')
            return False
    
    def _verb_check(self, verb:str):
        """ Checks for verb type. If empty, will upload NULL """
        if not verb.isalpha():
            return None
        elif verb.isalpha():
            return verb
        else:
            traceback.print_exc()
            print('error with verb check')
            return False




def vocab_import_csv(book:int):
    try:
        with open(VOCAB_DATA, 'r', encoding='utf-8') as fn:
            fn.readline()
            for line in fn:
                kinfo = KanjiInfo(line.strip().split(','), book)
                bookdata = kinfo.get_bd_format()
                codedata = kinfo.get_cd_format()

                # update book and code data tables
                curs.execute('INSERT INTO kanjiBD(id, kanji, translation, pronunciation, verb) VALUES (?,?,?,?,?)', bookdata)
                curs.execute('INSERT INTO kanjiCD(id, book, chapter, asked_translation, asked_pronunciation, asked_verb, current, time_current) VALUES (?,?,?,?,?,?,?,?)', codedata)
        conn.commit()
        return True

    except:
        traceback.print_exc()
        return False
            



if __name__ == '__main__':
    pass

