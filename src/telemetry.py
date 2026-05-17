import logging
import os
from datetime import datetime

# Ensure logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "telemetry.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("telemetry")

def log_event(event: str, **kwargs):
    """Log a telemetry event with optional key/value pairs."""
    details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    if details:
        logger.info(f"{event} | {details}")
    else:
        logger.info(event)
