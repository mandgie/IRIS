import logging
import os
from datetime import datetime
from pathlib import Path
from ..config import PROJECT_ROOT, LOG_LEVEL

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and better formatting"""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    logs_dir = Path(PROJECT_ROOT) / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create a new log file for each run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"agent_run_{timestamp}.log"
    
    # Setup handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(CustomFormatter())
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    
    # Setup root logger
    logger = logging.getLogger('goal_agent')
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Initial log entries
    logger.info("=" * 50)
    logger.info("Starting new agent run")
    logger.info("=" * 50)
    
    return logger