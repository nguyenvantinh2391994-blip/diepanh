"""
Mimi Robot - Memory Manager
Handles conversation history and personalization
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config_manager import ConfigManager

logger = logging.getLogger("mimi-memory")


class MemoryManager:
    """Manages conversation history and user facts"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.memory_config = config.memory_config
        self.db_path = Path(self.memory_config.get("database_path", "./data/mimi_memory.db"))
        self.connection = None
        self._ready = False

    async def initialize(self):
        """Initialize database connection"""
        import aiosqlite

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = await aiosqlite.connect(self.db_path)

        # Create tables
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                fact_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, fact_type, fact_value)
            )
        """)

        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                device_id TEXT PRIMARY KEY,
                child_name TEXT,
                preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.connection.commit()

        self._ready = True
        logger.info(f"Memory Manager initialized: {self.db_path}")

    def is_ready(self) -> bool:
        return self._ready

    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()

    async def get_user_context(self, device_id: str) -> Dict:
        """Get user context for AI prompt"""
        context = {
            "child_name": None,
            "preferences": [],
            "facts": []
        }

        if not self.connection:
            return context

        # Get user profile
        async with self.connection.execute(
            "SELECT child_name, preferences FROM user_profiles WHERE device_id = ?",
            (device_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                context["child_name"] = row[0]
                if row[1]:
                    context["preferences"] = json.loads(row[1])

        # Get user facts
        async with self.connection.execute(
            "SELECT fact_type, fact_value FROM user_facts WHERE device_id = ? ORDER BY updated_at DESC LIMIT 20",
            (device_id,)
        ) as cursor:
            facts = await cursor.fetchall()
            context["facts"] = [f"{row[0]}: {row[1]}" for row in facts]

        return context

    async def get_conversation_history(
        self,
        device_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent conversation history"""
        if not self.connection:
            return []

        async with self.connection.execute(
            """SELECT role, content FROM conversations
               WHERE device_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (device_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()

        # Reverse to get chronological order
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    async def save_conversation(
        self,
        device_id: str,
        user_message: str,
        assistant_message: str
    ):
        """Save a conversation exchange"""
        if not self.connection:
            return

        await self.connection.execute(
            "INSERT INTO conversations (device_id, role, content) VALUES (?, ?, ?)",
            (device_id, "user", user_message)
        )

        await self.connection.execute(
            "INSERT INTO conversations (device_id, role, content) VALUES (?, ?, ?)",
            (device_id, "assistant", assistant_message)
        )

        # Update last seen
        await self.connection.execute(
            """INSERT INTO user_profiles (device_id, last_seen)
               VALUES (?, CURRENT_TIMESTAMP)
               ON CONFLICT(device_id) DO UPDATE SET last_seen = CURRENT_TIMESTAMP""",
            (device_id,)
        )

        await self.connection.commit()

    async def extract_and_save_facts(
        self,
        device_id: str,
        user_message: str,
        assistant_message: str
    ):
        """Extract facts from conversation and save them"""
        if not self.connection:
            return

        # Extract child's name
        name_patterns = [
            r"(?:tên (?:con|em|mình) là|con là|em là|mình là)\s+(\w+)",
            r"(?:gọi (?:con|em|mình) là)\s+(\w+)",
            r"^(\w+)\s+(?:nè|đây|ạ)$",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                name = match.group(1).capitalize()
                await self._save_user_name(device_id, name)
                break

        # Extract preferences (things the child likes)
        like_patterns = [
            r"(?:con|em|mình|tôi)\s+thích\s+(.+?)(?:\.|,|$)",
            r"(?:con|em|mình|tôi)\s+yêu\s+(.+?)(?:\.|,|$)",
            r"(?:con|em|mình|tôi)\s+mê\s+(.+?)(?:\.|,|$)",
        ]

        for pattern in like_patterns:
            matches = re.findall(pattern, user_message.lower())
            for match in matches:
                await self._save_fact(device_id, "thích", match.strip())

        # Extract other facts
        fact_patterns = [
            (r"(?:con|em|mình)\s+(\d+)\s+tuổi", "tuổi"),
            (r"(?:con|em|mình)\s+học\s+lớp\s+(\d+)", "lớp"),
            (r"(?:con|em|mình)\s+sống (?:ở|tại)\s+(.+?)(?:\.|,|$)", "nơi ở"),
        ]

        for pattern, fact_type in fact_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                await self._save_fact(device_id, fact_type, match.group(1))

    async def _save_user_name(self, device_id: str, name: str):
        """Save child's name to profile"""
        await self.connection.execute(
            """INSERT INTO user_profiles (device_id, child_name)
               VALUES (?, ?)
               ON CONFLICT(device_id) DO UPDATE SET child_name = ?""",
            (device_id, name, name)
        )
        await self.connection.commit()
        logger.info(f"Saved child name: {name} for device {device_id}")

    async def _save_fact(self, device_id: str, fact_type: str, fact_value: str):
        """Save a fact about the user"""
        await self.connection.execute(
            """INSERT INTO user_facts (device_id, fact_type, fact_value)
               VALUES (?, ?, ?)
               ON CONFLICT(device_id, fact_type, fact_value)
               DO UPDATE SET updated_at = CURRENT_TIMESTAMP""",
            (device_id, fact_type, fact_value)
        )
        await self.connection.commit()
        logger.info(f"Saved fact: {fact_type}={fact_value} for device {device_id}")

    async def add_preference(self, device_id: str, preference: str):
        """Add a preference to user profile"""
        async with self.connection.execute(
            "SELECT preferences FROM user_profiles WHERE device_id = ?",
            (device_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row and row[0]:
            prefs = json.loads(row[0])
        else:
            prefs = []

        if preference not in prefs:
            prefs.append(preference)

        await self.connection.execute(
            """INSERT INTO user_profiles (device_id, preferences)
               VALUES (?, ?)
               ON CONFLICT(device_id) DO UPDATE SET preferences = ?""",
            (device_id, json.dumps(prefs, ensure_ascii=False),
             json.dumps(prefs, ensure_ascii=False))
        )
        await self.connection.commit()

    async def clear_history(self, device_id: str):
        """Clear conversation history for a device"""
        await self.connection.execute(
            "DELETE FROM conversations WHERE device_id = ?",
            (device_id,)
        )
        await self.connection.commit()
        logger.info(f"Cleared history for device {device_id}")

    async def get_stats(self, device_id: str) -> Dict:
        """Get conversation stats for a device"""
        async with self.connection.execute(
            """SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
               FROM conversations WHERE device_id = ?""",
            (device_id,)
        ) as cursor:
            row = await cursor.fetchone()

        return {
            "total_messages": row[0] if row else 0,
            "first_conversation": row[1] if row else None,
            "last_conversation": row[2] if row else None
        }
