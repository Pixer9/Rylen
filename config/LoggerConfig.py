
# Log prefix - current uses bot name
LOG_PREFIX = "Rylen"

# Director name of where logs will be stored
LOGS_DIR = "logs"

# When do you want logs to be rolled over?
WHEN = "midnight"

# The amount of logs stored before deletion of old logs
BACKUP_COUNT = 10

# Encoding used for log files
ENCODING = "UTF-8"

# Set the delay between closing a file stream and opening the next
DELAY = False

# If False, will measure time using calculated local time
USE_UTC = False

# Time to rotate logs - if timed based
AT_TIME = None

# Log level threshold
LOG_LEVEL = "INFO"
