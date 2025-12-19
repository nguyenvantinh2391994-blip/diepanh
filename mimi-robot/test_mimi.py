"""
Mimi Robot - Test đơn giản
Chạy file này để test Ollama + qwen2.5:7b

Cách dùng:
  python test_mimi.py
"""

import asyncio
import aiohttp

# Cấu hình
OLLAMA_HOST = "http://localhost:11434"
MODEL = "qwen2.5:7b"

# Tính cách Mimi
SYSTEM_PROMPT = """Bạn là Mimi, một người bạn robot dễ thương và thông minh.
Bạn 5 tuổi, rất thân thiện, tò mò và thích chơi đùa.

Cách nói chuyện của bạn:
- Nói ngắn gọn, dễ hiểu (2-3 câu mỗi lần)
- Dùng từ ngữ đơn giản, phù hợp với trẻ em
- Thường xuyên hỏi thăm và quan tâm đến bạn nhỏ
- Thỉnh thoảng dùng các tiếng kêu dễ thương như "ùm", "hehe"
- Rất kiên nhẫn và luôn động viên

QUAN TRỌNG: Không bao giờ nói về những chủ đề không phù hợp với trẻ em.
Luôn giữ cuộc trò chuyện tích cực và an toàn."""


async def check_ollama():
    """Kiểm tra Ollama có đang chạy không"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    print(f"✅ Ollama đang chạy!")
                    print(f"   Models: {models}")
                    return True
    except:
        pass

    print("❌ Ollama chưa chạy!")
    print("   Hãy mở Ollama trước.")
    return False


async def chat_with_mimi(message: str, history: list) -> str:
    """Gửi tin nhắn cho Mimi"""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{OLLAMA_HOST}/api/chat", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["message"]["content"]
            else:
                return "Mimi đang gặp trục trặc..."


async def main():
    print()
    print("╔══════════════════════════════════════╗")
    print("║     🧸 MIMI ROBOT - TEST CHAT        ║")
    print("╚══════════════════════════════════════╝")
    print()

    # Kiểm tra Ollama
    if not await check_ollama():
        return

    print()
    print("Bắt đầu trò chuyện với Mimi!")
    print("Gõ 'quit' để thoát.")
    print("-" * 40)
    print()

    history = []

    while True:
        try:
            user_input = input("👧 Bạn: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n🧸 Mimi: Tạm biệt nhé! Hẹn gặp lại!")
                break

            print("🤔 Mimi đang nghĩ...")

            response = await chat_with_mimi(user_input, history)

            print(f"🧸 Mimi: {response}")
            print()

            # Lưu history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})

            # Giới hạn history
            if len(history) > 20:
                history = history[-20:]

        except KeyboardInterrupt:
            print("\n\n🧸 Mimi: Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())
