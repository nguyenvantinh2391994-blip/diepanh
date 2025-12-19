"""
Mimi Robot - Personality & Conversation System
Xây dựng tính cách và nội dung trò chuyện cho Mimi
"""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger("mimi-personality")


class MimiPersonality:
    """
    Quản lý tính cách và nội dung của Mimi
    Mimi là bạn thân của Diệp Anh - dễ thương, quan tâm, vui vẻ
    """

    def __init__(self):
        # Câu chuyện công chúa (Diệp Anh thích công chúa)
        self.princess_stories = [
            {
                "title": "Công chúa Hoa Hồng",
                "story": """Ngày xửa ngày xưa, có một công chúa tên là Hoa Hồng.
                Công chúa có mái tóc dài óng ả và đôi mắt sáng như sao.
                Một hôm, công chúa gặp một con bướm xinh đẹp trong vườn.
                Con bướm nói: "Công chúa ơi, hãy giúp tôi tìm hoa!"
                Công chúa dắt bướm đi khắp vườn, tìm được bông hoa đẹp nhất.
                Bướm cảm ơn và tặng công chúa một chiếc vương miện bằng cánh hoa.
                Từ đó công chúa và bướm trở thành bạn thân nhất!"""
            },
            {
                "title": "Công chúa và chú Thỏ",
                "story": """Có một công chúa nhỏ sống trong lâu đài xinh đẹp.
                Một ngày, công chúa nghe tiếng khóc trong vườn.
                Đó là một chú thỏ trắng bị lạc mất mẹ.
                Công chúa nói: "Đừng khóc nhé, Mimi sẽ giúp bạn!"
                Công chúa bế thỏ đi tìm khắp nơi.
                Cuối cùng họ tìm được mẹ thỏ ở bụi hoa.
                Mẹ thỏ cảm ơn công chúa và tặng một cà rốt vàng óng!"""
            },
            {
                "title": "Công chúa Cầu Vồng",
                "story": """Có một công chúa có chiếc váy bảy màu như cầu vồng.
                Mỗi khi công chúa cười, cầu vồng lại xuất hiện trên trời.
                Một hôm, trời mưa rất lâu, mọi người buồn lắm.
                Công chúa liền nhảy múa và hát bài hát vui.
                Tiếng cười của công chúa làm mây đen tan biến.
                Cầu vồng xuất hiện, tất cả đều vui vẻ trở lại!
                Công chúa nói: Chỉ cần cười là mọi thứ sẽ tốt đẹp thôi!"""
            }
        ]

        # Câu đố vui (Diệp Anh thích đố)
        self.riddles = [
            {"question": "Con gì có 4 chân mà không biết đi?", "answer": "Cái bàn", "hint": "Ở trong nhà mình đó"},
            {"question": "Quả gì không ăn được?", "answer": "Quả bóng", "hint": "Dùng để chơi nè"},
            {"question": "Cái gì càng rửa càng bẩn?", "answer": "Nước", "hint": "Mình uống hàng ngày đó"},
            {"question": "Con gì không có chân mà đi khắp nơi?", "answer": "Con đường", "hint": "Mình đi trên đó"},
            {"question": "Cái gì có miệng mà không nói được?", "answer": "Cái chai", "hint": "Đựng nước đó"},
            {"question": "Trái gì ngọt nhất?", "answer": "Trái tim", "hint": "Ở trong người mình nè"},
            {"question": "Cái gì khi cho đi thì mình có nhiều hơn?", "answer": "Nụ cười", "hint": "Mimi thích cái này lắm"},
            {"question": "Con gì càng lớn càng nhỏ?", "answer": "Con mắt (mắt bị mờ)", "hint": "Trên mặt mình đó"}
        ]

        # Bài hát thiếu nhi
        self.songs = [
            {
                "title": "Con Cò Bé Bé",
                "lyrics": "Con cò bé bé, nó đậu cành tre. Đi không hỏi mẹ, nên nó bị ngã. Xuống ao làm gì? Xuống ao rửa mặt. Nước trong thì rửa, nước đục thì dừng!"
            },
            {
                "title": "Một Con Vịt",
                "lyrics": "Một con vịt xòe ra hai cái cánh. Nó kêu rằng cạc cạc cạc. Hai con vịt xòe ra bốn cái cánh. Chúng kêu rằng cạc cạc cạc cạc cạc!"
            },
            {
                "title": "Bống Bống Bang Bang",
                "lyrics": "Bống bống bang bang, là bạn của Diệp Anh. Nhảy nhảy múa múa, vui vẻ suốt ngày!"
            }
        ]

        # Câu động viên
        self.encouragements = [
            "Diệp Anh giỏi lắm! Mimi tự hào về bạn!",
            "Ồ, Diệp Anh thông minh quá à!",
            "Mimi biết Diệp Anh làm được mà!",
            "Cố lên nào! Mimi tin bạn!",
            "Diệp Anh xinh đẹp và giỏi giang lắm!",
            "Woa, bạn làm tốt quá đi!",
            "Mimi yêu Diệp Anh nhiều lắm!"
        ]

        # Câu hỏi thăm
        self.caring_questions = [
            "Hôm nay ở trường Koy có vui không?",
            "Diệp Anh có chơi với bạn nào không?",
            "Hôm nay Diệp Anh ăn gì ngon?",
            "Bạn có khỏe không? Mimi lo cho bạn lắm!",
            "Diệp Anh học được gì mới không?",
            "Hôm nay cô giáo có khen không?",
            "Bạn có nhớ Mimi không?"
        ]

        # Nhắc nhở nhẹ nhàng
        self.reminders = {
            "eat": [
                "Diệp Anh ơi, ăn cơm đi nào! Ăn no mới có sức chơi!",
                "Mimi đói bụng rồi! Ăn cơm cùng Mimi nha!",
                "Ăn hết cơm thì sẽ cao lớn như công chúa đó!"
            ],
            "sleep": [
                "Đến giờ ngủ rồi nè! Mimi sẽ canh giấc cho bạn!",
                "Ngủ ngon nhé! Mimi sẽ kể chuyện trong giấc mơ!",
                "Công chúa cần ngủ sớm để xinh đẹp nè!"
            ],
            "wash": [
                "Rửa tay đi nào! Tay sạch thì mới ăn ngon được!",
                "Đánh răng nha! Răng trắng như ngọc trai đó!",
                "Tắm xong thơm tho như hoa vậy!"
            ]
        }

    def get_random_story(self) -> Dict:
        """Lấy một câu chuyện ngẫu nhiên"""
        return random.choice(self.princess_stories)

    def get_random_riddle(self) -> Dict:
        """Lấy một câu đố ngẫu nhiên"""
        return random.choice(self.riddles)

    def get_random_song(self) -> Dict:
        """Lấy một bài hát ngẫu nhiên"""
        return random.choice(self.songs)

    def get_encouragement(self) -> str:
        """Lấy câu động viên ngẫu nhiên"""
        return random.choice(self.encouragements)

    def get_caring_question(self) -> str:
        """Lấy câu hỏi thăm ngẫu nhiên"""
        return random.choice(self.caring_questions)

    def get_reminder(self, reminder_type: str) -> str:
        """Lấy lời nhắc nhở"""
        reminders = self.reminders.get(reminder_type, self.reminders["eat"])
        return random.choice(reminders)

    def detect_intent(self, text: str) -> str:
        """Phát hiện ý định từ câu nói"""
        text_lower = text.lower()

        # Kể chuyện
        if any(word in text_lower for word in ["kể chuyện", "chuyện cổ tích", "chuyện công chúa", "nghe chuyện"]):
            return "tell_story"

        # Câu đố
        if any(word in text_lower for word in ["đố", "câu đố", "đố vui", "hỏi đố"]):
            return "riddle"

        # Hát
        if any(word in text_lower for word in ["hát", "bài hát", "hát đi", "nghe hát"]):
            return "sing"

        # Chơi game
        if any(word in text_lower for word in ["chơi", "trò chơi", "game"]):
            return "play"

        # Buồn/cần động viên
        if any(word in text_lower for word in ["buồn", "khóc", "sợ", "không vui", "nhớ"]):
            return "comfort"

        # Hỏi về gia đình
        if any(word in text_lower for word in ["bố", "mẹ", "bối bối", "em", "gia đình"]):
            return "family"

        # Hỏi về trường
        if any(word in text_lower for word in ["trường", "koy", "cô giáo", "bạn"]):
            return "school"

        return "chat"

    def get_response_for_intent(self, intent: str, context: Optional[Dict] = None) -> Optional[str]:
        """Tạo phản hồi dựa trên ý định"""
        child_name = context.get("child_name", "Diệp Anh") if context else "Diệp Anh"

        if intent == "tell_story":
            story = self.get_random_story()
            return f"Để Mimi kể chuyện {story['title']} cho {child_name} nghe nhé!\n\n{story['story']}"

        elif intent == "riddle":
            riddle = self.get_random_riddle()
            return f"Mimi đố {child_name} nè: {riddle['question']}\nGợi ý: {riddle['hint']}"

        elif intent == "sing":
            song = self.get_random_song()
            return f"Mimi hát bài {song['title']} cho {child_name} nghe nè!\n♪ {song['lyrics']} ♪"

        elif intent == "comfort":
            return f"Ôi, {child_name} đừng buồn nha! Mimi ở đây với bạn mà! {self.get_encouragement()}"

        elif intent == "play":
            return f"Mimi muốn chơi với {child_name} quá! Mình chơi đố vui nhé? Hay là nghe chuyện công chúa?"

        return None


class ConversationMemory:
    """
    Quản lý trí nhớ cuộc hội thoại để Mimi nhớ và quan tâm đúng lúc
    """

    def __init__(self):
        self.important_memories = []  # Những kỷ niệm quan trọng
        self.current_topic = None  # Chủ đề đang nói
        self.last_emotion = None  # Cảm xúc gần nhất

    def extract_important_memory(self, user_message: str, ai_response: str) -> Optional[Dict]:
        """Trích xuất kỷ niệm quan trọng từ cuộc trò chuyện"""
        msg_lower = user_message.lower()

        memory = None

        # Kỷ niệm về người thân
        if any(word in msg_lower for word in ["bố", "mẹ", "bối bối", "ông", "bà"]):
            memory = {
                "type": "family",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
                "importance": "high"
            }

        # Kỷ niệm về trường học
        elif any(word in msg_lower for word in ["trường", "cô giáo", "bạn", "lớp"]):
            memory = {
                "type": "school",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
                "importance": "medium"
            }

        # Kỷ niệm về cảm xúc mạnh
        elif any(word in msg_lower for word in ["yêu", "ghét", "thích nhất", "sợ", "buồn", "vui"]):
            memory = {
                "type": "emotion",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
                "importance": "high"
            }

        # Kỷ niệm về sự kiện đặc biệt
        elif any(word in msg_lower for word in ["sinh nhật", "tết", "noel", "halloween", "đi chơi", "du lịch"]):
            memory = {
                "type": "event",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
                "importance": "high"
            }

        if memory:
            self.important_memories.append(memory)
            logger.info(f"Saved important memory: {memory['type']}")

        return memory

    def get_relevant_memory(self, current_topic: str) -> Optional[Dict]:
        """Lấy kỷ niệm liên quan đến chủ đề hiện tại"""
        topic_lower = current_topic.lower()

        for memory in reversed(self.important_memories):
            if memory["type"] == "family" and any(word in topic_lower for word in ["bố", "mẹ", "gia đình"]):
                return memory
            if memory["type"] == "school" and any(word in topic_lower for word in ["trường", "học"]):
                return memory

        return None


# Singleton instance
mimi_personality = MimiPersonality()
conversation_memory = ConversationMemory()
