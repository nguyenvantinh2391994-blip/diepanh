"""
Mimi Robot - Backend Server (Phiên bản đơn giản)
Chạy: python main_simple.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Thêm thư mục cha vào path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
import aiosqlite
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================================================
# CONFIGURATION
# ============================================================

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {
        "server": {"host": "0.0.0.0", "port": 8080},
        "ai": {
            "provider": "ollama",
            "ollama": {"host": "http://localhost:11434", "model": "qwen2.5:7b", "temperature": 0.7}
        },
        "personality": {
            "system_prompt": "Bạn là Mimi, robot dễ thương, nói chuyện với trẻ em."
        },
        "memory": {"database_path": "./data/mimi_memory.db"}
    }

CONFIG = load_config()

# ============================================================
# DATABASE (Memory)
# ============================================================

class MemoryManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    async def init(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                device_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                device_id TEXT PRIMARY KEY,
                child_name TEXT,
                preferences TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.commit()
        print(f"✅ Database initialized: {self.db_path}")

    async def save_message(self, device_id: str, role: str, content: str):
        await self.conn.execute(
            "INSERT INTO conversations (device_id, role, content) VALUES (?, ?, ?)",
            (device_id, role, content)
        )
        await self.conn.commit()

    async def get_history(self, device_id: str, limit: int = 10):
        cursor = await self.conn.execute(
            "SELECT role, content FROM conversations WHERE device_id = ? ORDER BY id DESC LIMIT ?",
            (device_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    async def save_child_name(self, device_id: str, name: str):
        await self.conn.execute(
            "INSERT OR REPLACE INTO user_profile (device_id, child_name) VALUES (?, ?)",
            (device_id, name)
        )
        await self.conn.commit()
        print(f"💾 Saved child name: {name}")

    async def get_child_name(self, device_id: str):
        cursor = await self.conn.execute(
            "SELECT child_name FROM user_profile WHERE device_id = ?", (device_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

# ============================================================
# AI ENGINE (DeepSeek / Ollama)
# ============================================================

class AIEngine:
    def __init__(self, config: dict):
        ai_config = config.get("ai", {})
        self.provider = ai_config.get("provider", "ollama")
        self.system_prompt = config.get("personality", {}).get("system_prompt", "Bạn là Mimi.")
        self.session = None
        self.client = None

        if self.provider == "deepseek":
            deepseek_config = ai_config.get("deepseek", {})
            self.api_key = deepseek_config.get("api_key", "")
            self.model = deepseek_config.get("model", "deepseek-chat")
            self.temperature = deepseek_config.get("temperature", 0.8)
            self.max_tokens = deepseek_config.get("max_tokens", 1000)
        else:
            ollama_config = ai_config.get("ollama", {})
            self.host = ollama_config.get("host", "http://localhost:11434")
            self.model = ollama_config.get("model", "qwen2.5:7b")
            self.temperature = ollama_config.get("temperature", 0.7)

    async def init(self):
        if self.provider == "deepseek":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                print(f"✅ DeepSeek connected! Model: {self.model}")
                print("   🚀 Nhanh như CLG AI!")
            except Exception as e:
                print(f"❌ DeepSeek error: {e}")
        else:
            self.session = aiohttp.ClientSession()
            try:
                async with self.session.get(f"{self.host}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["name"] for m in data.get("models", [])]
                        print(f"✅ Ollama connected! Models: {models}")
                    else:
                        print("❌ Ollama not responding")
            except Exception as e:
                print(f"❌ Cannot connect to Ollama: {e}")

    async def chat(self, message: str, history: list = None, child_name: str = None):
        # Build system prompt with child name
        system = self.system_prompt
        if child_name:
            system += f"\n\nBạn đang nói chuyện với bé {child_name}."

        messages = []
        if history:
            messages.extend(history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": message})

        if self.provider == "deepseek":
            return await self._chat_deepseek(messages, system)
        else:
            return await self._chat_ollama(messages, system)

    async def _chat_deepseek(self, messages: list, system: str):
        try:
            full_messages = [{"role": "system", "content": system}] + messages
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ DeepSeek Error: {e}")
            return "Mimi đang gặp trục trặc, thử lại nhé!"

    async def _chat_ollama(self, messages: list, system: str):
        full_messages = [{"role": "system", "content": system}] + messages
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        try:
            async with self.session.post(f"{self.host}/api/chat", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["message"]["content"]
                else:
                    return "Mimi đang gặp trục trặc, thử lại nhé!"
        except Exception as e:
            print(f"❌ Ollama Error: {e}")
            return "Mimi không thể suy nghĩ được!"

    async def close(self):
        if self.session:
            await self.session.close()

# ============================================================
# TEXT TO SPEECH (Edge TTS)
# ============================================================

async def text_to_speech(text: str, voice: str = "vi-VN-HoaiMyNeural"):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return None

# ============================================================
# FASTAPI SERVER
# ============================================================

app = FastAPI(title="Mimi Robot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
memory = MemoryManager(CONFIG.get("memory", {}).get("database_path", "./data/mimi_memory.db"))
ai = AIEngine(CONFIG)

@app.on_event("startup")
async def startup():
    print("\n" + "="*50)
    print("🧸 MIMI ROBOT - BACKEND SERVER")
    print("="*50 + "\n")
    await memory.init()
    await ai.init()
    print("\n✅ Server ready!")
    print(f"   URL: http://localhost:{CONFIG['server']['port']}")
    print(f"   WebSocket: ws://localhost:{CONFIG['server']['port']}/ws")
    print("\n" + "="*50 + "\n")

@app.on_event("shutdown")
async def shutdown():
    await ai.close()

@app.get("/")
async def root():
    return {"status": "ok", "service": "Mimi Robot", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "ai": "ollama", "model": ai.model}

# WebSocket for robot communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    device_id = "default"
    print(f"🔌 New connection: {device_id}")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "device_info":
                device_id = data.get("device_id", "default")
                child_name = await memory.get_child_name(device_id)
                await websocket.send_json({
                    "type": "welcome",
                    "message": f"Xin chào{' ' + child_name if child_name else ''}! Mimi sẵn sàng rồi!"
                })

            elif msg_type == "text":
                text = data.get("text", "")
                print(f"👧 User: {text}")

                # Check if user is telling their name
                if "tên" in text.lower() and ("là" in text.lower() or "con là" in text.lower()):
                    import re
                    match = re.search(r"(?:tên (?:con|em|mình) là|con là|em là)\s+(\w+)", text.lower())
                    if match:
                        name = match.group(1).capitalize()
                        await memory.save_child_name(device_id, name)

                # Get history and child name
                history = await memory.get_history(device_id)
                child_name = await memory.get_child_name(device_id)

                # Send thinking status
                await websocket.send_json({"type": "thinking"})

                # Get AI response
                response = await ai.chat(text, history, child_name)
                print(f"🧸 Mimi: {response}")

                # Save to memory
                await memory.save_message(device_id, "user", text)
                await memory.save_message(device_id, "assistant", response)

                # Send text response
                await websocket.send_json({"type": "text", "text": response})

                # Generate and send audio
                audio = await text_to_speech(response)
                if audio:
                    import base64
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64.b64encode(audio).decode()
                    })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print(f"🔌 Disconnected: {device_id}")

# Simple chat endpoint for testing
@app.post("/chat")
async def chat_endpoint(data: dict):
    text = data.get("text", "")
    device_id = data.get("device_id", "default")

    history = await memory.get_history(device_id)
    child_name = await memory.get_child_name(device_id)

    response = await ai.chat(text, history, child_name)

    await memory.save_message(device_id, "user", text)
    await memory.save_message(device_id, "assistant", response)

    return {"response": response}


# Voice endpoint for ESP32 (HTTP fallback)
@app.post("/api/voice")
async def voice_endpoint(request: Request):
    """Handle voice input from ESP32 via HTTP POST"""
    import base64

    try:
        body = await request.body()
        device_id = request.headers.get("X-Device-ID", "default")

        # If body is JSON
        try:
            data = json.loads(body)
            audio_b64 = data.get("audio", "")
            audio_data = base64.b64decode(audio_b64) if audio_b64 else body
        except:
            audio_data = body

        # TODO: Implement Speech-to-Text here
        # For now, return a test response
        text = "Xin chào!"  # Placeholder

        # Get AI response
        history = await memory.get_history(device_id)
        child_name = await memory.get_child_name(device_id)
        response = await ai.chat(text, history, child_name)

        # Save to memory
        await memory.save_message(device_id, "user", text)
        await memory.save_message(device_id, "assistant", response)

        # Generate TTS
        audio = await text_to_speech(response)

        return {
            "text": response,
            "audio": base64.b64encode(audio).decode() if audio else None
        }
    except Exception as e:
        print(f"❌ Voice endpoint error: {e}")
        return {"error": str(e)}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host=CONFIG["server"]["host"],
        port=CONFIG["server"]["port"],
        reload=CONFIG["server"].get("debug", False)
    )
