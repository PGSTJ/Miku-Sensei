import json

from Database.utils import curs_lvl, conn_lvl




with open('Leveling\\config.json', 'r') as cf:
    prefs = json.load(cf)

BASE_XP_REQUIREMENT = prefs['baseXPreq']
BASE_XP_REWARD = prefs['baseXPrew']
EXP_FACTOR = prefs['EXPfactor']

BASE_STREAK_MULTIPLIER = prefs['baseStreakMultiplier']
STREAK_LEVEL_MULTIPLIER = prefs['streakLevelMultiplier']
STREAK_FACTOR = prefs['streakFactor']

RANK_TITLES = prefs['rankTitles']

def calculate_level_requirement(level:int) -> int:
    """ Find total XP required to level up """
    return round((BASE_XP_REQUIREMENT * level ** EXP_FACTOR),0)

def calculate_streak_reward(streak_length:int) -> int:
    streak_multiplier = (BASE_STREAK_MULTIPLIER + streak_length * STREAK_LEVEL_MULTIPLIER) ** STREAK_FACTOR
    return round((BASE_XP_REWARD * streak_multiplier),0)

def determine_rank(level:int) -> str:
    """ Determines rank title based on level """
    for group in RANK_TITLES:
        if level < int(group):
            return RANK_TITLES[group]
        
def _update_level_rank(user:str):
    """ Determines if new level has been reached """
    data:tuple = get_level_info(user) # (level, experience, rank)
    lvl_req = calculate_level_requirement(data[0])
    if data[1] > lvl_req:
        new_level = data[0] + 1
        curs_lvl.execute('UPDATE levelsInfo SET level=? WHERE name=?', (new_level, user))
    
        if new_level % 10 == 0:
            new_rank = determine_rank(data[0])
            curs_lvl.execute('UPDATE levelsInfo SET rank=? WHERE name=?', (new_rank, user))

    conn_lvl.commit()
    return True

def xp_calculator(accuracy:bool, streak:int) -> int:
    """ Determines amount of XP based on accuracy and streak """
    if not accuracy:
        return 0
    elif accuracy:
        if streak > 1:
            return calculate_streak_reward(streak)
        else:
            return 1
        
        


def get_level_info(user:str):
    """ Gets player level info to display as: Level - (current xp/xp req) """
    return [info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (user,))][0]

def upsert_info(user:str, experience:int=False):
    """ Adds or updates exsting data in level info table """
    stored_users = [info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (user,))]

    # add new user
    if not stored_users:
        rk = determine_rank(1)
        curs_lvl.execute('INSERT INTO levelsInfo(name, level, experience, rank) VALUES (?,?,?,?)', (user, 1, 0, rk))
    else:
        if experience:
            curr_xp = int([info[0] for info in curs_lvl.execute('SELECT experience FROM levelsInfo WHERE name=?', (user,))][0])
            new = curr_xp + experience
            curs_lvl.execute('UPDATE levelsInfo SET experience=? WHERE name=?', (new, user))

    conn_lvl.commit()
    return True

def profile_display(user:str):
    data = get_level_info(user)
    level = data[0]
    exp = data[1]
    rank:str = data[2]

    req = calculate_level_requirement(level)
    lvl_prog = f'{exp}/{int(req)}'
    return f'{level} ({lvl_prog})', rank



if __name__ == '__main__':
    d = upsert_info('PGSTJ')