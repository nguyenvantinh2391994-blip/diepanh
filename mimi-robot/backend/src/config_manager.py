"""
Mimi Robot - Configuration Manager
Loads and manages configuration from YAML files
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from backend/.env
_backend_dir = Path(__file__).parent.parent
load_dotenv(_backend_dir / ".env")
# Also try current directory
load_dotenv()


class ConfigManager:
    """Manages configuration loading and access"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        config = self._substitute_env_vars(config)

        return config

    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute ${VAR} with environment variables"""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Check for ${VAR} pattern
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return os.getenv(var_name, "")
            return obj
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.
        Example: config.get("server.port")
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> dict:
        """Get an entire configuration section"""
        return self.get(section, {})

    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()

    @property
    def ai_config(self) -> dict:
        """Get AI configuration"""
        provider = self.get("ai.provider", "anthropic")
        return {
            "provider": provider,
            **self.get(f"ai.{provider}", {})
        }

    @property
    def stt_config(self) -> dict:
        """Get Speech-to-Text configuration"""
        provider = self.get("speech_to_text.provider", "whisper")
        return {
            "provider": provider,
            "language": self.get("speech_to_text.language", "vi-VN"),
            **self.get(f"speech_to_text.{provider}", {})
        }

    @property
    def tts_config(self) -> dict:
        """Get Text-to-Speech configuration"""
        provider = self.get("text_to_speech.provider", "edge")
        return {
            "provider": provider,
            "language": self.get("text_to_speech.language", "vi-VN"),
            **self.get(f"text_to_speech.{provider}", {})
        }

    @property
    def personality(self) -> dict:
        """Get Mimi personality configuration"""
        return self.get_section("personality")

    @property
    def memory_config(self) -> dict:
        """Get memory configuration"""
        return self.get_section("memory")
