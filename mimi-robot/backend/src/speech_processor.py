"""
Mimi Robot - Speech Processor
Handles Speech-to-Text and Text-to-Speech
"""

import io
import logging
from typing import Optional
from abc import ABC, abstractmethod

from config_manager import ConfigManager

logger = logging.getLogger("mimi-speech")


class STTProvider(ABC):
    """Abstract Speech-to-Text provider"""

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        pass


class TTSProvider(ABC):
    """Abstract Text-to-Speech provider"""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass


class WhisperSTT(STTProvider):
    """OpenAI Whisper STT (local or API)"""

    def __init__(self, config: dict):
        self.model_name = config.get("model", "base")
        self.device = config.get("device", "cpu")
        self.model = None

    async def initialize(self):
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("Whisper not installed, using fallback")

    async def transcribe(self, audio_data: bytes) -> str:
        if not self.model:
            return ""

        import tempfile
        import numpy as np
        import wave
        import struct
        import os

        try:
            # Save audio to a debug file for inspection
            debug_path = os.path.join(os.path.dirname(__file__), "..", "debug_audio.wav")
            with wave.open(debug_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            logger.info(f"DEBUG: Saved audio to {debug_path}")

            # Create proper WAV file from raw PCM data
            # Audio format: 16-bit mono, 16000 Hz
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            # Write WAV file with proper headers
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(16000)  # 16000 Hz
                wav_file.writeframes(audio_data)

            logger.info(f"Saved WAV file: {len(audio_data)} bytes of audio")

            # Transcribe
            result = self.model.transcribe(
                temp_path,
                language="vi",
                fp16=False
            )

            transcribed_text = result.get("text", "").strip()
            logger.info(f"Whisper result: '{transcribed_text}'")

            os.unlink(temp_path)

            return transcribed_text

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""


class GoogleSTT(STTProvider):
    """Google Cloud Speech-to-Text"""

    def __init__(self, config: dict):
        self.credentials_path = config.get("credentials_path", "")
        self.language = config.get("language", "vi-VN")
        self.client = None

    async def initialize(self):
        try:
            from google.cloud import speech
            import os

            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

            self.client = speech.SpeechClient()
            logger.info("Google STT client initialized")
        except Exception as e:
            logger.warning(f"Google STT init failed: {e}")

    async def transcribe(self, audio_data: bytes) -> str:
        if not self.client:
            return ""

        from google.cloud import speech

        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language,
        )

        response = self.client.recognize(config=config, audio=audio)

        for result in response.results:
            return result.alternatives[0].transcript

        return ""


class EdgeTTS(TTSProvider):
    """Microsoft Edge TTS (free, high quality)"""

    def __init__(self, config: dict):
        self.voice = config.get("voice", "vi-VN-HoaiMyNeural")
        self.rate = config.get("rate", "+0%")
        self.pitch = config.get("pitch", "+0%")

    async def initialize(self):
        logger.info(f"Edge TTS initialized with voice: {self.voice}")

    async def synthesize(self, text: str) -> bytes:
        try:
            import edge_tts

            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )

            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            return audio_data

        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return b""


class GoogleTTS(TTSProvider):
    """Google Cloud Text-to-Speech"""

    def __init__(self, config: dict):
        self.credentials_path = config.get("credentials_path", "")
        self.language = config.get("language", "vi-VN")
        self.voice_name = config.get("voice", "vi-VN-Wavenet-A")
        self.client = None

    async def initialize(self):
        try:
            from google.cloud import texttospeech
            import os

            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google TTS client initialized")
        except Exception as e:
            logger.warning(f"Google TTS init failed: {e}")

    async def synthesize(self, text: str) -> bytes:
        if not self.client:
            return b""

        from google.cloud import texttospeech

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language,
            name=self.voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content


class SpeechProcessor:
    """Main Speech Processor managing STT and TTS"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.stt_provider: Optional[STTProvider] = None
        self.tts_provider: Optional[TTSProvider] = None
        self._ready = False

    async def initialize(self):
        """Initialize speech providers"""
        # Initialize STT
        stt_config = self.config.stt_config
        stt_provider_name = stt_config.get("provider", "whisper")

        logger.info(f"Initializing STT provider: {stt_provider_name}")

        if stt_provider_name == "whisper":
            self.stt_provider = WhisperSTT(stt_config)
        elif stt_provider_name == "google":
            self.stt_provider = GoogleSTT(stt_config)
        else:
            logger.warning(f"Unknown STT provider: {stt_provider_name}")

        if self.stt_provider:
            await self.stt_provider.initialize()

        # Initialize TTS
        tts_config = self.config.tts_config
        tts_provider_name = tts_config.get("provider", "edge")

        logger.info(f"Initializing TTS provider: {tts_provider_name}")

        if tts_provider_name == "edge":
            self.tts_provider = EdgeTTS(tts_config)
        elif tts_provider_name == "google":
            self.tts_provider = GoogleTTS(tts_config)
        else:
            logger.warning(f"Unknown TTS provider: {tts_provider_name}")

        if self.tts_provider:
            await self.tts_provider.initialize()

        self._ready = True
        logger.info("Speech Processor initialized")

    def is_ready(self) -> bool:
        return self._ready

    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech audio to text"""
        if not self.stt_provider:
            logger.warning("No STT provider available")
            return ""

        return await self.stt_provider.transcribe(audio_data)

    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio"""
        if not self.tts_provider:
            logger.warning("No TTS provider available")
            return b""

        return await self.tts_provider.synthesize(text)
