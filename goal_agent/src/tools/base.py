from abc import ABC, abstractmethod
from typing import Dict, List, Any
from enum import Enum

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