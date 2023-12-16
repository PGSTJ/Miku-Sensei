from utils import curs, conn

def kanji_bd(): # before deployment, update to be only creating kanji table rather than sample
    curs.execute('CREATE TABLE IF NOT EXISTS kanjiBD(id VARCHAR(15) PRIMARY KEY, kanji VARCHAR(10), translation VARCHAR(20), pronunciation VARCHAR(20), verb VARCHAR(20))')
    conn.commit()
    return True

def kanji_cd():
    """ Creates kanji code data table related to book data table """
    curs.execute('CREATE TABLE IF NOT EXISTS kanjiCD(id VARCHAR(15) PRIMARY KEY, book INT, chapter INT, asked_translation BOOL, asked_pronunciation BOOL, asked_verb BOOL, current BOOL, time_current VARCHAR(40), FOREIGN KEY (id) REFERENCES kanjiBD(id))')
    conn.commit()
    return True

def submission_profile():
    """User specific, contains submission data per submission group (coupled to current kanji)"""
    curs.execute('CREATE TABLE IF NOT EXISTS submissionProfile(spuid VARCHAR(10) PRIMARY KEY, user VARCHAR(20), kanji VARCHAR(8), correct BOOL, correct_time VARCHAR(30), first_incorrect BOOL, first_incorrect_time VARCHAR(30), second_incorrect BOOL, second_incorrect_time VARCHAR(30), third_incorrect BOOL, third_incorrect_time VARCHAR(30), period VARCHAR(15))')
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



def test_table():
    curs.execute('CREATE TABLE IF NOT EXISTS test(id VARCHAR(15) PRIMARY KEY, asked_translation BOOL, asked_pronunciation BOOL, asked_verb BOOL, current BOOL, time_current VARCHAR(40))')
    curs.execute('INSERT INTO test(id, asked_translation, asked_pronunciation, asked_verb, current, time_current) VALUES(?,?,?,?,?,?)', (1, True, True, False, False, ''))
    curs.execute('INSERT INTO test(id, asked_translation, asked_pronunciation, asked_verb, current, time_current) VALUES(?,?,?,?,?,?)', (2, False, False, False, False, ''))
    conn.commit()

if __name__ == '__main__':
    submission_profile()
    
