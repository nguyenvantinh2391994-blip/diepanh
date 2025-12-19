"""
Mimi Robot - Backend Server
Main entry point for the AI dialogue server
"""

import asyncio
import json
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config_manager import ConfigManager
from ai_engine import AIEngine
from speech_processor import SpeechProcessor
from memory_manager import MemoryManager
from connection_manager import ConnectionManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Mimi Backend Server...")

    await ai_engine.initialize()
    await speech_processor.initialize()
    await memory_manager.initialize()

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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.get("server.host", "0.0.0.0"),
        port=config.get("server.port", 8080),
        reload=config.get("server.debug", True)
    )
