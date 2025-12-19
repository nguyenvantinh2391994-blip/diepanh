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
        self.output_format = config.get("output_format", "pcm")  # "mp3" or "pcm"

    async def initialize(self):
        logger.info(f"Edge TTS initialized with voice: {self.voice}, output: {self.output_format}")

    async def synthesize(self, text: str) -> bytes:
        try:
            import edge_tts

            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )

            mp3_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_data += chunk["data"]

            if not mp3_data:
                logger.error("Edge TTS returned empty audio")
                return b""

            # Convert MP3 to raw PCM for ESP32
            if self.output_format == "pcm":
                return self._mp3_to_pcm(mp3_data)
            else:
                return mp3_data

        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return b""

    def _mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """Convert MP3 to raw PCM (16kHz, 16-bit, mono)"""
        try:
            from pydub import AudioSegment

            # Load MP3 from bytes
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))

            # Convert to 16kHz, mono, 16-bit
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit = 2 bytes

            # Get raw PCM data
            pcm_data = audio.raw_data

            logger.info(f"Converted {len(mp3_data)} bytes MP3 to {len(pcm_data)} bytes PCM")
            return pcm_data

        except ImportError:
            logger.error("pydub not installed! Install with: pip install pydub")
            logger.error("Also need ffmpeg: apt install ffmpeg")
            return b""
        except Exception as e:
            logger.error(f"MP3 to PCM conversion error: {e}")
            return b""


class GeminiTTS(TTSProvider):
    """Google Gemini 2.5 Flash TTS"""

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gemini-2.5-flash-preview-tts")
        self.voice = config.get("voice", "Kore")  # Friendly female voice
        self.fallback_tts = None  # Will be set to EdgeTTS

    async def initialize(self):
        if not self.api_key:
            logger.warning("Gemini API key not set - TTS will fallback to Edge")
            logger.warning("Kiem tra file .env trong thu muc backend/ co GEMINI_API_KEY=xxx")
            return

        # Mask API key for logging (show first 10 chars)
        masked_key = self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
        logger.info(f"Gemini TTS initialized with voice: {self.voice}, API key: {masked_key}")

    def set_fallback(self, fallback: TTSProvider):
        """Set fallback TTS provider (Edge TTS)"""
        self.fallback_tts = fallback

    async def synthesize(self, text: str) -> bytes:
        if not self.api_key:
            logger.warning("Gemini API key not available, using fallback")
            if self.fallback_tts:
                return await self.fallback_tts.synthesize(text)
            return b""

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            response = client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice,
                            )
                        )
                    ),
                ),
            )

            # Get audio data from response
            audio_data = response.candidates[0].content.parts[0].inline_data.data

            # Gemini returns WAV, need to convert to PCM
            pcm_data = self._wav_to_pcm(audio_data)
            logger.info(f"Gemini TTS: generated {len(pcm_data)} bytes PCM")
            return pcm_data

        except Exception as e:
            logger.error(f"Gemini TTS error: {e}, using fallback")
            if self.fallback_tts:
                return await self.fallback_tts.synthesize(text)
            return b""

    def _wav_to_pcm(self, wav_data: bytes) -> bytes:
        """Convert WAV to raw PCM (16kHz, 16-bit, mono)"""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_wav(io.BytesIO(wav_data))
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)

            return audio.raw_data
        except Exception as e:
            logger.error(f"WAV to PCM conversion error: {e}")
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

        # Always create Edge TTS as fallback
        edge_tts_config = self.config.get_section("text_to_speech").get("edge", {})
        edge_tts_config.update({
            "voice": self.config.get("text_to_speech.edge.voice", "vi-VN-HoaiMyNeural"),
            "rate": self.config.get("text_to_speech.edge.rate", "+10%"),
            "pitch": self.config.get("text_to_speech.edge.pitch", "+15Hz"),
            "output_format": "pcm"
        })
        edge_fallback = EdgeTTS(edge_tts_config)
        await edge_fallback.initialize()

        if tts_provider_name == "edge":
            self.tts_provider = edge_fallback
        elif tts_provider_name == "gemini":
            gemini_config = self.config.get_section("text_to_speech").get("gemini", {})
            self.tts_provider = GeminiTTS(gemini_config)
            self.tts_provider.set_fallback(edge_fallback)
            await self.tts_provider.initialize()
        elif tts_provider_name == "google":
            self.tts_provider = GoogleTTS(tts_config)
            await self.tts_provider.initialize()
        else:
            logger.warning(f"Unknown TTS provider: {tts_provider_name}, using Edge")
            self.tts_provider = edge_fallback

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
