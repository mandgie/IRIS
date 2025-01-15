import logging
import os
from datetime import datetime
from pathlib import Path
from ..config import PROJECT_ROOT, LOG_LEVEL

class SingletonLogger:
    _instance = None
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._setup_logger()
        return cls._logger

    @classmethod
    def _setup_logger(cls):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = Path(PROJECT_ROOT) / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create a new log file for each run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"agent_run_{timestamp}.log"
        
        # Setup handler
        file_handler = logging.FileHandler(log_file, mode='w', delay=False)
        file_handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        
        # Setup logger
        cls._logger = logging.getLogger('goal_agent')
        cls._logger.setLevel(LOG_LEVEL)
        cls._logger.addHandler(file_handler)
        
        # Initial log entries
        cls._logger.info("=" * 50)
        cls._logger.info("Starting new agent run")
        cls._logger.info("=" * 50)

def setup_logging():
    """Get or create the singleton logger"""
    return SingletonLogger.get_logger()