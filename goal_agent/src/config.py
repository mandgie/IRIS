from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Agent configuration
AGENT_CONFIG = {
    "max_steps": 10,
    "temperature": 0.7,
    "model_name": "gpt-3.5-turbo"  # or your preferred model
}

# Memory configuration
MEMORY_CONFIG = {
    "storage_path": str(DATA_DIR / "memory.json")
} 