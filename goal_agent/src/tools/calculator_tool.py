from typing import Dict, Any
from .base import BaseTool, ToolType

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