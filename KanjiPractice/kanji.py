import random
import datetime
import traceback
import logging

from Database.utils import curs, conn
from . import profile as pf

import discord

log_JPGen = logging.getLogger('JPGen')
ttl = logging.getLogger('TT')


class EmbedCreation():
    """ ABC for embed creations"""
    MIKU_FOLDER = 'photos\\miku'

    def create_embed(self, type:str, **modifiers) -> discord.Embed:
        """
        Creates and formats embeds

        if :param type: is 'kanji presentation', modifiers MUST contain keys:
        - current: str

        if :param type: is 'kanji submission', modifiers MUST contain keys:
        - user: discord.User | Member
        - accuracy: bool
        - message: str

        if :param type: is 'maxed submissions'. modifiers MUST contain keys:
        - translation: str
        - pronunciation: str
        """

        embed = discord.Embed(title='Embed', color=discord.Colour.from_rgb(34,225,197))

        if type == 'kanji presentation':
            embed.title = 'Kanji Practice'
            kanji = modifiers['current']
            question = modifiers['question']
            embed.add_field(name=question, value=kanji)

        elif type == 'maxed submissions':
            embed.title = 'Current Kanji Answer'
            embed.description = 'ran outta tries my man'
            translation = modifiers['translation']
            pronunciation = modifiers['pronunciation']

            embed.add_field(name='Translation', value=translation)
            embed.add_field(name='Pronunciation', value=pronunciation)

        return embed
        





class KanjiPresentation(EmbedCreation):
    """Responsible for presenting and logging current kanji data"""
    

    def __init__(self) -> None:
        super().__init__()    
        self.choose_kanji()

        self.question = self._select_question(self.question_idx)

    def choose_kanji(self) -> bool:
        """
        Pulls random kanji from DB to send in embed every 30 minutes, updates DB with what kanji was chosen and sets seenInCycle to True;
            this allows every kanji in DB to be seen at least once before looping;
            if all kanji has been shown, resets marker and chooses again
            logs what kanji was sent for verification
            called in kanji_embed

        :param loop: bool value default to True to start while loop
        :return: str containing randomly chosen kanji
        """
        # reset current kanji designation
        curs.execute('UPDATE kanjiCD SET current=?', (False,))
        
        self.kanji_id, self.question_idx = self._available_kanji()
        print(self.kanji_id)

        # update object attributes
        self.current_kanji = [char[0] for char in curs.execute('SELECT kanji FROM kanjiBD WHERE id=?',(self.kanji_id,))][0]
        self.ck_timestamp = datetime.datetime.now()
        
        # update logs
        log_JPGen.info(f'{self.current_kanji} presented to server')

        # update DB that chosen word has been shown
        curs.execute('UPDATE kanjiCD SET current=?, time_current=? WHERE id=?', (True, self.ck_timestamp, self.kanji_id))
        conn.commit()
            
    def _available_kanji(self, loop=True) -> list | bool:
        """ Extracts all available kanji for a question and resets if none available """
        while loop:
            try:
                kanji_packages = [info for info in curs.execute('SELECT id, asked_translation, asked_pronunciation, asked_verb FROM kanjiCD WHERE asked_translation=? OR asked_pronunciation=? OR asked_verb=?', (False, False, False))]
                selected_package = list(random.choice(kanji_packages))
                question_idx = self._question_determination(selected_package)
                kanji_id = selected_package[0]

                self._update_question_tracking(kanji_id, question_idx)
                
                loop = False
                return kanji_id, question_idx
                
            except IndexError:
                # reset after everything has been seen
                curs.execute('UPDATE kanjiCD SET asked_translation=?, asked_pronunciation=?, asked_verb=?', (False, False, False))
                conn.commit()
                log_JPGen.info('Kanji reset')
            except:
                traceback.print_exc()
                return False
        
    def _select_question(self, question_idx:int) -> str:
        """ Selects question message content based on question index """
        QUESTIONS = {
            1: 'What is the translation of the kanji below?',
            2: 'What is the pronunciation of the kanji below?',
            3: 'Is this a transitive or intransitive verb?'
        }

        return QUESTIONS[question_idx]
    
    def _question_determination(self, q_package:list):
        """ Organizes current question data and randomly chooses a question based on status """
        # determine if kanji is a verb; if not, removes verb question option/consideration
        self.verb_type = [info[0] for info in curs.execute('SELECT verb FROM kanjiBD where id=?', (q_package[0],))][0]

        if not self.verb_type:
            formatted_group = enumerate(q_package[1:-1])
            curs.execute('UPDATE kanjiCD set asked_verb=? WHERE id=?', (True, q_package[0]))
            conn.commit()
        else:
            formatted_group = enumerate(q_package[1:])
        
        # print(self.verb_type)

        # extract saved indices pertaining to available questions - will map selected question index to question type
        organized_questions = [q_pair[0] for q_pair in formatted_group if q_pair[1] == 0]
        # print(f'org_qs: {organized_questions}')
        q_i = random.choice(organized_questions)
        return q_i + 1
    
    def _update_question_tracking(self, kid:str, q_idx:int):
        """ Updates asked_question status of DB to ensure no repeats until all have been seen/asked """
        if q_idx == 1:
            col = 'asked_translation'
        elif q_idx == 2:
            col = 'asked_pronunciation'
        elif q_idx == 3:
            col = 'asked_verb'

        curs.execute(f'UPDATE kanjiCD SET {col}=? WHERE id=?', (True, kid))
        conn.commit()
        return True

        
        
        
            
    def get_kanji_embed(self):
        """ Sends embed from constructor function """
        return self.create_embed(type='kanji presentation', current=self.current_kanji, question=self.question)
    

def current_kanji() -> list:
    """Returns: list with following order: kanji, translation, pronunciation, verb, time set ck"""
    id = [info for info in curs.execute('SELECT id, time_current FROM kanjiCD WHERE current=?', (True,))][0]
    ck = [info for info in curs.execute('SELECT kanji, translation, pronunciation, verb FROM kanjiBD WHERE id=?', (id[0],))][0]
    # print(f'ck id: {id[1]}')
    if ck:
        return list(ck) + [id[1]]
    else:
        return None

class SubmissionMenu(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label='Translation', style=discord.ButtonStyle.green)
    async def translation(self, interaction: discord.Interaction, button:discord.ui.Button):
        ck = current_kanji()
        await interaction.response.send_message(ck[1])


    @discord.ui.button(label='Pronunciation', style=discord.ButtonStyle.blurple)
    async def pronunciation(self, interaction: discord.Interaction, button:discord.ui.Button):
        ck = current_kanji()
        await interaction.response.send_message(ck[2])
            