# logger.py
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import os

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.error or record.levelno == logging.exception:
            record.message = f"{record.module} - {record.msg}"
        return super().format(record)

logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[]
)

logger = logging.getLogger(__name__)

custom_formatter = CustomFormatter()

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(custom_formatter)

logger.addHandler(stream_handler)

# Add TimedRotatingFileHandler
log_filename = os.path.join(logs_dir, datetime.datetime.now().strftime('%m-%d-%y') + ".txt")
file_handler = TimedRotatingFileHandler(filename=log_filename, when="midnight", interval=1, backupCount=0)
file_handler.setFormatter(custom_formatter)
logger.addHandler(file_handler)