from typing import Any, Dict, Optional
import json
from pathlib import Path

class Memory:
    def __init__(self, storage_path: str = "../data/memory.json"):
        self.storage_path = Path(storage_path)
        self.memory_data = self._load_memory()
        
    def _load_memory(self) -> Dict:
        """Load memory from storage."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save(self) -> None:
        """Save memory to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.memory_data, f)
    
    def add(self, key: str, value: Any) -> None:
        """Add item to memory."""
        self.memory_data[key] = value
        self.save()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from memory."""
        return self.memory_data.get(key) 