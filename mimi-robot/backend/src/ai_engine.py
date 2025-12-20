"""
Mimi Robot - AI Engine
Handles AI conversation with different providers
"""

import logging
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod

from config_manager import ConfigManager
from mimi_personality import mimi_personality, conversation_memory

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


class OllamaProvider(AIProvider):
    """
    Ollama - Chạy AI hoàn toàn LOCAL, MIỄN PHÍ
    Không cần internet, không gửi dữ liệu đi đâu
    """

    def __init__(self, config: dict):
        self.host = config.get("host", "http://localhost:11434")
        self.model = config.get("model", "llama3.2")  # hoặc qwen2.5, gemma2
        self.temperature = config.get("temperature", 0.7)
        self.session = None

    async def initialize(self):
        import aiohttp
        self.session = aiohttp.ClientSession()

        # Kiểm tra Ollama đang chạy
        try:
            async with self.session.get(f"{self.host}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    logger.info(f"Ollama connected. Available models: {models}")

                    # Kiểm tra model có sẵn (so khớp đầy đủ hoặc phần tên)
                    model_names = [m.split(":")[0] for m in models]
                    if self.model not in models and self.model.split(":")[0] not in model_names:
                        logger.warning(f"Model {self.model} not found. Run: ollama pull {self.model}")
                    else:
                        logger.info(f"Model {self.model} is available!")
                else:
                    logger.error("Ollama not responding")
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            logger.info("Hướng dẫn cài Ollama:")
            logger.info("1. Tải từ: https://ollama.ai/download")
            logger.info("2. Cài đặt và chạy Ollama")
            logger.info(f"3. Chạy: ollama pull {self.model}")

    async def generate(self, messages: List[Dict], system_prompt: str) -> str:
        if not self.session:
            raise RuntimeError("Ollama session not initialized")

        # Ollama API format
        full_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            full_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 50  # Giới hạn ~50 tokens = 2-3 câu ngắn
            }
        }

        try:
            async with self.session.post(
                f"{self.host}/api/chat",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["message"]["content"]
                else:
                    error = await resp.text()
                    logger.error(f"Ollama error: {error}")
                    return "Mimi đang gặp trục trặc, thử lại nhé!"

        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return "Mimi không thể suy nghĩ được, kiểm tra Ollama nhé!"

    async def close(self):
        if self.session:
            await self.session.close()


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

        if provider_name == "ollama":
            self.provider = OllamaProvider(ai_config)
            logger.info("Using Ollama (LOCAL, FREE, PRIVATE)")
        elif provider_name == "anthropic":
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

        # Check for special intents first (stories, riddles, songs)
        intent = mimi_personality.detect_intent(user_input)
        special_response = mimi_personality.get_response_for_intent(intent, context)

        if special_response and intent in ["tell_story", "riddle", "sing"]:
            # For these intents, use pre-built responses for consistency
            logger.info(f"Using special response for intent: {intent}")
            return special_response

        # Build system prompt with context
        system_prompt = self._build_system_prompt(context)

        # Add intent hint to help AI respond appropriately
        if intent == "comfort":
            system_prompt += "\n\n⚠️ Diệp Anh đang buồn/sợ - hãy an ủi và động viên!"
        elif intent == "family":
            system_prompt += "\n\n💕 Diệp Anh đang nói về gia đình - hãy hỏi thăm!"
        elif intent == "school":
            system_prompt += "\n\n🏫 Diệp Anh đang nói về trường - hãy quan tâm!"

        # Build messages from history
        messages = self._build_messages(user_input, history)

        # Generate response
        try:
            response = await self.provider.generate(messages, system_prompt)

            # Apply safety filter
            response = self._apply_safety_filter(response)

            # Save important memories
            conversation_memory.extract_important_memory(user_input, response)

            return response

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "Mimi đang nghĩ không ra, cậu hỏi lại được không?"

    def _build_system_prompt(self, context: Optional[Dict]) -> str:
        """Build system prompt with user context - Mimi's living memory"""
        prompt = self.system_prompt

        if context:
            child_name = context.get("child_name", "Diệp Anh")

            # Add personalized context
            prompt += f"\n\n=== TRÍ NHỚ CỦA MIMI VỀ {child_name.upper()} ==="

            # Group facts by category for better understanding
            facts = context.get("facts", [])
            if facts:
                # Parse facts into categories
                recent_activities = []
                likes = []
                friends = []
                feelings = []
                toys = []
                school_info = []
                other_facts = []

                for fact in facts:
                    fact_lower = fact.lower()
                    if "hoạt động hôm nay" in fact_lower or "hôm nay" in fact_lower:
                        recent_activities.append(fact)
                    elif "thích" in fact_lower or "yêu" in fact_lower or "mê" in fact_lower:
                        likes.append(fact)
                    elif "bạn bè" in fact_lower or "bạn" in fact_lower:
                        friends.append(fact)
                    elif "cảm xúc" in fact_lower or "vui" in fact_lower or "buồn" in fact_lower:
                        feelings.append(fact)
                    elif "đồ chơi" in fact_lower:
                        toys.append(fact)
                    elif "trường" in fact_lower or "lớp" in fact_lower or "cô giáo" in fact_lower:
                        school_info.append(fact)
                    else:
                        other_facts.append(fact)

                # Build memory section with context
                if recent_activities:
                    prompt += f"\n\n📅 GẦN ĐÂY {child_name} đã:"
                    for act in recent_activities[-3:]:  # Last 3 activities
                        prompt += f"\n  - {act}"
                    prompt += f"\n  → Mimi nên hỏi thăm về những hoạt động này!"

                if feelings:
                    prompt += f"\n\n💭 TÂM TRẠNG gần đây:"
                    for feel in feelings[-2:]:
                        prompt += f"\n  - {feel}"
                    prompt += f"\n  → Mimi nên quan tâm đến cảm xúc của {child_name}!"

                if likes:
                    prompt += f"\n\n❤️ NHỮNG ĐIỀU {child_name} THÍCH:"
                    for like in likes[-5:]:
                        prompt += f"\n  - {like}"
                    prompt += f"\n  → Mimi có thể gợi ý chơi/nói về những thứ này!"

                if friends:
                    prompt += f"\n\n👫 BẠN BÈ:"
                    for friend in friends[-3:]:
                        prompt += f"\n  - {friend}"

                if toys:
                    prompt += f"\n\n🧸 ĐỒ CHƠI:"
                    for toy in toys[-3:]:
                        prompt += f"\n  - {toy}"

                if school_info:
                    prompt += f"\n\n🏫 TRƯỜNG HỌC:"
                    for info in school_info:
                        prompt += f"\n  - {info}"

                if other_facts:
                    prompt += f"\n\n📝 GHI NHỚ KHÁC:"
                    for fact in other_facts[-3:]:
                        prompt += f"\n  - {fact}"

            # Add proactive behavior instructions
            prompt += f"""

=== CÁCH MIMI SỬ DỤNG TRÍ NHỚ ===
- NẾU {child_name} vừa kể gì đó thú vị → Mimi hỏi thêm chi tiết
- NẾU biết {child_name} thích gì → Mimi có thể gợi ý chơi/nói về nó
- NẾU biết {child_name} có bạn → Hỏi thăm về bạn đó
- NẾU biết cảm xúc gần đây → Quan tâm và động viên phù hợp
- Thỉnh thoảng Mimi chủ động nhắc lại những kỷ niệm: "Này, hôm trước {child_name} có kể..."
- QUAN TRỌNG: Không lặp lại y chang, mà dùng thông tin một cách tự nhiên"""

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

        import re

        # Remove Chinese/Japanese/Korean characters
        original_len = len(response)
        response = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', '', response)

        # Remove English words (keep Vietnamese)
        response = re.sub(r'\b[a-zA-Z]{3,}\b', '', response)

        # Clean up extra whitespace/newlines
        response = re.sub(r'\n\s*\n', '\n', response)
        response = re.sub(r'  +', ' ', response)
        response = response.strip()

        if len(response) < original_len:
            logger.warning(f"Removed non-Vietnamese: {original_len} -> {len(response)} chars")

        # === GIỚI HẠN TỐI ĐA 3 CÂU ===
        # Tách câu bằng dấu . ! ? và giới hạn
        sentences = re.split(r'(?<=[.!?])\s+', response)
        if len(sentences) > 3:
            response = ' '.join(sentences[:3])
            if not response.endswith(('.', '!', '?')):
                response += '!'
            logger.info(f"Truncated to 3 sentences: {len(sentences)} -> 3")

        # Fallback: giới hạn theo từ nếu vẫn còn dài
        max_words = safety_config.get("max_response_length", 40)
        words = response.split()
        if len(words) > max_words:
            response = " ".join(words[:max_words]) + "..."

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
