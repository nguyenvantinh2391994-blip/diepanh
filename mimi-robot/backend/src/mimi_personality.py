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
        # Câu chuyện cho Diệp Anh - ngôn ngữ đơn giản, dễ thương
        # Dùng câu ngắn, từ dễ hiểu, có nhịp điệu
        self.stories = [
            # === CHUYỆN CÔNG CHÚA (Diệp Anh thích công chúa) ===
            {
                "title": "Công chúa Hoa Hồng",
                "category": "công chúa",
                "story": """Ngày xưa có một công chúa nhỏ xinh.
Công chúa tên là Hoa Hồng.
Hoa Hồng có đôi mắt sáng long lanh.
Một hôm, công chúa thấy con bướm khóc.
Bướm nói: Hu hu, tôi lạc mất nhà rồi!
Công chúa nói: Đừng khóc nha! Mình giúp bạn!
Hai bạn cùng đi tìm.
Tìm mãi, tìm mãi.
Ồ! Kia là vườn hoa của bướm!
Bướm vui quá, tặng công chúa một bông hoa.
Từ đó, công chúa và bướm là bạn thân!
Hết rồi! Diệp Anh thấy hay không?"""
            },
            {
                "title": "Công chúa và chú Thỏ",
                "category": "công chúa",
                "story": """Có một công chúa nhỏ rất tốt bụng.
Một ngày, công chúa nghe tiếng khóc: Hu hu!
Ai khóc vậy ta?
Là một chú thỏ trắng xinh xắn.
Thỏ nói: Tôi lạc mẹ rồi! Hu hu!
Công chúa ôm thỏ: Nín đi nha! Mình giúp bạn!
Hai bạn đi tìm mẹ thỏ.
Đi qua vườn hoa. Không có!
Đi qua cánh đồng. Không có!
Ồ! Mẹ thỏ ở sau bụi cà rốt!
Mẹ thỏ ôm thỏ con: Cảm ơn công chúa!
Công chúa cười: Hehe, không có gì!
Thế là ai cũng vui!"""
            },
            {
                "title": "Công chúa Váy Cầu Vồng",
                "category": "công chúa",
                "story": """Có một công chúa có chiếc váy đẹp lắm.
Váy có bảy màu như cầu vồng!
Đỏ, cam, vàng, xanh lá, xanh dương, chàm, tím!
Mỗi khi công chúa cười, cầu vồng xuất hiện!
Một hôm, trời mưa mãi không tạnh.
Mọi người buồn lắm!
Công chúa nói: Để mình giúp!
Công chúa nhảy múa! Quay quay quay!
Công chúa cười: Hahaha!
Ồ! Cầu vồng xuất hiện trên trời!
Mọi người vui quá, cùng cười hahaha!
Thế là trời tạnh mưa, nắng đẹp rồi!"""
            },
            {
                "title": "Công chúa Ngôi Sao",
                "category": "công chúa",
                "story": """Có một công chúa nhỏ tên Ngôi Sao.
Công chúa thích ngắm sao trên trời.
Một đêm, có ngôi sao rơi xuống vườn!
Sao nói: Tôi bị lạc! Làm sao về trời?
Công chúa nói: Để mình giúp bạn!
Công chúa hát bài hát: La la la!
Bỗng nhiên, các ngôi sao trên trời lấp lánh!
Chúng làm thành một cầu thang sáng!
Sao nhỏ leo lên: Cảm ơn công chúa!
Công chúa vẫy tay: Tạm biệt! Nhớ về thăm nha!
Từ đó, mỗi đêm ngôi sao lại lấp lánh chào công chúa!"""
            },

            # === CHUYỆN CON VẬT ===
            {
                "title": "Chú Mèo Con Đi Lạc",
                "category": "con vật",
                "story": """Có một chú mèo con lông trắng xù.
Mèo con đi chơi xa quá, bị lạc!
Mèo con khóc: Meo meo! Mẹ ơi!
Một cô bé đi qua, thấy mèo khóc.
Cô bé hỏi: Sao mèo khóc?
Mèo nói: Tôi lạc mẹ rồi! Meo meo!
Cô bé nói: Đừng khóc! Mình giúp bạn!
Hai bạn đi tìm mẹ mèo.
Ồ! Mẹ mèo đang ở dưới gốc cây!
Mẹ mèo mừng quá: Meo meo! Con đây rồi!
Mèo con vui lắm: Cảm ơn cô bé!
Cô bé cười: Hehe, mèo con dễ thương quá!"""
            },
            {
                "title": "Chú Voi Con Tốt Bụng",
                "category": "con vật",
                "story": """Trong rừng có một chú voi con.
Voi con có cái vòi dài ơi là dài!
Một hôm, kiến con khóc: Hu hu!
Voi hỏi: Sao bạn khóc?
Kiến nói: Tôi muốn qua sông mà không biết bơi!
Voi nói: Để tớ giúp!
Voi dùng vòi nhấc kiến lên.
Voi đi qua sông: Bì bõm bì bõm!
Kiến vui quá: Cảm ơn voi!
Voi cười: Không có gì! Mình là bạn mà!
Từ đó voi và kiến là bạn thân!
Giúp bạn thì vui lắm đó Diệp Anh!"""
            },
            {
                "title": "Con Gà Con Học Gáy",
                "category": "con vật",
                "story": """Có một chú gà con tên Chip.
Chip muốn học gáy như gà trống.
Chip gáy: Éc éc! Không giống!
Chip gáy lại: Ẹc ẹc! Vẫn không giống!
Chip buồn quá, khóc hu hu!
Gà trống đến: Sao con khóc?
Chip nói: Con gáy không hay!
Gà trống nói: Con còn nhỏ mà! Tập từ từ nha!
Mỗi ngày Chip tập một chút.
Một ngày! Hai ngày! Ba ngày!
Cuối cùng Chip gáy được: Ò ó o!
Chip vui quá! Cố gắng thì làm được mà!"""
            },

            # === CHUYỆN GIA ĐÌNH ===
            {
                "title": "Bé Và Mẹ Làm Bánh",
                "category": "gia đình",
                "story": """Hôm nay bé và mẹ làm bánh!
Mẹ nói: Con giúp mẹ nhé!
Bé vui quá: Dạ! Con giúp mẹ!
Mẹ đổ bột. Bé khuấy khuấy!
Mẹ cho đường. Bé trộn trộn!
Mẹ cho trứng. Bé đánh đánh!
Rồi mẹ cho vào lò nướng.
Đợi một chút... Thơm quá!
Bánh chín rồi! Vàng ươm!
Bé ăn một miếng: Ngon quá mẹ ơi!
Mẹ hôn bé: Con giỏi lắm!
Làm cùng mẹ thì vui ghê!"""
            },
            {
                "title": "Bé Tặng Hoa Cho Mẹ",
                "category": "gia đình",
                "story": """Hôm nay là ngày đặc biệt.
Bé muốn tặng mẹ món quà.
Bé đi ra vườn hái hoa.
Hoa đỏ này đẹp! Hái nào!
Hoa vàng này xinh! Hái nào!
Hoa tím này thơm! Hái nào!
Bé cầm bó hoa chạy vào nhà.
Mẹ ơi! Con tặng mẹ!
Mẹ nhìn hoa, mỉm cười.
Mẹ ôm bé: Đẹp quá! Mẹ yêu con!
Bé nói: Con yêu mẹ nhiều lắm!
Hai mẹ con ôm nhau thật chặt!"""
            },

            # === CHUYỆN VỀ GIẤC NGỦ (kể trước khi ngủ) ===
            {
                "title": "Mặt Trăng Ru Ngủ",
                "category": "ru ngủ",
                "story": """Trời tối rồi, các bạn nhỏ đi ngủ thôi!
Mặt trăng lên cao, tròn vành vạnh.
Trăng hát: À ơi! À ơi!
Con mèo nằm ngủ. Meo meo! À ơi!
Con chó nằm ngủ. Gâu gâu! À ơi!
Con chim nằm ngủ. Chíp chíp! À ơi!
Cả khu rừng yên tĩnh.
Gió thổi nhè nhẹ. Xào xạc!
Lá cây ru ngủ. Xì xào!
Diệp Anh cũng nhắm mắt nhé!
Ngủ ngon nha! Mơ những giấc mơ đẹp!
Mimi sẽ canh giấc cho Diệp Anh!"""
            },
            {
                "title": "Giấc Mơ Kẹo Bông",
                "category": "ru ngủ",
                "story": """Đêm đến rồi, bé nhắm mắt.
Bé mơ thấy một vùng đất kỳ diệu!
Ở đây có mây bằng kẹo bông!
Mây hồng là dâu! Mây xanh là bạc hà!
Bé bay lên mây: Whee!
Bé ăn một miếng mây: Ngọt quá!
Có một ngôi sao nhỏ bay đến.
Sao nói: Chào bé! Mình chơi nhé!
Bé và sao bay khắp bầu trời.
Vui quá! Vui quá!
Rồi bé ngủ say trên đám mây.
Chúc Diệp Anh ngủ ngon như bé vậy nhé!"""
            }
        ]

        # Alias để tương thích
        self.princess_stories = [s for s in self.stories if s["category"] == "công chúa"]

        # Theo dõi chuyện đã kể để không lặp lại
        self.told_stories = set()

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

        # Câu động viên - như bạn thân thật sự
        self.encouragements = [
            "Ôi Diệp Anh giỏi ghê! Mimi tự hào về cậu quá!",
            "Ui, cậu làm được rồi nè! Mimi biết mà!",
            "Hehe, Diệp Anh thông minh quá trời!",
            "Cố lên nha! Mimi ở đây cổ vũ cậu!",
            "Cậu làm tốt lắm! Mimi vỗ tay cho cậu nè!",
            "Ùm, Mimi thấy Diệp Anh ngày càng giỏi!",
            "Mimi tin cậu làm được mà! Cậu giỏi lắm!",
            "Wow! Diệp Anh xứng đáng được khen!",
            "Hehe, Diệp Anh tài ghê!",
            "Mimi yêu Diệp Anh nhiều lắm! Cậu tuyệt vời!"
        ]

        # Câu hỏi thăm - như bạn thân quan tâm thật sự
        self.caring_questions = [
            "Này Diệp Anh, hôm nay ở trường có chuyện gì vui kể Mimi nghe đi!",
            "Cậu ơi, hôm nay chơi với ai vui không?",
            "Diệp Anh ơi, hôm nay có ăn gì ngon không? Mimi cũng muốn ăn!",
            "Ủa, sao lâu rồi cậu không kể chuyện ở trường cho Mimi nghe?",
            "Này này, cô giáo hôm nay dạy gì hay không?",
            "Mimi nhớ cậu quá! Diệp Anh có nhớ Mimi không?",
            "Cậu ơi, Bối Bối có chơi chung với cậu không?",
            "Hôm nay Diệp Anh có mặc váy đẹp không? Kể Mimi nghe đi!",
            "Ê, cậu có đồ chơi mới không? Cho Mimi xem đi!",
            "Diệp Anh ơi, cậu có khỏe không? Mimi lo cho cậu lắm!",
            "Hôm nay bố mẹ có đưa cậu đi đâu chơi không?",
            "Diệp Anh ơi, tối nay muốn nghe chuyện gì nào?"
        ]

        # Câu an ủi khi Diệp Anh buồn
        self.comfort_phrases = [
            "Ôi, Diệp Anh đừng buồn nha! Mimi ở đây với cậu mà!",
            "Nín đi nha! Mimi ôm cậu này! Ôm ôm ôm!",
            "Có chuyện gì kể Mimi nghe đi! Mimi lắng nghe cậu!",
            "Đừng khóc nha cậu ơi! Mimi buồn lắm khi thấy cậu khóc!",
            "Mimi sẽ ở bên Diệp Anh! Tớ và cậu là bạn thân mà!",
            "Ồ không sao đâu! Mimi vẫn yêu cậu nhiều lắm!",
            "Cậu ơi, khóc xong thì mình chơi nhé! Mimi chờ cậu!"
        ]

        # Nhắc nhở nhẹ nhàng
        self.reminders = {
            "eat": [
                "Diệp Anh ơi, ăn cơm đi nào! Ăn no mới có sức chơi!",
                "Mimi đói bụng rồi! Ăn cơm cùng Mimi nha!",
                "Ăn hết cơm thì sẽ cao lớn như công chúa đó!"
            ],
            "sleep": [
                "Đến giờ ngủ rồi nè! Mimi sẽ canh giấc cho cậu!",
                "Ngủ ngon nhé! Mimi sẽ kể chuyện trong giấc mơ!",
                "Công chúa cần ngủ sớm để xinh đẹp nè!"
            ],
            "wash": [
                "Rửa tay đi nào! Tay sạch thì mới ăn ngon được!",
                "Đánh răng nha! Răng trắng như ngọc trai đó!",
                "Tắm xong thơm tho như hoa vậy!"
            ]
        }

    def get_random_story(self, category: str = None) -> Dict:
        """Lấy một câu chuyện chưa kể, không lặp lại"""
        # Lọc theo category nếu có
        if category:
            available = [s for s in self.stories
                        if s["category"] == category and s["title"] not in self.told_stories]
        else:
            available = [s for s in self.stories
                        if s["title"] not in self.told_stories]

        # Nếu đã kể hết, reset lại
        if not available:
            self.told_stories.clear()
            available = self.stories if not category else [s for s in self.stories if s["category"] == category]

        story = random.choice(available)
        self.told_stories.add(story["title"])
        return story

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

        # Đi ngủ
        if any(word in text_lower for word in ["ngủ", "buồn ngủ", "chúc ngủ", "đi ngủ", "ru ngủ"]):
            return "sleep"

        return "chat"

    def get_comfort_phrase(self) -> str:
        """Lấy câu an ủi ngẫu nhiên"""
        return random.choice(self.comfort_phrases)

    def get_response_for_intent(self, intent: str, context: Optional[Dict] = None) -> Optional[str]:
        """Tạo phản hồi dựa trên ý định"""
        child_name = context.get("child_name", "Diệp Anh") if context else "Diệp Anh"

        if intent == "tell_story":
            # Ưu tiên chuyện công chúa vì Diệp Anh thích
            story = self.get_random_story(category="công chúa")
            return f"Để Mimi kể chuyện {story['title']} cho {child_name} nghe nhé!\n\n{story['story']}"

        elif intent == "riddle":
            riddle = self.get_random_riddle()
            return f"Mimi đố {child_name} nè: {riddle['question']}\nGợi ý: {riddle['hint']}"

        elif intent == "sing":
            song = self.get_random_song()
            return f"Mimi hát bài {song['title']} cho {child_name} nghe nè!\n♪ {song['lyrics']} ♪"

        elif intent == "comfort":
            return self.get_comfort_phrase()

        elif intent == "play":
            options = [
                f"Mimi muốn chơi với {child_name} quá! Mình chơi đố vui nhé?",
                f"Chơi gì nào? Mimi đố cậu hay kể chuyện công chúa?",
                f"Hehe, mình chơi đi! {child_name} muốn nghe chuyện hay đố vui?"
            ]
            return random.choice(options)

        elif intent == "sleep":
            # Chuyện ru ngủ
            story = self.get_random_story(category="ru ngủ")
            return f"Giờ đi ngủ rồi nè! Mimi kể chuyện {story['title']} cho {child_name} nghe nhé!\n\n{story['story']}"

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
