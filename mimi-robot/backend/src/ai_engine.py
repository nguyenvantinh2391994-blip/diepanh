"""
Mimi Robot - AI Engine
Handles AI conversation with different providers
"""

import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

from config_manager import ConfigManager

logger = logging.getLogger("mimi-ai")


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def generate(self, messages: List[Dict], system_prompt: str) -> str:
        pass


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider"""

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "claude-3-5-sonnet-20241022")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 500)
        self.client = None

    async def initialize(self):
        if self.api_key:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            logger.info("Anthropic client initialized")

    async def generate(self, messages: List[Dict], system_prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 500)
        self.client = None

    async def initialize(self):
        if self.api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized")

    async def generate(self, messages: List[Dict], system_prompt: str) -> str:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content


class AIEngine:
    """Main AI Engine that manages providers and conversation"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.provider: Optional[AIProvider] = None
        self._ready = False

        # Get personality
        personality = config.personality
        self.system_prompt = personality.get("system_prompt", "Bạn là Mimi, robot dễ thương.")
        self.name = personality.get("name", "Mimi")

    async def initialize(self):
        """Initialize the AI provider"""
        ai_config = self.config.ai_config
        provider_name = ai_config.get("provider", "anthropic")

        logger.info(f"Initializing AI provider: {provider_name}")

        if provider_name == "anthropic":
            self.provider = AnthropicProvider(ai_config)
        elif provider_name == "openai":
            self.provider = OpenAIProvider(ai_config)
        else:
            raise ValueError(f"Unknown AI provider: {provider_name}")

        await self.provider.initialize()
        self._ready = True
        logger.info("AI Engine initialized successfully")

    def is_ready(self) -> bool:
        return self._ready

    async def generate_response(
        self,
        user_input: str,
        context: Optional[Dict] = None,
        history: Optional[List[Dict]] = None
    ) -> str:
        """Generate a response to user input"""
        if not self._ready:
            raise RuntimeError("AI Engine not initialized")

        # Build system prompt with context
        system_prompt = self._build_system_prompt(context)

        # Build messages from history
        messages = self._build_messages(user_input, history)

        # Generate response
        try:
            response = await self.provider.generate(messages, system_prompt)

            # Apply safety filter
            response = self._apply_safety_filter(response)

            return response

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "Mimi đang nghĩ không ra, bạn hỏi lại được không?"

    def _build_system_prompt(self, context: Optional[Dict]) -> str:
        """Build system prompt with user context"""
        prompt = self.system_prompt

        if context:
            # Add personalized context
            if context.get("child_name"):
                prompt += f"\n\nBạn đang nói chuyện với {context['child_name']}."

            if context.get("preferences"):
                prefs = ", ".join(context["preferences"])
                prompt += f"\n{context.get('child_name', 'Bạn nhỏ')} thích: {prefs}."

            if context.get("facts"):
                facts = "\n".join(f"- {fact}" for fact in context["facts"])
                prompt += f"\n\nNhững điều bạn nhớ về bạn nhỏ:\n{facts}"

        return prompt

    def _build_messages(
        self,
        user_input: str,
        history: Optional[List[Dict]]
    ) -> List[Dict]:
        """Build message list for AI"""
        messages = []

        # Add conversation history (last N messages)
        if history:
            for msg in history[-10:]:  # Keep last 10 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })

        return messages

    def _apply_safety_filter(self, response: str) -> str:
        """Apply child-safe content filtering"""
        safety_config = self.config.get_section("safety")

        if not safety_config.get("enabled", True):
            return response

        # Check max length
        max_length = safety_config.get("max_response_length", 150)
        words = response.split()
        if len(words) > max_length:
            response = " ".join(words[:max_length]) + "..."

        return response

    async def detect_emotion(self, text: str) -> str:
        """Detect emotion from text for display"""
        text_lower = text.lower()

        # Simple keyword-based emotion detection
        if any(word in text_lower for word in ["vui", "haha", "hehe", "tuyệt", "hay"]):
            return "happy"
        elif any(word in text_lower for word in ["buồn", "tiếc", "xin lỗi"]):
            return "sad"
        elif any(word in text_lower for word in ["ồ", "wow", "thật sao", "không thể"]):
            return "surprised"
        elif any(word in text_lower for word in ["yêu", "thương", "nhớ"]):
            return "love"
        elif any(word in text_lower for word in ["nghĩ", "hmm", "để xem"]):
            return "thinking"
        else:
            return "happy"  # Default happy face
