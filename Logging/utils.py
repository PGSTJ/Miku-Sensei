import logging


GENERAL_LOG = 'Logging\\records\\general.log'
JAPANESE_PRACTICE_LOG = 'Logging\\records\\kanji.log'
ERROR_LOG = 'Logging\\records\\error.log'

LOGGERS = []

class LoggerFormatting():
    """
    ABC

    :param format: should be a format string for a regular python logs OR a ```JsonFormatter``` object for JSON logs
    """
    def __init__(self, format_dict:dict) -> None:
        self.name = format_dict['name']
        self.level = format_dict['level']
        self.file_path = format_dict['file_path']

        if 'format' in format_dict:
            self.format = format_dict['format']
        else:
            self.format = ''


# def create_logger(self, name:str, format:str, file_path:str, level:int) -> logging.Logger:
def create_logger(formatting:LoggerFormatting) -> logging.Logger:
    
    logger = logging.getLogger(formatting.name)
    logger.setLevel(formatting.level)

    formatter = logging.Formatter(formatting.format)

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(formatting.level)
    logger.addHandler(streamHandler)

    fileHandler = logging.FileHandler(formatting.file_path, encoding='utf-8')
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(formatting.level)
    logger.addHandler(fileHandler)


    return logger


def create_json_logger(formatting:LoggerFormatting) -> logging.Logger:
    logger = logging.getLogger(formatting.name)
    logger.setLevel(formatting.level)

    formatter = formatting.format

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(formatting.level)
    logger.addHandler(streamHandler)

    fileHandler = logging.FileHandler(formatting.file_path)
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(formatting.level)
    logger.addHandler(fileHandler)

    return logger

def lal():
    """ Prints all active loggers in system """
    all = [l for l in logging.Logger.manager.loggerDict.values() if isinstance(l, logging.Logger)]
    for i in all:
        print(i)

def init(regularformat:dict=None, jsonformat:dict=None):
    if regularformat:
        for formats in regularformat:
            format = LoggerFormatting(format_dict=regularformat[formats])
            create_logger(format)
            LOGGERS.append(format.name)
    if jsonformat:
        for formats in jsonformat:
            format = LoggerFormatting(jsonformat[formats])
            create_json_logger(format)
        LOGGERS.append(format.name)
    return True



def disable_logger(logger_name:str):
    logger = logging.getLogger(logger_name)
    
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    logger.disabled = True

    return True

def ttl():
    logger = logging.getLogger('TT')
    logger.setLevel(30)

    formatter = logging.Formatter("[%(asctime)s]%(name)s:%(levelname)s:%(message)s")

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(30)
    logger.addHandler(streamHandler)

    fileHandler = logging.FileHandler(ERROR_LOG)
    fileHandler.setFormatter(formatter)
    streamHandler.setLevel(30)
    logger.addHandler(fileHandler)

    return logger
