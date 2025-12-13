import logging
import logging.handlers
import sys
from pathlib import Path

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "bot.log"

# ====== FORMAT ======
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ====== STDOUT (for Docker logs) ======
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# ====== FILE ROTATION (keep last 10 files, 5MB each) ======
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=10, encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# ====== ROOT LOGGER ======
logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler], force=True)

def create_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
