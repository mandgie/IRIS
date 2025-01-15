from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from .memory import MemorySystem
from .tools import ToolRegistry, NoteTool, CalculatorTool
from .llm import LLMInterface

@dataclass
class Goal:
    description: str
    success_criteria: Dict[str, any]
    target_date: datetime

class Agent:
    def __init__(self, goal: Goal, api_key: str):
        self.goal = goal
        self.last_action_time = None
        self.tool_registry = ToolRegistry()
        self.llm = LLMInterface(api_key)
        self.memory = MemorySystem()
        
        # Register default tools
        self.tool_registry.register_tool(NoteTool())
        self.tool_registry.register_tool(CalculatorTool())
    
    def analyze_situation(self) -> Dict:
        """Analyze current situation and return structured analysis"""
        current_time = datetime.now()
        time_since_last_action = None if not self.last_action_time else \
            (current_time - self.last_action_time).total_seconds() / 3600
        
        # Get context from memory system
        context = self.memory.get_relevant_context({
            'current_time': current_time,
            'time_since_last_action': time_since_last_action,
            'goal': self.goal.__dict__
        })
        
        # Format memory components for prompt
        recent_decisions_summary = self._format_recent_decisions(context['recent'])
        patterns_summary = self._format_patterns(context['patterns'])
        summaries_text = self._format_summaries(context['summaries'])
        
        return {
            "timestamp": current_time.isoformat(),
            "time_since_last_action": time_since_last_action,
            "recent_history": recent_decisions_summary,
            "patterns": patterns_summary,
            "summaries": summaries_text
        }
    
    def _format_recent_decisions(self, decisions: List[Dict]) -> str:
        """Format recent decisions for the prompt"""
        if not decisions:
            return "No recent decisions"
        
        formatted = []
        for decision in decisions[:5]:  # Show last 5 decisions
            action_str = "No action taken"
            if decision['decision'] == 'Action' and decision['action_details']:
                tool = decision['action_details'].get('tool', 'unknown')
                result = decision.get('action_result', {})
                status = result.get('status', 'unknown')
                action_str = f"Used {tool} tool - Status: {status}"
            
            formatted.append(f"- {decision['timestamp']}: {action_str}")
        
        return "\n".join(formatted)
    
    def _format_patterns(self, patterns: List[Dict]) -> str:
        """Format patterns for the prompt"""
        if not patterns:
            return "No significant patterns detected"
        
        formatted = []
        for pattern in patterns:
            formatted.append(f"- {pattern['description']}")
            if pattern.get('details'):
                details = pattern['details']
                if isinstance(details, dict):
                    for key, value in details.items():
                        formatted.append(f"  * {key}: {value}")
                elif isinstance(details, list):
                    for item in details:
                        if isinstance(item, dict):
                            for key, value in item.items():
                                formatted.append(f"  * {key}: {value}")
                        else:
                            formatted.append(f"  * {item}")
        
        return "\n".join(formatted)
    
    def _format_summaries(self, summaries: List[Dict]) -> str:
        """Format summaries for the prompt"""
        if not summaries:
            return "No historical summaries available"
        
        formatted = []
        for summary in summaries[:3]:  # Show last 3 summaries
            summary_data = summary['summary']
            formatted.append(f"Summary ({summary['summary_type']}) for {summary['start_date']} to {summary['end_date']}:")
            formatted.append(f"- Total decisions: {summary_data['total_decisions']}")
            formatted.append(f"- Actions taken: {summary_data['actions_taken']}")
            formatted.append(f"- Success rate: {summary_data['successful_actions']}/{summary_data['actions_taken']}")
        
        return "\n".join(formatted)
    
    def make_decision(self) -> Dict:
        """Make a decision based on current situation"""
        situation = self.analyze_situation()
        
        # Add available tools to the prompt
        available_tools = "\n".join([
            f"- {tool}: {self.tool_registry.get_tool(tool).get_description()}"
            for tool in self.tool_registry.list_tools()
        ])
        
        prompt = f"""
        You are an AI agent responsible for helping achieve the goal: {self.goal.description}
        Success Criteria: {self.goal.success_criteria}
        Target Date: {self.goal.target_date}
        
        Current Situation:
        - Time: {situation['timestamp']}
        - Time Since Last Action: {situation['time_since_last_action']} hours
        
        Recent History:
        {situation['recent_history']}
        
        Observed Patterns:
        {situation['patterns']}
        
        Historical Summaries:
        {situation['summaries']}
        
        Available Tools:
        {available_tools}
        
        Based on this context, determine if any action is needed right now.
        
        Respond with an XML document in this exact format:
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
    
    def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Use a specific tool"""
        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            tool.last_used = datetime.now()
            return tool.execute(params)
        return {"status": "error", "message": f"Tool {tool_name} not found"}

    def run_cycle(self):
        """Run one decision cycle"""
        decision = self.make_decision()
        
        if decision["decision"] == "Action" and decision["action_details"]:
            self.last_action_time = datetime.now()
            try:
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
        
        # Store decision in memory system
        self.memory.store_decision(decision)
        
        # Create summaries if needed
        current_time = datetime.now()
        if current_time.hour == 0 and current_time.minute < 15:  # Around midnight
            yesterday = current_time - timedelta(days=1)
            self.memory.create_summary('daily', 
                                     start_date=yesterday.replace(hour=0, minute=0),
                                     end_date=yesterday.replace(hour=23, minute=59))
            
            # Weekly summary on Sunday
            if current_time.weekday() == 6:  # Sunday
                week_start = current_time - timedelta(days=7)
                self.memory.create_summary('weekly',
                                         start_date=week_start.replace(hour=0, minute=0),
                                         end_date=current_time.replace(hour=23, minute=59))
            
            # Monthly summary on the last day of the month
            if (current_time + timedelta(days=1)).day == 1:
                month_start = current_time.replace(day=1, hour=0, minute=0)
                self.memory.create_summary('monthly',
                                         start_date=month_start,
                                         end_date=current_time.replace(hour=23, minute=59))
        
        return decision