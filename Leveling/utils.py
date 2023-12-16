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




class LevelRankUpdater():
    """ Updates profile data which is accessible by profile_display() method """
    def __init__(self, user:str, streak:int=0, accuracy:bool=None, submission:bool=True, extra_xp:int=0) -> None:
        self.user = user
        self.streak = streak
        self.accuracy = accuracy

        # current info 
        player_info = self.get_level_info(self.user)
        self.level = self.update_level_to = player_info[0]
        self.experience = player_info[1]
        self.rank = player_info[2]

        if submission:
            self.rewarded_xp = self.xp_calculator()
        if not submission:
            self.rewarded_xp = extra_xp
        
        print(f'rew xp: {self.rewarded_xp}')

        # update databases: level and total experience - rank will inherently update based off those two values
        update_exp = upsert_info(self.user, self.rewarded_xp) # update experience
        update_level = self.updater() # update level

        if update_exp and update_level:
            self.rank = self.determine_rank() # update rank

        # level up info - must happen last to ensure UTD in profile display
        self.level_up_req = self.calculate_level_requirement(self.level)

    
    @staticmethod
    def get_level_info(user:str) -> list:
        """ Gets player level info to display from levelsInfo DB """
        return list([info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (user,))][0])
    
    @staticmethod
    def calculate_level_requirement(level:int) -> int:
        """ Find total XP required to level up """
        return round((BASE_XP_REQUIREMENT * level ** EXP_FACTOR),0)
    
    def calculate_streak_reward(self) -> int:
        print(f'streak: {self.streak}')
        streak_multiplier = (BASE_STREAK_MULTIPLIER + self.streak * STREAK_LEVEL_MULTIPLIER) ** STREAK_FACTOR
        print(f'streak multiplier: {streak_multiplier}')
        return round((BASE_XP_REWARD * streak_multiplier),0)
    

    def xp_calculator(self) -> int:
        """ Determines amount of XP based on accuracy and streak """
        if not self.accuracy:
            return 0
        elif self.accuracy:
            if self.streak > 1:
                return self.calculate_streak_reward()
            else:
                return 1
    
    def determine_rank(self) -> str:
        """ Determines rank title based on level """
        for group in RANK_TITLES:
            print(f'rank title: {RANK_TITLES[group]}')
            if self.level < int(group):
                return RANK_TITLES[group]
            
    def updater(self, loop=True):
        """ Determines if new level has been reached and updates DB for LEVEL"""
        total_exp = self.experience + self.rewarded_xp

        # new level determination
        while loop:
            lur = self.calculate_level_requirement(self.update_level_to)
            if total_exp > lur:
                self.update_level_to += 1
            elif total_exp < lur:
                loop = False
            else:
                loop = False
                return False # error
        
        # update database as needed
        if self.level != self.update_level_to:
            curs_lvl.execute('UPDATE levelsInfo SET level=? WHERE name=?', (self.update_level_to, self.user))
            conn_lvl.commit()

            self.level = self.update_level_to # allows determination of new rank
            return True
        elif self.level == self.update_level_to:
            return True
        else:
            return False # error


    def profile_display(self) -> tuple:
        """ Returns string format for Profile Card """
        lvl_prog = f'{self.experience}/{int(self.level_up_req)}'
        return f'{self.level} ({lvl_prog})', self.rank




def upsert_info(user:str, rewarded_experience:int=False):
    """ Adds or updates exsting EXPERIENCE data in level info table """
    stored_users = [info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (user,))]

    # add new user
    if not stored_users:
        rk = RANK_TITLES['10']
        curs_lvl.execute('INSERT INTO levelsInfo(name, level, experience, rank) VALUES (?,?,?,?)', (user, 1, 0, rk))

    # calculates new total XP based on rewarded XP 
    if rewarded_experience:
        curr_xp = int([info[0] for info in curs_lvl.execute('SELECT experience FROM levelsInfo WHERE name=?', (user,))][0])
        new = curr_xp + rewarded_experience
        curs_lvl.execute('UPDATE levelsInfo SET experience=? WHERE name=?', (new, user))

    conn_lvl.commit()
    return True


def give_exp(user:str, amount:int):
    try:
        current = [info[0] for info in curs_lvl.execute('SELECT experience FROM levelsInfo WHERE name=?', (user,))][0]
        new = amount + int(current)
    except:
        new = amount

    upsert_info(user, new)
    
    return True




if __name__ == '__main__':
    d = upsert_info('PGSTJ')