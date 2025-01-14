# goal_agent/src/agent.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from .tools import ToolRegistry, NoteTool, CalculatorTool
from .llm import LLMInterface
import json

@dataclass
class Goal:
    description: str
    success_criteria: Dict[str, any]
    target_date: datetime

class Agent:
    def __init__(self, goal: Goal, api_key: str):
        self.goal = goal
        self.last_action_time = None
        self.memory = []
        self.tool_registry = ToolRegistry()
        self.llm = LLMInterface(api_key)
        
        # Register default tools
        self.tool_registry.register_tool(NoteTool())
        self.tool_registry.register_tool(CalculatorTool())
    
    def analyze_situation(self) -> Dict:
        """Analyze current situation and return structured analysis"""
        current_time = datetime.now()
        time_since_last_action = None if not self.last_action_time else \
            (current_time - self.last_action_time).total_seconds() / 3600  # in hours
        
        return {
            "timestamp": current_time.isoformat(),
            "time_since_last_action": time_since_last_action,
            "recent_observations": self.memory[-5:] if self.memory else []
        }
    
    def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Use a specific tool"""
        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            tool.last_used = datetime.now()
            return tool.execute(params)
        return {"status": "error", "message": f"Tool {tool_name} not found"}
    
    def make_decision(self) -> Dict:
        """Updated to use LLM for decision making without async"""
        situation = self.analyze_situation()
        
        # Add available tools to the prompt
        available_tools = "\n".join([
            f"- {tool}: {self.tool_registry.get_tool(tool).get_description()}"
            for tool in self.tool_registry.list_tools()
        ])
        
        # In src/agent.py, update the prompt in make_decision()
        prompt = f"""
        You are an AI agent responsible for helping achieve the goal: {self.goal.description}
        Success Criteria: {self.goal.success_criteria}

        Current Situation:
        - Time: {situation['timestamp']}
        - Time Since Last Action: {situation['time_since_last_action']} hours
        - Recent History: {situation['recent_observations']}

        Available Tools:
        {available_tools}

        Your task is to make a decision about whether any action is needed right now.

        IMPORTANT: Respond with a pure XML document. Do NOT use markdown formatting or code blocks.
        Start your response directly with the <decision> tag.

        Example format:
        <decision>
            <analysis>Detailed analysis of the situation</analysis>
            <action_type>Action or No Action</action_type>
            <reasoning>Clear explanation of your decision</reasoning>
            <action_details>
                <tool>tool_name</tool>
                <parameters>
                    <action>action_name</action>
                    <content>content_here</content>
                </parameters>
            </action_details>
            <next_check>time period</next_check>
        </decision>
        """
        
        decision = self.llm.process_decision(prompt)
        return decision
    
    def run_cycle(self):
        """Run one decision cycle"""
        decision = self.make_decision()
        self.memory.append(decision)
        
        if decision["decision"] == "Action" and decision["action_details"]:
            self.last_action_time = datetime.now()
            # Execute action if specified
            try:
                # action_details is already a dict, no need to parse JSON
                tool_name = decision["action_details"].get("tool")
                params = decision["action_details"].get("parameters", {})
                if tool_name:
                    action_result = self.use_tool(tool_name, params)
                    decision["action_result"] = action_result
            except Exception as e:
                print(f"Error executing action: {e}")
                decision["action_result"] = {
                    "status": "error",
                    "message": f"Error executing action: {str(e)}"
                }
        
        return decision