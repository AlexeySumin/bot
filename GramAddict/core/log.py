import logging
import os
from colorama import Fore, Style
from colorama import init as init_colorama
from logging import LogRecord
from logging.handlers import RotatingFileHandler
from uuid import uuid4

COLORS = {
    "DEBUG": Style.DIM,
    "INFO": Fore.WHITE,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.MAGENTA,
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, *, fmt, datefmt=None):
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)

    def format(self, record):
        msg = super().format(record)
        levelname = record.levelname
        if hasattr(record, "color"):
            return f"{record.color}{msg}{Style.RESET_ALL}"
        if levelname in COLORS:
            return f"{COLORS[levelname]}{msg}{Style.RESET_ALL}"
        return msg


class LoggerFilterGramAddictOnly(logging.Filter):
    def filter(self, record: LogRecord):
        return record.name.startswith("GramAddict")


def create_log_file_handler(filename):
    file_handler = RotatingFileHandler(
        filename,
        mode="a",
        backupCount=10,
        maxBytes=1000000,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)8s | %(message)s (%(filename)s:%(lineno)d)",
            datefmt=r"[%m/%d %H:%M:%S]",
        )
    )
    file_handler.addFilter(LoggerFilterGramAddictOnly())
    return file_handler


def configure_logger():
    global g_session_id
    global g_log_file_name
    global g_logs_dir
    global g_file_handler

    g_session_id = uuid4()
    g_logs_dir = "logs"
    g_log_file_name = f"{g_session_id}.log"

    init_colorama()

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console logger (limited but colored log)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        ColoredFormatter(
            fmt="%(asctime)s %(levelname)8s | %(message)s", datefmt="[%m/%d %H:%M:%S]"
        )
    )
    console_handler.addFilter(LoggerFilterGramAddictOnly())
    root_logger.addHandler(console_handler)

    # File logger (full raw log)
    if not os.path.exists(g_logs_dir):
        os.makedirs(g_logs_dir)
    g_file_handler = create_log_file_handler(f"{g_logs_dir}/{g_log_file_name}")
    root_logger.addHandler(g_file_handler)

    init_logger = logging.getLogger(__name__)
    init_logger.debug(f"Initial log file: {g_logs_dir}/{g_log_file_name}")


def get_log_file_config():
    return g_log_file_name, g_logs_dir, g_file_handler, g_session_id


def update_log_file_name(username: str):
    unamed_log_file_name, logs_dir, file_handler, _ = get_log_file_config()
    unamed_full_filename = f"{logs_dir}/{unamed_log_file_name}"

    init_logger = logging.getLogger(__name__)
    if not username:
        init_logger.error(f"No username found, using log file {unamed_full_filename}")
        return
    named_log_file_name = f"{username}.log"
    named_full_filename = f"{logs_dir}/{named_log_file_name}"
    rollover = False
    if os.path.isfile(named_full_filename):
        rollover = True

    named_file_handler = create_log_file_handler(named_full_filename)
    if rollover:
        named_file_handler.doRollover()

    # copy existing runtime logs (uidd4.log) to named log file (username.log)
    with open(unamed_full_filename, "r") as unamed_file, open(
        named_full_filename, "a"
    ) as named_file:
        for line in unamed_file:
            named_file.write(line)

    root_logger = logging.getLogger()
    root_logger.removeHandler(file_handler)
    os.remove(unamed_full_filename)
    root_logger.addHandler(named_file_handler)
    root_logger.debug(f"Updated log file: {named_full_filename}")

    global g_log_file_name
    global g_file_handler
    g_log_file_name = named_log_file_name
    g_file_handler = named_file_handler
