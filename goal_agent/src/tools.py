# goal_agent/src/tools.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from enum import Enum
import json
from datetime import datetime

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

    def get_description(self) -> str:
        """Return a description of what the tool does and how to use it"""
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

# Example implementation of a simple tool
class NoteTool(BaseTool):
    def __init__(self):
        super().__init__("note_taking", ToolType.INFORMATION)
        self.notes = []
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        if action == "write":
            note = {
                "content": params.get("content"),
                "timestamp": datetime.now().isoformat()
            }
            self.notes.append(note)
            return {"status": "success", "note": note}
        elif action == "read":
            return {"status": "success", "notes": self.notes}
        else:
            return {"status": "error", "message": "Invalid action"}

    def get_description(self) -> str:
        return """
        Note Taking Tool
        Actions:
        - write: Create a new note
          Params: {"action": "write", "content": "note content"}
        - read: Read all notes
          Params: {"action": "read"}
        """

# Example of a calculation tool
class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__("calculator", ToolType.ANALYSIS)
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get("operation")
        numbers = params.get("numbers", [])
        
        if operation == "average":
            result = sum(numbers) / len(numbers) if numbers else 0
            return {"status": "success", "result": result}
        # Add more operations as needed
        
        return {"status": "error", "message": "Invalid operation"}

    def get_description(self) -> str:
        return """
        Calculator Tool
        Operations:
        - average: Calculate average of numbers
          Params: {"operation": "average", "numbers": [1, 2, 3]}
        """