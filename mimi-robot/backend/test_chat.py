"""Test Mimi chat - Kiểm tra Mimi nói chuyện dài"""
import requests

# Test chat với Mimi
response = requests.post(
    "http://localhost:8080/chat",
    json={"text": "Kể cho Diệp Anh nghe câu chuyện về con thỏ đi!", "device_id": "test"}
)

print("🧸 Mimi trả lời:")
print("-" * 50)
print(response.json().get("response", "Lỗi!"))
print("-" * 50)
print(f"\n📏 Độ dài: {len(response.json().get('response', '').split())} từ")
