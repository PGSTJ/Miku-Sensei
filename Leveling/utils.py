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

RANK_TITLES:dict = prefs['rankTitles']


class LevelInfo():
    """ Base class for LevelsInfo DB, can do basic DB manipulation such as deleting or creating profiles """
    def __init__(self, user:str) -> None:
        self.user = user

        try:
            self.stored_users:tuple = [info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (self.user,))][0]

        except IndexError:
            # add new user
            # print(f'stored users: {self.stored_users}')
            rk = RANK_TITLES['10']
            curs_lvl.execute('INSERT INTO levelsInfo(name, level, experience, rank) VALUES (?,?,?,?)', (self.user, 1, 0, rk))
            conn_lvl.commit()
    
    def delete_DB_profile(self):
        """ Deletes user from LevelInfo DB """
        curs_lvl.execute('DELETE FROM levelsInfo WHERE name=?', (self.user,))
        conn_lvl.commit()
        return True
        

class LevelInfoUpdater(LevelInfo):
    """ Updater object for LevelsInfo DB """
    def __init__(self, user:str, streak:int=0, accuracy:bool=None, submission:bool=True, extra_xp:int=0) -> None:
        super().__init__(user)

        self.change_level = False
        self.change_rank = False

        # current info 
        player_info = self.get_level_info()
        self.level = player_info[0]
        self.experience = player_info[1]
        self.rank = player_info[2]


        if submission:
            self.accuracy = accuracy
            self.streak = streak
            self.rewarded_xp = self.xp_calculator()
        elif not submission:
            self.rewarded_xp = extra_xp
        
        # print(f'rew xp: {self.rewarded_xp}')
        self.updater()

        # level up info - must happen last to ensure UTD in profile display
        self.level_up_req = self.calculate_level_requirement(self.level)
        

    def get_level_info(self) -> list:
        """ Gets player level info to display from levelsInfo DB """
        return list([info for info in curs_lvl.execute('SELECT level, experience, rank FROM levelsInfo WHERE name=?', (self.user,))][0])
    

    def updater(self, level_loop=True):
        """ Updates level, experience, and rank in levelsInfo DB"""
        self.experience += self.rewarded_xp

        # continually loops to account for large jumps in XP, which should be impossible
        while level_loop is True:
            if self.experience > self.calculate_level_requirement(self.level):
                self.level += 1
                self.change_level = True
            else:
                level_loop = False
        
        self.determine_rank()
        curs_lvl.execute('UPDATE levelsInfo SET level=?, experience=?, rank=? WHERE name=?', (self.level, self.experience, self.rank, self.user))
        conn_lvl.commit()
        return True
        
    def determine_rank(self) -> None:
        """ Determines rank title based on level """
        for group in RANK_TITLES:
            # print(f'rank title: {RANK_TITLES[group]}')
            if self.level < int(group):
                self.rank = RANK_TITLES[group]
                self.change_rank = True
                return 
        
    @staticmethod
    def calculate_level_requirement(level:int) -> int:
        """ Find total XP required to level up """
        return round((BASE_XP_REQUIREMENT * level ** EXP_FACTOR),0)

    def xp_calculator(self) -> int:
        """ Determines amount of XP based on accuracy and streak """
        if not self.accuracy:
            return 0
        elif self.accuracy:
            if self.streak > 1:
                return self.calculate_streak_reward()
            else:
                return 1
            
    def calculate_streak_reward(self) -> int:
        # print(f'streak: {self.streak}')
        streak_multiplier = (BASE_STREAK_MULTIPLIER + self.streak * STREAK_LEVEL_MULTIPLIER) ** STREAK_FACTOR
        # print(f'streak multiplier: {streak_multiplier}')
        return round((BASE_XP_REWARD * streak_multiplier),0)
    
    def profile_display(self) -> tuple:
        """ Returns string format for Profile Card """
        lvl_prog = f'{int(self.experience)}/{int(self.level_up_req)}'
        return f'{self.level} ({lvl_prog})', self.rank
    

if __name__ == '__main__':
    pass