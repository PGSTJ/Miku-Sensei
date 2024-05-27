import os
import csv
import traceback

from utils import curs, conn

KANJI_FILE = 'Database\\data\\kanji.csv'


def kanji_bd(): # before deployment, update to be only creating kanji table rather than sample
    curs.execute('CREATE TABLE IF NOT EXISTS kanjiBD(id VARCHAR(15) PRIMARY KEY, kanji VARCHAR(10), translation VARCHAR(20), pronunciation VARCHAR(20), verb VARCHAR(20))')
    conn.commit()
    return True

def kanji_cd():
    """ Creates kanji code data table related to book data table """
    curs.execute('CREATE TABLE IF NOT EXISTS kanjiCD(id VARCHAR(15) PRIMARY KEY, book INT, chapter INT, asked_translation BOOL, asked_pronunciation BOOL, asked_verb BOOL, current BOOL, time_current VARCHAR(40), question_type INT, FOREIGN KEY (id) REFERENCES kanjiBD(id))')
    conn.commit()
    return True

def submission_profile():
    """User specific, contains submission data per submission group (coupled to current kanji)"""
    curs.execute('CREATE TABLE IF NOT EXISTS submissionProfile(spuid VARCHAR(10) PRIMARY KEY, user VARCHAR(20), kanji VARCHAR(8), correct BOOL, total_incorrect INT, correct_time VARCHAR(30), first_incorrect BOOL, first_incorrect_time VARCHAR(30), second_incorrect BOOL, second_incorrect_time VARCHAR(30), third_incorrect BOOL, third_incorrect_time VARCHAR(30), period VARCHAR(15))')
    return True

def profile():
    curs.execute('CREATE TABLE IF NOT EXISTS profiles(name VARCHAR(20) PRIMARY KEY, level VARCHAR(15), total_correct INT, total_incorrect INT, total_answered INT, streak INT, achievements INT, rank VARCHAR(30), created VARCHAR(15))')
    return True

def recreate_all():
    tables = [info[0] for info in curs.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',))]

    for table in tables:
        curs.execute(f'DROP TABLE {table}')
    conn.commit()

    f, e, d, t = kanji_bd(), submission_profile(), profile(), kanji_cd()

    if f and e and d and t:
        print('kanji submission db tables created')
    else:
        print('error, no tables created')


class KanjiUpload():
    def __init__(self, row:list) -> None:
        self.clean = False
        self.id = ''
        self.term = row[0]
        self.tranlsation = row[2]
        self.pronunciation = row[1]
        self.chapter = row[3]
        self.verb = row[4]
        self.book = 1

        mop = self._multiple_options_parser()
        ig =  self.id_generator()
        utd = self._upload_to_db()
        
        if mop and ig and utd:
            self.clean = True
        else:
            traceback.print_exc()
        


    def _upload_to_db(self):
        try:
            curs.execute('INSERT INTO kanjiBD(id, kanji, translation, pronunciation, verb) VALUES(?,?,?,?,?)', (self.id, self.term, self.tranlsation, self.pronunciation, self.verb))
            curs.execute('INSERT INTO kanjiCD(id, book, chapter, asked_translation, asked_pronunciation, asked_verb, current, time_current, question_type) VALUES(?,?,?,?,?,?,?,?,?)', (self.id, self.book, self.chapter, False, False, False, False, '', 0))
        except:
            traceback.print_exc()
            return False # raise error    
        conn.commit()
        return True

    def _multiple_options_parser(self):
        """ Parses kanji with multiple translation/pronunciation options """
        try:
            if ';' in self.tranlsation:
                format = self.tranlsation.split(';')
                finalized = [item.strip() for item in format]
                self.tranlsation = str(finalized)
            if ';' in self.pronunciation:
                format = self.pronunciation.split(';')
                finalized = [item.strip() for item in format]
                self.pronunciation = str(finalized)
        except:
            traceback.print_exc()
            return False # raise error
        return True
    
    def id_generator(self):
        all = [info[0] for info in curs.execute('SELECT COUNT(id) FROM kanjiBD')][0]
        self.id = f'{self.book}.{self.chapter}.{str(all + 1)}'
        return True

    def pronunciation_formatter(self):
        """ formats commas back into pronunciation, inititially removed to avoid confusion with CSV parsing """


def upload_kanji():
    """ Handles uploading kanji data into DB tables """
    # d = 0
    with open(KANJI_FILE, 'r', encoding='utf-8') as fn:
        fn.readline()
        data = csv.reader(fn)
        
        for row in data:
            KanjiUpload([info.strip() for info in row])
            # d += 1
            # if d == 10:
            #     break
        print('upload success')

            
            



def test_table():
    curs.execute('CREATE TABLE IF NOT EXISTS test(id VARCHAR(15) PRIMARY KEY, asked_translation BOOL, asked_pronunciation BOOL, asked_verb BOOL, current BOOL, time_current VARCHAR(40))')
    curs.execute('INSERT INTO test(id, asked_translation, asked_pronunciation, asked_verb, current, time_current) VALUES(?,?,?,?,?,?)', (1, True, True, False, False, ''))
    curs.execute('INSERT INTO test(id, asked_translation, asked_pronunciation, asked_verb, current, time_current) VALUES(?,?,?,?,?,?)', (2, False, False, False, False, ''))
    conn.commit()

if __name__ == '__main__':
    submission_profile()
    
