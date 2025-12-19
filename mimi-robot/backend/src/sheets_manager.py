"""
Mimi Robot - Google Sheets Manager
Lưu trữ cuộc hội thoại và dữ liệu học được vào Google Sheets
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger("mimi-sheets")


class SheetsManager:
    """Quản lý lưu trữ dữ liệu vào Google Sheets"""

    def __init__(self, credentials_path: str, spreadsheet_name: str = "mimi", sheet_name: str = "2025"):
        self.credentials_path = Path(credentials_path)
        self.spreadsheet_name = spreadsheet_name
        self.sheet_name = sheet_name
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self._ready = False

    async def initialize(self):
        """Khởi tạo kết nối Google Sheets"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            if not self.credentials_path.exists():
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                return False

            # Scopes cần thiết cho Google Sheets
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Xác thực với Google
            creds = Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=scopes
            )
            self.client = gspread.authorize(creds)

            # Mở spreadsheet
            try:
                self.spreadsheet = self.client.open(self.spreadsheet_name)
                logger.info(f"Opened spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                logger.error(f"Spreadsheet '{self.spreadsheet_name}' not found!")
                logger.info("Hãy tạo spreadsheet mới với tên 'mimi' và chia sẻ với service account email")
                return False

            # Mở hoặc tạo worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(self.sheet_name)
                logger.info(f"Using worksheet: {self.sheet_name}")
            except gspread.WorksheetNotFound:
                # Tạo worksheet mới
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=self.sheet_name,
                    rows=1000,
                    cols=10
                )
                # Thêm header
                self.worksheet.update('A1:G1', [[
                    'Thời gian',
                    'Loại',
                    'Người nói',
                    'Nội dung',
                    'Phản hồi AI',
                    'Dữ liệu học được',
                    'Cảm xúc'
                ]])
                logger.info(f"Created new worksheet: {self.sheet_name}")

            self._ready = True
            logger.info("Google Sheets Manager initialized successfully!")
            return True

        except ImportError:
            logger.warning("gspread not installed! Run: pip install gspread google-auth")
            return False
        except Exception as e:
            logger.error(f"Google Sheets initialization error: {e}")
            return False

    def is_ready(self) -> bool:
        return self._ready

    async def log_conversation(
        self,
        user_message: str,
        ai_response: str,
        learned_facts: Optional[List[str]] = None,
        emotion: Optional[str] = None
    ):
        """Ghi log cuộc hội thoại vào Google Sheets"""
        if not self._ready or not self.worksheet:
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            facts_str = ", ".join(learned_facts) if learned_facts else ""

            row = [
                timestamp,
                "conversation",
                "Diệp Anh",
                user_message,
                ai_response,
                facts_str,
                emotion or ""
            ]

            # Thêm row mới vào cuối sheet
            self.worksheet.append_row(row)
            logger.debug(f"Logged conversation to Google Sheets")

        except Exception as e:
            logger.error(f"Error logging to Google Sheets: {e}")

    async def log_fact(self, fact_type: str, fact_value: str):
        """Ghi log dữ liệu học được"""
        if not self._ready or not self.worksheet:
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = [
                timestamp,
                "fact",
                "system",
                f"{fact_type}: {fact_value}",
                "",
                f"{fact_type}={fact_value}",
                ""
            ]

            self.worksheet.append_row(row)
            logger.debug(f"Logged fact: {fact_type}={fact_value}")

        except Exception as e:
            logger.error(f"Error logging fact to Google Sheets: {e}")

    async def log_event(self, event_type: str, details: str):
        """Ghi log sự kiện (wake up, sleep, etc.)"""
        if not self._ready or not self.worksheet:
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = [
                timestamp,
                "event",
                "system",
                event_type,
                details,
                "",
                ""
            ]

            self.worksheet.append_row(row)
            logger.debug(f"Logged event: {event_type}")

        except Exception as e:
            logger.error(f"Error logging event to Google Sheets: {e}")

    async def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """Lấy các cuộc hội thoại gần đây từ Google Sheets"""
        if not self._ready or not self.worksheet:
            return []

        try:
            # Lấy tất cả dữ liệu
            all_values = self.worksheet.get_all_values()

            # Bỏ header và lấy các row conversation
            conversations = []
            for row in reversed(all_values[1:]):  # Đảo ngược để lấy mới nhất
                if len(row) >= 5 and row[1] == "conversation":
                    conversations.append({
                        "timestamp": row[0],
                        "user_message": row[3],
                        "ai_response": row[4],
                        "emotion": row[6] if len(row) > 6 else ""
                    })
                    if len(conversations) >= limit:
                        break

            return list(reversed(conversations))  # Đảo lại theo thứ tự thời gian

        except Exception as e:
            logger.error(f"Error getting conversations from Google Sheets: {e}")
            return []

    async def get_all_facts(self) -> List[Dict]:
        """Lấy tất cả dữ liệu đã học từ Google Sheets"""
        if not self._ready or not self.worksheet:
            return []

        try:
            all_values = self.worksheet.get_all_values()

            facts = []
            for row in all_values[1:]:
                if len(row) >= 6 and row[1] == "fact" and row[5]:
                    # Parse fact từ format "type=value"
                    parts = row[5].split("=", 1)
                    if len(parts) == 2:
                        facts.append({
                            "timestamp": row[0],
                            "type": parts[0],
                            "value": parts[1]
                        })

            return facts

        except Exception as e:
            logger.error(f"Error getting facts from Google Sheets: {e}")
            return []
