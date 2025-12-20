"""
Mimi Robot - Backend Server
Main entry point for the AI dialogue server

Cách chạy:
    python main.py              # Chạy bình thường, hiển thị log
    python main.py --stop       # Dừng server đang chạy
    python main.py --status     # Kiểm tra trạng thái

Chạy ẩn trên Windows:
    Double-click file start_mimi.vbs
"""

import asyncio
import json
import logging
import base64
import os
import sys
import signal
import atexit
import time
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from config_manager import ConfigManager
from ai_engine import AIEngine
from speech_processor import SpeechProcessor
from memory_manager import MemoryManager
from connection_manager import ConnectionManager
from sheets_manager import SheetsManager

# PID file để quản lý process
PID_FILE = Path(__file__).parent.parent / "data" / "mimi.pid"
LOG_FILE = Path(__file__).parent.parent / "data" / "mimi.log"


def setup_logging():
    """Setup logging ra console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def is_process_running(pid: int) -> bool:
    """Kiểm tra process có đang chạy không"""
    if sys.platform == "win32":
        # Windows: dùng tasklist
        import subprocess
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        # Linux/Mac: dùng signal 0
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def get_running_pid() -> int | None:
    """Lấy PID của process đang chạy"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_process_running(pid):
                return pid
            else:
                PID_FILE.unlink(missing_ok=True)
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)
    return None


def write_pid():
    """Ghi PID hiện tại vào file"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def remove_pid():
    """Xóa PID file khi thoát"""
    PID_FILE.unlink(missing_ok=True)


def stop_existing_instance() -> bool:
    """Dừng instance đang chạy (nếu có)"""
    pid = get_running_pid()
    if pid:
        print(f"Dang dung Mimi server cu (PID: {pid})...")
        try:
            import time
            if sys.platform == "win32":
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                time.sleep(1)
            else:
                os.kill(pid, signal.SIGTERM)
                for _ in range(10):
                    time.sleep(0.5)
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                else:
                    os.kill(pid, signal.SIGKILL)

            print("Da dung server cu")
            PID_FILE.unlink(missing_ok=True)
            return True
        except Exception as e:
            print(f"Loi khi dung: {e}")
            PID_FILE.unlink(missing_ok=True)
            return True
    return True


def show_status():
    """Hiển thị trạng thái server"""
    pid = get_running_pid()
    if pid:
        print(f"Mimi server dang chay (PID: {pid})")
        print(f"Log file: {LOG_FILE}")
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text(encoding='utf-8', errors='ignore').splitlines()[-10:]
            if lines:
                print("\n--- Log gan day ---")
                for line in lines:
                    print(line)
    else:
        print("Mimi server khong chay")


# Setup logging
setup_logging()
logger = logging.getLogger("mimi-server")

# Global managers (will be initialized in lifespan)
config = ConfigManager()
ai_engine = AIEngine(config)
speech_processor = SpeechProcessor(config)
memory_manager = MemoryManager(config)
connection_manager = ConnectionManager()

# Google Sheets manager (optional)
sheets_config = config.get_section("google_sheets")
sheets_manager = None
if sheets_config.get("enabled", False):
    sheets_manager = SheetsManager(
        credentials_path=sheets_config.get("credentials_path", "./src/credentials.json"),
        spreadsheet_name=sheets_config.get("spreadsheet_name", "mimi"),
        sheet_name=sheets_config.get("sheet_name", "2025")
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Mimi Backend Server...")

    await ai_engine.initialize()
    await speech_processor.initialize()
    await memory_manager.initialize()

    if sheets_manager:
        success = await sheets_manager.initialize()
        if success:
            logger.info("Google Sheets logging enabled")
        else:
            logger.warning("Google Sheets not available - logging disabled")

    logger.info("All services initialized successfully!")

    yield  # Server runs here

    # Shutdown
    logger.info("Shutting down Mimi Backend Server...")
    await memory_manager.close()


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Mimi Robot API",
    description="Backend server for Mimi - AI Voice Robot",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Mimi Robot Backend",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "ai_engine": ai_engine.is_ready(),
            "speech_processor": speech_processor.is_ready(),
            "memory_manager": memory_manager.is_ready()
        }
    }


# Wake words to detect - nhiều variations vì Whisper không chính xác
WAKE_WORDS = [
    # Chuẩn
    "mimi", "mi mi", "mí mi", "mi-mi", "mimi ơi", "mimi oi",
    # Variations Whisper có thể nghe thành
    "mì mì", "mi mì", "mì mi", "mỳ mỳ", "mỉ mỉ",
    "mê mê", "me me", "mề mề",
    "hiểu", "hiu", "iu",
    "mimi oi", "mimi ơi", "mì mì ơi",
    "ê mimi", "hey mimi", "hê mimi",
    "alo", "a lô",
    # Từ log thực tế - Whisper nghe thành:
    "mì no", "mi no", "mino",
    "mình mi", "minh mi",
    "mình", "minh",
    # Whisper English mode nghe thành:
    "my", "me", "mia", "mimi", "meemee",
    "my tian", "tian", "mi tian",
    "jimmy", "timmy", "mini",
    "nini", "nina",
]


# Conversation Session Manager
# Quản lý phiên trò chuyện - sau khi gọi "Mimi", tiếp tục lắng nghe trong 60 giây
class ConversationSession:
    """Quản lý phiên trò chuyện với timeout"""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout = timeout_seconds
        self.sessions = {}  # device_id -> last_activity_time

    def start_session(self, device_id: str):
        """Bắt đầu hoặc gia hạn phiên trò chuyện"""
        self.sessions[device_id] = time.time()
        logger.info(f"[Session] Started/renewed for {device_id}, timeout in {self.timeout}s")

    def is_active(self, device_id: str) -> bool:
        """Kiểm tra phiên còn hoạt động không"""
        if device_id not in self.sessions:
            return False

        elapsed = time.time() - self.sessions[device_id]
        if elapsed < self.timeout:
            return True
        else:
            # Session expired
            del self.sessions[device_id]
            logger.info(f"[Session] Expired for {device_id}")
            return False

    def extend_session(self, device_id: str):
        """Gia hạn phiên khi có hoạt động"""
        if device_id in self.sessions:
            self.sessions[device_id] = time.time()

# Global session manager (60 giây timeout)
conversation_session = ConversationSession(timeout_seconds=60)


def contains_wake_word(text: str) -> bool:
    """Check if text contains a wake word"""
    text_lower = text.lower().strip()
    for wake_word in WAKE_WORDS:
        if wake_word in text_lower:
            return True
    return False


def remove_wake_word(text: str) -> str:
    """Remove wake word from text to get the actual command"""
    text_lower = text.lower().strip()
    for wake_word in WAKE_WORDS:
        if wake_word in text_lower:
            result = text_lower.replace(wake_word, "").strip()
            for filler in ["ơi", "oi", "à", "a", "này", "nay"]:
                if result.startswith(filler):
                    result = result[len(filler):].strip()
            return result if result else text
    return text


@app.post("/api/voice")
async def voice_endpoint(request: Request):
    """
    HTTP endpoint for voice processing.
    Receives raw PCM audio, returns PCM audio response.

    Logic:
    1. Nếu có wake word "Mimi" → bắt đầu session 60 giây, trả lời
    2. Nếu đang trong session (60 giây) → trả lời mà không cần wake word
    3. Nếu hết session và không có wake word → bỏ qua
    """
    device_id = "default_device"

    try:
        audio_data = await request.body()
        logger.info(f"[HTTP] Received {len(audio_data)} bytes of audio")

        if len(audio_data) < 1000:
            logger.warning("[HTTP] Audio too short, ignoring")
            return Response(content=b"", status_code=204)

        # Speech-to-Text
        logger.info("[HTTP] Converting speech to text...")
        recognized_text = await speech_processor.speech_to_text(audio_data)

        if not recognized_text or recognized_text.strip() == "":
            logger.info("[HTTP] No speech detected, ignoring")
            return Response(content=b"", status_code=204)

        logger.info(f"[HTTP] Recognized: {recognized_text}")

        # === WAKE WORD + SESSION LOGIC ===
        has_wake_word = contains_wake_word(recognized_text)
        session_active = conversation_session.is_active(device_id)

        if has_wake_word:
            # Wake word detected → start/renew session
            conversation_session.start_session(device_id)
            command_text = remove_wake_word(recognized_text)
            logger.info(f"[HTTP] Wake word detected! Session started. Command: {command_text}")

        elif session_active:
            # No wake word but session is active → process anyway
            command_text = recognized_text
            conversation_session.extend_session(device_id)
            logger.info(f"[HTTP] Session active, processing: {command_text}")

        else:
            # No wake word and no active session → ignore
            logger.info("[HTTP] No wake word and no active session, ignoring")
            return Response(content=b"", status_code=204)

        # === GENERATE RESPONSE ===
        context = await memory_manager.get_user_context(device_id)
        history = await memory_manager.get_conversation_history(device_id, limit=10)

        if not command_text or len(command_text) < 2:
            # Chỉ gọi tên, chưa nói gì
            if context.get("child_name"):
                response_text = f"Dạ, Mimi đây! Sao đó {context['child_name']}?"
            else:
                response_text = "Dạ, Mimi đây! Gì đó cậu?"
        else:
            logger.info("[HTTP] Generating AI response...")
            response_text = await ai_engine.generate_response(
                user_input=command_text,
                context=context,
                history=history
            )
            logger.info(f"[HTTP] AI Response: {response_text}")

            await memory_manager.save_conversation(device_id, command_text, response_text)
            await memory_manager.extract_and_save_facts(device_id, command_text, response_text)

            if sheets_manager and sheets_manager.is_ready():
                await sheets_manager.log_conversation(
                    user_message=command_text,
                    ai_response=response_text,
                    learned_facts=None,
                    emotion=None
                )

        # Extend session after successful response
        conversation_session.extend_session(device_id)

        # Generate TTS audio
        logger.info(f"[HTTP] Generating TTS for: {response_text}")
        tts_audio = await speech_processor.text_to_speech(response_text)

        if tts_audio:
            logger.info(f"[HTTP] Generated {len(tts_audio)} bytes of PCM audio")
            return Response(
                content=tts_audio,
                media_type="audio/pcm",
                headers={
                    "X-Response-Text": base64.b64encode(response_text.encode()).decode(),
                    "X-Sample-Rate": "16000",
                    "X-Bits": "16",
                    "X-Channels": "1"
                }
            )
        else:
            logger.error("[HTTP] TTS failed")
            return Response(content=b"", status_code=500)

    except Exception as e:
        logger.error(f"[HTTP] Error: {e}", exc_info=True)
        return Response(content=str(e).encode(), status_code=500)


@app.get("/api/test-speak")
async def test_speak():
    """Test TTS endpoint"""
    try:
        test_text = "Xin chào! Mimi hoạt động bình thường!"
        logger.info(f"[TEST] Generating TTS for: {test_text}")

        tts_audio = await speech_processor.text_to_speech(test_text)

        if tts_audio:
            logger.info(f"[TEST] Generated {len(tts_audio)} bytes of PCM audio")
            return Response(content=tts_audio, media_type="audio/pcm")
        else:
            return Response(content=b"TTS failed", status_code=500)

    except Exception as e:
        logger.error(f"[TEST] Error: {e}")
        return Response(content=str(e).encode(), status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for robot communication"""
    device_id = None

    try:
        await connection_manager.connect(websocket)
        logger.info("New WebSocket connection established")

        audio_buffer = bytearray()
        is_receiving_audio = False

        while True:
            try:
                message = await websocket.receive()

                if "text" in message:
                    data = json.loads(message["text"])
                    msg_type = data.get("type", "")

                    if msg_type == "device_info":
                        device_id = data.get("device_id")
                        await connection_manager.register_device(websocket, device_id)
                        logger.info(f"Device registered: {device_id}")

                        user_context = await memory_manager.get_user_context(device_id)
                        await websocket.send_json({
                            "type": "welcome",
                            "message": "Xin chào! Mimi sẵn sàng rồi!"
                        })

                    elif msg_type == "audio_start":
                        is_receiving_audio = True
                        audio_buffer.clear()
                        logger.info("Audio stream started")

                    elif msg_type == "audio_end":
                        is_receiving_audio = False
                        logger.info(f"Audio stream ended, buffer size: {len(audio_buffer)}")
                        await process_voice_input(websocket, device_id, bytes(audio_buffer))
                        audio_buffer.clear()

                    elif msg_type == "text":
                        text = data.get("text", "")
                        await process_text_input(websocket, device_id, text)

                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})

                elif "bytes" in message:
                    if is_receiving_audio:
                        audio_buffer.extend(message["bytes"])

            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {device_id}")
    finally:
        connection_manager.disconnect(websocket)


async def process_voice_input(websocket: WebSocket, device_id: str, audio_data: bytes):
    """Process voice input from robot"""
    try:
        await websocket.send_json({"type": "thinking"})

        # Speech-to-Text
        logger.info("Converting speech to text...")
        text = await speech_processor.speech_to_text(audio_data)

        if not text or text.strip() == "":
            logger.info("No speech detected")
            fallback_text = "Mimi không nghe rõ, cậu nói lại được không?"
            await websocket.send_json({"type": "text", "text": fallback_text})
            audio = await speech_processor.text_to_speech(fallback_text)
            if audio:
                await websocket.send_json({
                    "type": "audio",
                    "data": base64.b64encode(audio).decode('utf-8')
                })
            return

        logger.info(f"Recognized: {text}")
        await process_text_input(websocket, device_id, text)

    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Có lỗi xảy ra, thử lại nhé!"
        })


async def process_text_input(websocket: WebSocket, device_id: str, text: str):
    """Process text input and generate response"""
    try:
        context = await memory_manager.get_user_context(device_id)
        conversation_history = await memory_manager.get_conversation_history(device_id)

        logger.info(f"Generating response for: {text}")
        response = await ai_engine.generate_response(
            user_input=text,
            context=context,
            history=conversation_history
        )

        logger.info(f"AI Response: {response}")

        await memory_manager.save_conversation(
            device_id=device_id,
            user_message=text,
            assistant_message=response
        )
        await memory_manager.extract_and_save_facts(device_id, text, response)

        emotion = await ai_engine.detect_emotion(response)

        if sheets_manager and sheets_manager.is_ready():
            await sheets_manager.log_conversation(
                user_message=text,
                ai_response=response,
                learned_facts=None,
                emotion=emotion
            )

        await websocket.send_json({"type": "text", "text": response})
        await websocket.send_json({"type": "emotion", "emotion": emotion})

        logger.info("Converting text to speech...")
        audio_data = await speech_processor.text_to_speech(response)

        if audio_data:
            await websocket.send_json({
                "type": "audio",
                "data": base64.b64encode(audio_data).decode('utf-8')
            })

    except Exception as e:
        logger.error(f"Error processing text: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Mimi gặp trục trặc rồi!"
        })


def run_server():
    """Chạy server"""
    # Dừng instance cũ nếu có
    if not stop_existing_instance():
        sys.exit(1)

    print("Khoi dong Mimi server...")

    # Ghi PID
    write_pid()
    atexit.register(remove_pid)

    # Signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"Mimi server started (PID: {os.getpid()})")

    # Run uvicorn
    uvicorn.run(
        "main:app",
        host=config.get("server.host", "0.0.0.0"),
        port=config.get("server.port", 8080),
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mimi Robot Backend Server")
    parser.add_argument("--stop", action="store_true", help="Dừng server đang chạy")
    parser.add_argument("--status", action="store_true", help="Kiểm tra trạng thái server")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.stop:
        if stop_existing_instance():
            print("Da dung Mimi server")
        else:
            print("Khong the dung server")
    else:
        run_server()
