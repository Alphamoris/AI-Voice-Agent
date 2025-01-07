from typing import Dict, Optional
import openai
from loguru import logger
import os
import json

class LanguageModel:
    def __init__(self, config: Dict):
        self.config = config
        self.provider = config["default_provider"]
        self.is_initialized = False
        self.conversation_history = {}
        
    async def initialize(self):
        """Initialize language model clients."""
        if self.provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        self.is_initialized = True
        
    async def generate_response(self, user_input: str, session_id: str) -> str:
        """Generate response using the configured language model."""
        if not self.is_initialized:
            raise RuntimeError("Language model not initialized")
            
        try:
            if self.provider == "openai":
                return await self._generate_openai_response(user_input, session_id)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Response generation error: {str(e)}")
            raise
            
    async def _generate_openai_response(self, user_input: str, session_id: str) -> str:
        """Generate response using OpenAI's API."""
        try:
            # Get conversation history for this session
            history = self.conversation_history.get(session_id, [])
            
            # Prepare messages
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant engaged in a voice conversation. Keep your responses concise and natural."}
            ]
            
            # Add conversation history
            messages.extend(history)
            
            # Add user's input
            messages.append({"role": "user", "content": user_input})
            
            # Get model configuration
            model_config = self.config["providers"]["openai"]
            
            # Generate response
            response = await openai.ChatCompletion.acreate(
                model=model_config["model"],
                messages=messages,
                temperature=model_config["temperature"],
                max_tokens=model_config["max_tokens"]
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Update conversation history
            history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response_text}
            ])
            
            # Trim history if too long
            if len(history) > 10:  # Keep last 5 exchanges
                history = history[-10:]
            
            self.conversation_history[session_id] = history
            
            return response_text
            
        except Exception as e:
            logger.error(f"OpenAI response generation error: {str(e)}")
            raise
            
    def clear_history(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            
    def health_check(self) -> Dict:
        """Check the health of the language model service."""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "provider": self.provider
        }
