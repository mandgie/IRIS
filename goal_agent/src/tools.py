from abc import ABC, abstractmethod
from typing import Dict, List, Any
from enum import Enum
from datetime import datetime
import json
import sqlite3
from .config import DB_PATH

class ToolType(Enum):
    MEMORY = "memory"
    ANALYSIS = "analysis"
    INFORMATION = "information"
    PLANNING = "planning"
    INTEGRATION = "integration"

class BaseTool(ABC):
    def __init__(self, name: str, tool_type: ToolType):
        self.name = name
        self.tool_type = tool_type
        self.last_used = None

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self._tools.keys())
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """Get all tools of a specific type"""
        return [tool for tool in self._tools.values() if tool.tool_type == tool_type]

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

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__("calculator", ToolType.ANALYSIS)
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get("operation")
        numbers = params.get("numbers", [])
        
        if not numbers:
            return {"status": "error", "message": "Numbers are required"}
            
        try:
            if operation == "average":
                result = sum(numbers) / len(numbers)
            elif operation == "sum":
                result = sum(numbers)
            elif operation == "min":
                result = min(numbers)
            elif operation == "max":
                result = max(numbers)
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
            return {"status": "success", "result": result}
            
        except Exception as e:
            return {"status": "error", "message": f"Calculation error: {str(e)}"}
    
    def get_description(self) -> str:
        return """
        Calculator Tool
        Operations:
        - average: Calculate average of numbers
          Parameters: {"operation": "average", "numbers": [1, 2, 3]}
        - sum: Calculate sum of numbers
          Parameters: {"operation": "sum", "numbers": [1, 2, 3]}
        - min: Find minimum value
          Parameters: {"operation": "min", "numbers": [1, 2, 3]}
        - max: Find maximum value
          Parameters: {"operation": "max", "numbers": [1, 2, 3]}
        """