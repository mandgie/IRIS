from .base import ToolRegistry, ToolType
from .calculator_tool import CalculatorTool
from .note_tool import NoteTool
from .todo_tool import TodoTool

def get_tool_registry() -> ToolRegistry:
    """Create and return a ToolRegistry with all available tools registered"""
    registry = ToolRegistry()
    
    # Register all available tools
    registry.register_tool(CalculatorTool())
    registry.register_tool(NoteTool())
    registry.register_tool(TodoTool())
    
    return registry 