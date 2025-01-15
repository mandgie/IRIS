# goal_agent/src/llm.py
import google.generativeai as genai
from typing import Dict, Any
import xml.etree.ElementTree as ET

class LLMInterface:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        self.chat = self.model.start_chat(history=[])
    
    def _clean_xml(self, text: str) -> str:
        """Clean XML text by removing markdown code blocks and extra whitespace"""
        # Remove markdown code blocks if present
        if "```xml" in text:
            text = text.split("```xml")[1]
        if "```" in text:
            text = text.split("```")[0]
        return text.strip()
    
    def process_decision(self, prompt: str) -> Dict[str, Any]:
        """Process a decision using the LLM"""
        try:
            formatted_prompt = f"""{prompt}

Important: Provide your response as XML without any markdown formatting or code blocks. Start directly with <decision>."""
            
            response = self.chat.send_message(formatted_prompt)
            print("Raw LLM Response:", response.text)  # Debug print
            
            # Clean and parse XML
            xml_text = self._clean_xml(response.text)
            
            root = ET.fromstring(xml_text)
            
            decision = {
                "analysis": root.find('analysis').text.strip() if root.find('analysis') is not None else "",
                "decision": root.find('action_type').text.strip() if root.find('action_type') is not None else "",
                "reasoning": root.find('reasoning').text.strip() if root.find('reasoning') is not None else "",
                "action_details": None,
                "next_check": root.find('next_check').text.strip() if root.find('next_check') is not None else ""
            }
            
            # Process action details if present
            action_details = root.find('action_details')
            if action_details is not None and decision["decision"] == "Action":
                tool = action_details.find('tool')
                parameters = action_details.find('parameters')
                if tool is not None and parameters is not None:
                    decision["action_details"] = {
                        "tool": tool.text.strip(),
                        "parameters": {
                            child.tag: child.text.strip()
                            for child in parameters
                        }
                    }
            
            print("Parsed Decision:", decision)  # Debug print
            return decision
            
        except Exception as e:
            print(f"Error processing LLM decision: {e}")
            print(f"Failed XML content:", response.text)  # Additional debug info
            return {
                "analysis": "Error in LLM processing",
                "decision": "No Action",
                "reasoning": f"Error occurred: {str(e)}",
                "action_details": None,
                "next_check": "1 hour"
            }