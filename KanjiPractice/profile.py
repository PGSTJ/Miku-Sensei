import discord
import logging
import traceback
from typing import Dict


from Database.utils import curs, conn, PROFILE_ATTRIBUTES
from Background.ServerUtils import current_time
from Leveling import utils as lvl

logger = logging.getLogger('JPGen')
logger_pfu = logging.getLogger('PFU')

ttl = logging.getLogger('TT')

class DeleteProfile(discord.ui.View):
    def __init__(self, user:str):
        super().__init__()
        self.user = user
        
    @discord.ui.button(label='Delete Profile', style=discord.ButtonStyle.red)
    async def delete_profile(self, interaction: discord.Interaction, button:discord.ui.Button):
        delete_profile(self.user)
        await interaction.response.send_message('Your profile has been deleted.')

    @discord.ui.button(label='Keep Profile', style=discord.ButtonStyle.blurple)
    async def keep_profile(self, interaction: discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message('Your profile lives another day.')



def create_profile(user: str) -> bool:
    """
    Creates japanese learner profile as defined above

    :param user: discord name as str
    """
    try:
        lvl.upsert_info(user)
        level_descr, rnk = '0 (0/0)', 'unranked'
        curs.execute('INSERT INTO profiles(name, level, total_correct, total_incorrect, total_answered, streak, achievements, rank, created) VALUES (?,?,?,?,?,?,?,?,?)', (user, level_descr, 0, 0, 0, 0, 0, rnk, current_time()))
        conn.commit()

        logger.info(f'{user} created a JapaneseLearner profile')

        return True
    except:
        traceback.print_exc()
        logger.error(f'Error creating {user}\'s JapaneseLearner profile')

def delete_profile(user:str):
    """
    Delete specified user profile from DB

    :param user: str of user name
    :return: bool confirmation
    """
    curs.execute('DELETE FROM profiles WHERE name=?', (user,))
    conn.commit()
    logger.info(f'{user}\'s profile has been deleted.')

def profile_embed(user:discord.Member) -> discord.Embed:
    """
    Creates and formats profile embed sent on command to view stats

    :param user: name of user as string to locate in DB
    :return: discord.Embed of profile info
    """
    user_info = [info for info in curs.execute('SELECT * FROM profiles WHERE name=?', (user.name,))][0]

    # set/create attributes
    level = f'Level: {user_info[1]}'
    record = f'{user_info[2]} - {user_info[3]}'
    if user_info[7] == 0:
        rank = 'Unranked'
    else:
        rank = f'{user_info[7]}'
    try:
        ci_ratio = float(user_info[2] / user_info[3])
    except ZeroDivisionError:
        ci_ratio = 0.0


    profile = discord.Embed(title=f'Japanese Practice Profile - {user.name}', color=discord.Colour.from_rgb(34,225,197), description=f'{level} | {rank}')

    profile.add_field(name='Record', value=record)
    profile.add_field(name='Streak', value=user_info[5])
    profile.add_field(name='Questions Answered', value=user_info[4])

    profile.add_field(name='C/I ratio', value=ci_ratio)
    profile.add_field(name='Achievements', value=user_info[6])

    profile.set_thumbnail(url=user.avatar)

    logger.info(f'{user}\'s profile was viewed')
    return profile

def update_value(name:str, *attributes) -> bool:
    """
    Update any value in profile DB

    :param value: optional list with various values to update

    - level
    - total_correct
    - total_incorrect
    - total_answered
    - streak
    - achievements
    - rank
    - resetStreak

    :return: bool confirmation of success or not
    """
    current_values = _current_profile_attributes(name)

    try:
        for category in attributes[0]:
            if category == 'resetStreak':
                curs.execute('UPDATE profiles SET streak=? WHERE name=?', (0, name))
                logger_pfu.info(f'{name} streak reset', extra={'category':'reset streak', 'time':current_time()})
            else: 
                new = current_values[category] + 1
                curs.execute(f'UPDATE profiles SET {category}=? WHERE name=?', (new, name))
                logger_pfu.info(f'{name} {category} updated', extra={'category':category, 'time':current_time()})
        
        conn.commit()
        return True
    except:
        traceback.print_exc()
        return False
    
def _current_profile_attributes(name:str) -> Dict[str, int]:
    """ Creates formatted dictionary of current profile values"""
    current_values = list([info for info in curs.execute('SELECT * from profiles WHERE name=?', (name,))][0])
    
    # index of category in PROFILE_ATTRIBUTES is mapped to order of columns extracted from DB
    return {cat:current_values[PROFILE_ATTRIBUTES.index(cat) + 1] for cat in PROFILE_ATTRIBUTES}




def validation(name:str) -> bool:
    """
    Checks of profile exists in DB. True/valid if exists.

    :param name: str of users name to check against DB
    :return: bool validation
    """

    registered_users = [users[0] for users in curs.execute('SELECT name FROM profiles')]
    if name in registered_users:
        return True
    else:
        return False
    
def get_attribute(user:str, *attributes) -> list:
    """
    Extracts specified profile attributes
    
    optional list with various values to update

    - level
    - total_correct
    - total_incorrect
    - total_answered
    - streak
    - achievements
    - rank
    - resetStreak
    """
    cols = ''
    for attr in attributes[0]:
        if attr in PROFILE_ATTRIBUTES:
            cols + f', {attr}'

    all = [attr for attr in attributes[0] if attr in PROFILE_ATTRIBUTES]
    if len(all) > 1:
        cols = ','.join(all)
    else:
        cols = all[0]
    return [info for info in curs.execute(f'SELECT {cols} FROM profiles WHERE name=?', (user,))][0]

    
def _update_level_rank(user:str, level:str=False, rank:str=False):
    if level:
        curs.execute('UPDATE profiles SET level=? WHERE name=?', (level, user))
    if rank:
        curs.execute('UPDATE profiles SET rank=? WHERE name=?', (rank, user))
    conn.commit()
    return True