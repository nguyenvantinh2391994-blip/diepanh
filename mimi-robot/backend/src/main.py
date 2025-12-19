"""
Mimi Robot - Backend Server
Main entry point for the AI dialogue server

Chạy ẩn (daemon mode):
    python main.py          # Tự động tắt instance cũ và chạy mới
    python main.py --stop   # Dừng server đang chạy
    python main.py --status # Kiểm tra trạng thái
"""

import asyncio
import json
import logging
import base64
import os
import sys
import signal
import atexit
from pathlib import Path

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


def setup_logging(daemon_mode: bool = False):
    """Setup logging - console hoặc file tùy chế độ"""
    # Đảm bảo thư mục data tồn tại
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    handlers = []

    if daemon_mode:
        # Daemon mode: log ra file
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(file_handler)
    else:
        # Interactive mode: log ra console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(console_handler)

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers
    )


def get_running_pid() -> int | None:
    """Lấy PID của process đang chạy"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Kiểm tra process còn sống không
            os.kill(pid, 0)
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            # Process không còn tồn tại
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
        print(f"🛑 Đang dừng Mimi server cũ (PID: {pid})...")
        try:
            import time

            if is_windows():
                # Windows: dùng taskkill
                import subprocess
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True
                )
                time.sleep(1)
            else:
                # Linux/Mac: dùng signal
                os.kill(pid, signal.SIGTERM)
                # Đợi process tắt
                for _ in range(10):  # Đợi tối đa 5 giây
                    time.sleep(0.5)
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                else:
                    # Nếu vẫn chưa tắt, kill mạnh
                    os.kill(pid, signal.SIGKILL)

            print("✅ Đã dừng server cũ")
            PID_FILE.unlink(missing_ok=True)
            return True

        except ProcessLookupError:
            PID_FILE.unlink(missing_ok=True)
            return True
        except PermissionError:
            print(f"❌ Không có quyền dừng process {pid}")
            return False
        except Exception as e:
            print(f"⚠️ Lỗi khi dừng: {e}")
            PID_FILE.unlink(missing_ok=True)
            return True
    return True


def is_windows():
    """Kiểm tra có phải Windows không"""
    return sys.platform == "win32"


def daemonize():
    """Chuyển process thành daemon (chạy ẩn) - chỉ Linux/Mac"""
    if is_windows():
        # Windows không hỗ trợ fork, bỏ qua daemonize
        # Server sẽ chạy trong subprocess riêng
        return

    # Fork lần 1
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process thoát
            sys.exit(0)
    except OSError as e:
        print(f"Fork #1 failed: {e}")
        sys.exit(1)

    # Tách khỏi terminal
    os.setsid()
    os.umask(0)

    # Fork lần 2
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"Fork #2 failed: {e}")
        sys.exit(1)

    # Redirect stdin/stdout/stderr
    sys.stdout.flush()
    sys.stderr.flush()

    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())

    # stdout và stderr ghi vào log file
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fd = os.open(str(LOG_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
    os.dup2(log_fd, sys.stdout.fileno())
    os.dup2(log_fd, sys.stderr.fileno())


def start_background_windows():
    """Khởi động server ẩn trên Windows bằng subprocess"""
    import subprocess

    # Tìm pythonw.exe để chạy không có console window
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")

    # Nếu có pythonw thì dùng, không thì dùng python với CREATE_NO_WINDOW
    script_path = Path(__file__).resolve()

    # Tạo startup info để ẩn window
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    # Chạy với flag --foreground trong subprocess (vì đã detach rồi)
    cmd = [python_exe, str(script_path), "--foreground"]

    process = subprocess.Popen(
        cmd,
        stdout=open(LOG_FILE, 'a', encoding='utf-8'),
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        cwd=str(script_path.parent)
    )

    # Ghi PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(process.pid))

    print(f"✅ Mimi server đã khởi động (PID: {process.pid})")
    print(f"📝 Log file: {LOG_FILE}")
    return process.pid


def show_status():
    """Hiển thị trạng thái server"""
    pid = get_running_pid()
    if pid:
        print(f"✅ Mimi server đang chạy (PID: {pid})")
        print(f"📝 Log file: {LOG_FILE}")
        if LOG_FILE.exists():
            # Hiển thị 10 dòng log cuối
            lines = LOG_FILE.read_text().splitlines()[-10:]
            if lines:
                print("\n--- Log gần đây ---")
                for line in lines:
                    print(line)
    else:
        print("❌ Mimi server không chạy")


# Setup logging mặc định (sẽ được cập nhật trong main)
logger = logging.getLogger("mimi-server")

# Initialize FastAPI app
app = FastAPI(
    title="Mimi Robot API",
    description="Backend server for Mimi - AI Voice Robot",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Mimi Backend Server...")

    await ai_engine.initialize()
    await speech_processor.initialize()
    await memory_manager.initialize()

    # Initialize Google Sheets (optional)
    if sheets_manager:
        success = await sheets_manager.initialize()
        if success:
            logger.info("Google Sheets logging enabled")
        else:
            logger.warning("Google Sheets not available - logging disabled")

    logger.info("All services initialized successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Mimi Backend Server...")
    await memory_manager.close()


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


# Wake words to detect
WAKE_WORDS = ["mimi", "mi mi", "mí mi", "mi-mi", "mimi ơi", "mimi oi", "ê mimi", "hey mimi"]


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
            # Remove wake word and clean up
            result = text_lower.replace(wake_word, "").strip()
            # Remove common filler words after wake word
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
    Only responds if wake word "Mimi" is detected.
    """
    try:
        # Receive raw audio data
        audio_data = await request.body()
        logger.info(f"[HTTP] Received {len(audio_data)} bytes of audio")

        if len(audio_data) < 1000:
            logger.warning("[HTTP] Audio too short, ignoring")
            # Return empty response - don't speak
            return Response(content=b"", status_code=204)

        # Speech-to-Text
        logger.info("[HTTP] Converting speech to text...")
        recognized_text = await speech_processor.speech_to_text(audio_data)

        if not recognized_text or recognized_text.strip() == "":
            logger.info("[HTTP] No speech detected, ignoring")
            return Response(content=b"", status_code=204)

        logger.info(f"[HTTP] Recognized: {recognized_text}")

        # Check for wake word
        if not contains_wake_word(recognized_text):
            logger.info("[HTTP] No wake word detected, ignoring")
            return Response(content=b"", status_code=204)

        logger.info("[HTTP] Wake word detected! Processing...")

        # Remove wake word to get actual command
        command_text = remove_wake_word(recognized_text)
        logger.info(f"[HTTP] Command after removing wake word: {command_text}")

        # Use a default device_id for HTTP mode (can be improved with device identification)
        device_id = "default_device"

        # Get user context and conversation history
        context = await memory_manager.get_user_context(device_id)
        history = await memory_manager.get_conversation_history(device_id, limit=10)

        # If only wake word was said (no command), respond with greeting
        if not command_text or len(command_text) < 2:
            if context.get("child_name"):
                response_text = f"Dạ, {context['child_name']}! Mimi đang nghe đây! Bạn cần gì nào?"
            else:
                response_text = "Dạ, Mimi đang nghe đây! Bạn cần gì nào?"
        else:
            # Get AI response with context
            logger.info("[HTTP] Generating AI response...")
            response_text = await ai_engine.generate_response(
                user_input=command_text,
                context=context,
                history=history
            )
            logger.info(f"[HTTP] AI Response: {response_text}")

            # Save conversation and extract facts
            await memory_manager.save_conversation(device_id, command_text, response_text)
            await memory_manager.extract_and_save_facts(device_id, command_text, response_text)

            # Log to Google Sheets (if enabled)
            if sheets_manager and sheets_manager.is_ready():
                await sheets_manager.log_conversation(
                    user_message=command_text,
                    ai_response=response_text,
                    learned_facts=None,
                    emotion=None
                )

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
    """
    Simple endpoint to test TTS and speaker.
    Returns a test audio file.
    """
    try:
        test_text = "Xin chào! Mimi hoạt động bình thường!"
        logger.info(f"[TEST] Generating TTS for: {test_text}")

        tts_audio = await speech_processor.text_to_speech(test_text)

        if tts_audio:
            logger.info(f"[TEST] Generated {len(tts_audio)} bytes of PCM audio")
            return Response(
                content=tts_audio,
                media_type="audio/pcm"
            )
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

        # Audio buffer for incoming voice data
        audio_buffer = bytearray()
        is_receiving_audio = False

        while True:
            try:
                # Receive message (text or binary)
                message = await websocket.receive()

                if "text" in message:
                    # Handle text/JSON messages
                    data = json.loads(message["text"])
                    msg_type = data.get("type", "")

                    if msg_type == "device_info":
                        device_id = data.get("device_id")
                        await connection_manager.register_device(websocket, device_id)
                        logger.info(f"Device registered: {device_id}")

                        # Load user memory
                        user_context = await memory_manager.get_user_context(device_id)
                        await websocket.send_json({
                            "type": "welcome",
                            "message": f"Xin chào! Mimi sẵn sàng rồi!"
                        })

                    elif msg_type == "audio_start":
                        is_receiving_audio = True
                        audio_buffer.clear()
                        logger.info("Audio stream started")

                    elif msg_type == "audio_end":
                        is_receiving_audio = False
                        logger.info(f"Audio stream ended, buffer size: {len(audio_buffer)}")

                        # Process the complete audio
                        await process_voice_input(
                            websocket, device_id, bytes(audio_buffer)
                        )
                        audio_buffer.clear()

                    elif msg_type == "text":
                        # Direct text input (for testing)
                        text = data.get("text", "")
                        await process_text_input(websocket, device_id, text)

                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})

                elif "bytes" in message:
                    # Handle binary audio data
                    if is_receiving_audio:
                        audio_buffer.extend(message["bytes"])

            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {device_id}")
    finally:
        connection_manager.disconnect(websocket)


async def process_voice_input(websocket: WebSocket, device_id: str, audio_data: bytes):
    """Process voice input from robot"""
    try:
        # Notify robot that we're processing
        await websocket.send_json({"type": "thinking"})

        # DEBUG MODE: Always respond with test message to verify speaker works
        logger.info(f"Received {len(audio_data)} bytes of audio - sending test response")

        test_text = "Xin chào! Mimi nghe thấy bạn rồi!"
        await websocket.send_json({
            "type": "text",
            "text": test_text
        })

        # Generate and send TTS audio
        tts_audio = await speech_processor.text_to_speech(test_text)
        if tts_audio:
            import base64
            audio_base64 = base64.b64encode(tts_audio).decode('utf-8')
            logger.info(f"Sending TTS audio: {len(tts_audio)} bytes")
            await websocket.send_json({
                "type": "audio",
                "data": audio_base64
            })
        else:
            logger.error("TTS failed to generate audio")
        return

        # Original code below (disabled for testing)
        # Speech-to-Text
        logger.info("Converting speech to text...")
        text = await speech_processor.speech_to_text(audio_data)

        if not text or text.strip() == "":
            logger.info("No speech detected")
            fallback_text = "Mimi không nghe rõ, bạn nói lại được không?"
            await websocket.send_json({
                "type": "text",
                "text": fallback_text
            })
            # Also send audio for the fallback message
            audio_data = await speech_processor.text_to_speech(fallback_text)
            if audio_data:
                import base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                await websocket.send_json({
                    "type": "audio",
                    "data": audio_base64
                })
            return

        logger.info(f"Recognized: {text}")

        # Process with AI
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
        # Get user context and memory
        context = await memory_manager.get_user_context(device_id)
        conversation_history = await memory_manager.get_conversation_history(device_id)

        # Generate AI response
        logger.info(f"Generating response for: {text}")
        response = await ai_engine.generate_response(
            user_input=text,
            context=context,
            history=conversation_history
        )

        logger.info(f"AI Response: {response}")

        # Save to memory
        await memory_manager.save_conversation(
            device_id=device_id,
            user_message=text,
            assistant_message=response
        )

        # Extract any memory updates (names, preferences, etc.)
        await memory_manager.extract_and_save_facts(device_id, text, response)

        # Determine emotion based on response
        emotion = await ai_engine.detect_emotion(response)

        # Log to Google Sheets (if enabled)
        if sheets_manager and sheets_manager.is_ready():
            await sheets_manager.log_conversation(
                user_message=text,
                ai_response=response,
                learned_facts=None,
                emotion=emotion
            )

        # Send text response first
        await websocket.send_json({
            "type": "text",
            "text": response
        })

        # Send emotion
        await websocket.send_json({
            "type": "emotion",
            "emotion": emotion
        })

        # Convert to speech and send audio
        logger.info("Converting text to speech...")
        audio_data = await speech_processor.text_to_speech(response)

        if audio_data:
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            await websocket.send_json({
                "type": "audio",
                "data": audio_base64
            })

    except Exception as e:
        logger.error(f"Error processing text: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Mimi gặp trục trặc rồi!"
        })


def run_server(daemon_mode: bool = True):
    """Chạy server"""
    # Dừng instance cũ nếu có
    if not stop_existing_instance():
        sys.exit(1)

    if daemon_mode:
        print("🚀 Khởi động Mimi server (chế độ ẩn)...")

        if is_windows():
            # Windows: chạy subprocess riêng
            start_background_windows()
            sys.exit(0)  # Parent thoát sau khi spawn xong
        else:
            # Linux/Mac: fork daemon
            daemonize()
            setup_logging(daemon_mode=True)
    else:
        setup_logging(daemon_mode=False)
        print("🚀 Khởi động Mimi server (chế độ interactive)...")

    # Ghi PID và đăng ký cleanup
    write_pid()
    atexit.register(remove_pid)

    # Xử lý signal để cleanup khi bị kill
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"Mimi server started (PID: {os.getpid()})")

    # Chạy uvicorn
    uvicorn.run(
        "main:app",
        host=config.get("server.host", "0.0.0.0"),
        port=config.get("server.port", 8080),
        reload=False,  # Không reload trong daemon mode
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mimi Robot Backend Server")
    parser.add_argument("--stop", action="store_true", help="Dừng server đang chạy")
    parser.add_argument("--status", action="store_true", help="Kiểm tra trạng thái server")
    parser.add_argument("--foreground", "-f", action="store_true", help="Chạy ở chế độ foreground (hiển thị log)")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.stop:
        if stop_existing_instance():
            print("✅ Đã dừng Mimi server")
        else:
            print("❌ Không thể dừng server")
    else:
        # Chạy server (mặc định là daemon mode)
        run_server(daemon_mode=not args.foreground)
