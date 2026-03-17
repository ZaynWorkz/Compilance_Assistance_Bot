# app/conversation/llm_manager.py

from typing import Dict, Any, List
import openai  # or any LLM library
from .prompts import PromptManager

class LLMManager:
    """Manages LLM interactions for conversational flow"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.prompt_manager = PromptManager()
        self.max_tokens = 150
        self.temperature = 0.3  # Low temperature for consistent responses
        
    def generate_response(self, 
                         message: str, 
                         current_state: str, 
                         context: Dict[str, Any],
                         conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate LLM response based on current context
        """
        # Build prompt with context
        system_prompt = self.prompt_manager.get_system_prompt(current_state, context)
        
        # Format conversation history
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add last 5 messages for context
        for msg in conversation_history[-5:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            # Call LLM (simplified - use actual LLM client)
            response = self._call_llm(messages)
            return self._post_process_response(response, context)
        except Exception as e:
            return f"I'm having trouble processing your request. Please continue with the document upload process. Error: {str(e)}"
    
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Mock LLM call - replace with actual LLM integration
        """
        # This is a mock - in production, use actual LLM API
        # For example with OpenAI:
        # response = openai.ChatCompletion.create(
        #     model=self.model,
        #     messages=messages,
        #     max_tokens=self.max_tokens,
        #     temperature=self.temperature
        # )
        # return response.choices[0].message.content
        
        # Mock response for development
        return "I'll help you with the document upload process. Please follow the instructions to upload your documents."
    
    def _post_process_response(self, response: str, context: Dict[str, Any]) -> str:
        """
        Post-process LLM response to ensure it follows workflow constraints
        """
        # Ensure response doesn't contain prohibited content
        prohibited_phrases = [
            "legal advice",
            "I am a lawyer",
            "this is legally binding",
            "you should sue"
        ]
        
        for phrase in prohibited_phrases:
            if phrase in response.lower():
                response = response.replace(phrase, "")
        
        return response.strip()