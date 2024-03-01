import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import os

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            record.message = f"{record.module} - {record.msg}"
        else:
            self._style = logging.PercentStyle("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s")
        return super().format(record)

logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
)

logger = logging.getLogger(__name__)

custom_formatter = CustomFormatter()

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(custom_formatter)
logger.addHandler(stream_handler)

# Add TimedRotatingFileHandler to auto-rotate log files
log_filename = os.path.join(logs_dir, datetime.datetime.now().strftime('%m-%d-%y') + ".txt")
file_handler = TimedRotatingFileHandler(filename=log_filename, when="midnight", backupCount=20)
file_handler.setFormatter(custom_formatter)
logger.addHandler(file_handler)
