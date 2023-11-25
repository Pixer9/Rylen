# logger.py
import logging

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.error or record.levelno == logging.exception:
            record.message = f"{record.module} - {record.msg}"
        return super().format(record)
    
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    filename="Rylen_Bot_Log.txt",
    filemode='a'
)

logger = logging.getLogger(__name__)

custom_formatter = CustomFormatter()

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(custom_formatter)

logger.addHandler(stream_handler)