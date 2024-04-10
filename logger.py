from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
#from utility import config
from config import LoggerConfig as lc
import logging
import time
import os

class BaseLogger(object):

    logs_dir = lc.LOGS_DIR

    def __init__(self) -> None:
        # Ensure log directory exists - this is where all written logs will go
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

    
    def setup_logger(self, logger_name: str, file_name: str, log_format: str, handler_type: str, level=logging.INFO):
        logger = logging.getLogger(logger_name)

        if handler_type == "timed":
            handler = TimedRotatingFileHandler(
                filename=os.path.join(self.logs_dir, file_name),
                when=lc.WHEN,
                interval=1,
                backupCount=lc.BACKUP_COUNT,
                encoding=lc.ENCODING,
                delay=lc.DELAY,
                utc=lc.USE_UTC
            )
        else:
            handler = logging.FileHandler(os.path.join(self.logs_dir, file_name), encoding="utf-8")

        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)
        logger.setLevel(level)
        return logger
    

class MainLogger(BaseLogger):

    def __init__(self) -> None:
        super().__init__()
        self.logger = self.setup_logger(
            'main_logger',
            f"{lc.LOG_PREFIX}-debug-log.log",
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
            handler_type="timed",
            level=logging.INFO
        )


class UserLogger(BaseLogger):

    def __init__(self) -> None:
        super().__init__()
        self.logger = self.setup_logger(
            'user_logger',
            f"{lc.LOG_PREFIX}-user-log.log",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handler_type="file",
            level=logging.INFO
        )


main_logger = MainLogger().logger
user_logger = UserLogger().logger