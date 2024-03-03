import logging
from logging.handlers import TimedRotatingFileHandler
from utility import config
import os

# Ensure log directory exists - this is where all written logs will go
logs_dir = "logs" 
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

log_filename = os.path.join(logs_dir, config.BOT_NAME + "-logs.txt")

# Set up logger
logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()

file_handler = TimedRotatingFileHandler(filename=log_filename, when="midnight", backupCount=20)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[stream_handler, file_handler] 
)