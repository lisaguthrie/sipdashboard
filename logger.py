DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
levels = {DEBUG: "DEBUG", INFO: "INFO", WARNING: "WARNING", ERROR: "ERROR"}
LOGLEVEL = INFO

def log_message(loglevel: int, logmessage: str):
    """Simple logging function with levels"""
    if (loglevel >= LOGLEVEL):
        print(f"[{levels.get(loglevel, 'LOG')}] {logmessage}")