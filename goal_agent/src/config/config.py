"""
Main configuration file for the goal agent.
Contains environment variables, paths, and general settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the project root directory
PROJECT_ROOT = os.getenv('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Database configuration
DB_NAME = os.getenv('DB_NAME', 'goal_agent.db')
DB_PATH = os.path.join(PROJECT_ROOT, DB_NAME)

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Agent configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '3600'))  # Default 1 hour in seconds
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Create data directory if it doesn't exist
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
