from . import utils
from pythonjsonlogger import jsonlogger

formatting = {
    'General': {
        'name': 'JPGen',
        'level': 10,
        'format': "%(name)s:%(asctime)s:%(levelname)s:%(message)s",
        'file_path': utils.GENERAL_LOG

    }
}


json_formatting = {
    'SubmissionJSON' : {
        'name': 'JPSub',
        'level': 10,
        'format': jsonlogger.JsonFormatter(static_fields={'logger':'Submission'}),
        'file_path': utils.JAPANESE_PRACTICE_LOG
        
    },
    'profile_update': {
        'name': 'PFU',
        'level': 10,
        'format': jsonlogger.JsonFormatter(static_fields={'logger':'PFU'}),
        'file_path': utils.JAPANESE_PRACTICE_LOG
    }

}

def init() -> bool:
    if utils.init(formatting, json_formatting):
        return True
    else:
        return False
        #TODO: custom error?
