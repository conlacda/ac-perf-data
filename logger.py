import logging
from logging.handlers import TimedRotatingFileHandler

# Create a TimedRotatingFileHandler
log_filename = "logs.txt"
log_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s from %(filename)s line %(lineno)d"
)
handler = TimedRotatingFileHandler(
    log_filename, when="midnight", interval=1, backupCount=7
)  # rotate daily, keep 7 days of logs
handler.setFormatter(log_formatter)

# Add the handler to the root logger
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
