from utils import curs_lvl, conn_lvl

def levelsInfo():
    """ DB Table of players level info """
    curs_lvl.execute('CREATE TABLE IF NOT EXISTS levelsInfo(name VARCHAR(20) PRIMARY KEY, level INT, experience INT, rank VARCHAR(30))')
    conn_lvl.commit()
    return True


if __name__ == '__main__':
    user = 'PGSTJ'
    stored_users = [info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (user,))]

    if not stored_users:
        print('empty')
    else:
        print('something')
