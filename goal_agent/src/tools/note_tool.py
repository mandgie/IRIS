import sqlite3
from datetime import datetime
import json
from typing import Dict, Any
from .base import BaseTool, ToolType
from ..config import DB_PATH

class NoteTool(BaseTool):
    def __init__(self):
        super().__init__("note_taking", ToolType.INFORMATION)
        self.db_path = DB_PATH
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        
        if action == "write":
            content = params.get("content")
            if not content:
                return {"status": "error", "message": "Content is required for write action"}
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO notes (content, timestamp, category, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (
                        content,
                        datetime.now().isoformat(),
                        params.get("category", "general"),
                        json.dumps(params.get("metadata", {}))
                    ))
                    note_id = cursor.lastrowid
                    
                    return {
                        "status": "success", 
                        "note": {
                            "id": note_id,
                            "content": content,
                            "timestamp": datetime.now().isoformat(),
                            "category": params.get("category", "general")
                        }
                    }
            except Exception as e:
                return {"status": "error", "message": f"Database error: {str(e)}"}
            
        elif action == "read":
            category = params.get("category")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    if category:
                        cursor.execute("SELECT * FROM notes WHERE category = ? ORDER BY timestamp DESC", (category,))
                    else:
                        cursor.execute("SELECT * FROM notes ORDER BY timestamp DESC")
                    
                    notes = [dict(row) for row in cursor.fetchall()]
                    return {"status": "success", "notes": notes}
                    
            except Exception as e:
                return {"status": "error", "message": f"Database error: {str(e)}"}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def get_description(self) -> str:
        return """
        Note Taking Tool
        Actions:
        - write: Create a new note
          Parameters: {"action": "write", "content": "note content", "category": "optional category"}
        - read: Read notes
          Parameters: {"action": "read", "category": "optional category filter"}
        """