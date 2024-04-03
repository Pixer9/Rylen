from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
#from utility import config
from config import LoggerConfig as lc
import logging
import time
import os

# Ensure log directory exists - this is where all written logs will go

if not os.path.exists(lc.LOGS_DIR):
    os.makedirs(lc.LOGS_DIR)
'''
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    
    def __init__(self, 
                 dir_name: str=lc.LOGS_DIR, 
                 when: str=lc.WHEN, 
                 backupCount: int=lc.BACKUP_COUNT, 
                 encoding: str=lc.ENCODING, 
                 delay: bool=lc.DELAY,
                 utc: bool=lc.USE_UTC,
                 atTime: datetime=lc.AT_TIME) -> None:
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
        currentTime = int(time.time())
        t = self.rolloverAt - self.interval

        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstNow = time.localtime(currentTime)[-1]
            dstThen = timeTuple[-1]

            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        
        if self.stream:
            self.stream.close()
            self.stream = None

        self.baseFileName = self.get_new_log_file()
        self.rotate(self.baseFileName, '')

        if not self.delay:
            self.stream = self._open()

        self.rolloverAt = self.computeRollover(currentTime)


log_filename = os.path.join(lc.LOGS_DIR, f"{lc.LOG_PREFIX}-log-{datetime.now().strftime('%Y-%m-%d')}.txt")

logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()

file_handler = CustomTimedRotatingFileHandler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[stream_handler, file_handler]
)
'''

class MidnightRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when=lc.WHEN, interval=1, backupCount=lc.BACKUP_COUNT, encoding=lc.ENCODING, delay=lc.DELAY, utc=lc.USE_UTC) -> None:
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)
        self.suffix_time = datetime.now().strftime("%Y-%m-%d")

    def shouldRollover(self, record):
        now = datetime.now()
        if now.strftime("%Y-%m-%d") != self.suffix_time:
            return 1
        return 0
    
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        self.baseFileName = self.baseFileName.replace(self.suffix_time, datetime.now().strftime("%Y-%m-%d"))
        self.mode = 'a'
        self.stream = self._open()

logger = logging.getLogger(__name__)
log_filename = os.path.join(lc.LOGS_DIR, f"{lc.LOG_PREFIX}-log.log")

stream_handler = logging.StreamHandler()

file_handler = TimedRotatingFileHandler(filename=log_filename, when=lc.WHEN, interval=1, backupCount=lc.BACKUP_COUNT, encoding=lc.ENCODING, delay=lc.DELAY, utc=lc.USE_UTC, atTime=None)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[stream_handler, file_handler]
)