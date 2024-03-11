from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
#from utility import config
from config import LoggerConfig as lc
import logging
import os

# Ensure log directory exists - this is where all written logs will go
if not os.path.exists(lc.LOGS_DIR):
    os.makedirs(lc.LOGS_DIR)

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    
    def __init__(self, 
                 dir_name: str=lc.LOGS_DIR, 
                 when: str=lc.WHEN, 
                 backupCount: int=lc.BACKUP_COUNT, 
                 encoding: str=lc.ENCODING, 
                 delay: bool=lc.DELAY,
                 utc: bool=lc.USE_UTC,
                 atTime: str=lc.AT_TIME) -> None:
        self.dir_name = dir_name
        self.when = when
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        self.encoding = encoding
        self.delay = delay
        file_name = self.get_new_log_file()
        super().__init__(filename=file_name, when=when, backupCount=backupCount, encoding=encoding, delay=delay, utc=utc, atTime=atTime)


    def get_new_log_file(self):
        """ Generates a log file name based on the current date. """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.dir_name, f"{lc.LOG_PREFIX}-log-{date_str}.txt")
    

    def doRollover(self) -> None:
        """
            Overridden method to change the way the new log file is named and
            avoid appending the date as a suffix.
        """
        self.stream.close()
        self.baseFileName = self.get_new_log_file()
        if not self.delay:
            self.stream = self._open()


log_filename = os.path.join(lc.LOGS_DIR, f"{lc.LOG_PREFIX}-log-{datetime.now().strftime('%Y-%m-%d')}.txt")

logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()

file_handler = CustomTimedRotatingFileHandler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[stream_handler, file_handler]
)