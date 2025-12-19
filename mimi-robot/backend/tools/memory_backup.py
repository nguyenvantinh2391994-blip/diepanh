#!/usr/bin/env python3
"""
Mimi Robot - Memory Backup & Restore Tool
Công cụ sao lưu và khôi phục ký ức của Mimi

Sử dụng:
  python memory_backup.py export         # Xuất ký ức ra file
  python memory_backup.py import FILE    # Nhập ký ức từ file
  python memory_backup.py stats          # Xem thống kê
"""

import argparse
import json
import os
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Thư mục mặc định
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "mimi_memory.db"
BACKUP_DIR = Path(__file__).parent.parent / "backups"


def ensure_backup_dir():
    """Tạo thư mục backup nếu chưa có"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection(db_path=None):
    """Kết nối database"""
    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        print(f"❌ Không tìm thấy database: {path}")
        print("   Mimi chưa có ký ức nào để backup!")
        sys.exit(1)
    return sqlite3.connect(path)


def export_memory(output_path=None):
    """Xuất toàn bộ ký ức của Mimi ra file ZIP"""
    ensure_backup_dir()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = BACKUP_DIR / f"mimi_memory_{timestamp}.zip"

    print("📦 Đang xuất ký ức của Mimi...")

    conn = get_db_connection()
    cursor = conn.cursor()

    data = {
        "export_date": datetime.now().isoformat(),
        "version": "1.0",
        "profiles": [],
        "conversations": [],
        "facts": [],
    }

    # Export user profiles
    cursor.execute("SELECT * FROM user_profiles")
    columns = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        data["profiles"].append(dict(zip(columns, row)))

    # Export conversations
    cursor.execute("SELECT * FROM conversations ORDER BY timestamp")
    columns = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        data["conversations"].append(dict(zip(columns, row)))

    # Export facts
    cursor.execute("SELECT * FROM user_facts")
    columns = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        data["facts"].append(dict(zip(columns, row)))

    conn.close()

    # Tạo file ZIP
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Lưu dữ liệu chính
        zf.writestr("memory.json", json.dumps(data, ensure_ascii=False, indent=2))

        # Tạo file README
        readme = f"""# Mimi Memory Backup
Ngày xuất: {data['export_date']}
Số hồ sơ: {len(data['profiles'])}
Số cuộc hội thoại: {len(data['conversations'])}
Số sự kiện nhớ: {len(data['facts'])}

Để khôi phục, chạy:
  python memory_backup.py import {output_path.name}
"""
        zf.writestr("README.txt", readme)

    file_size = output_path.stat().st_size / 1024  # KB

    print(f"✅ Đã xuất thành công!")
    print(f"   📁 File: {output_path}")
    print(f"   📊 Kích thước: {file_size:.1f} KB")
    print(f"   👤 Số hồ sơ: {len(data['profiles'])}")
    print(f"   💬 Số hội thoại: {len(data['conversations'])}")
    print(f"   🧠 Số ký ức: {len(data['facts'])}")

    return output_path


def import_memory(input_path, merge=True):
    """Nhập ký ức từ file backup"""
    input_path = Path(input_path)

    if not input_path.exists():
        print(f"❌ Không tìm thấy file: {input_path}")
        sys.exit(1)

    print(f"📥 Đang nhập ký ức từ: {input_path}")

    # Đọc file ZIP
    with zipfile.ZipFile(input_path, 'r') as zf:
        memory_data = json.loads(zf.read("memory.json").decode('utf-8'))

    print(f"   📅 Ngày backup: {memory_data['export_date']}")
    print(f"   👤 Số hồ sơ: {len(memory_data['profiles'])}")
    print(f"   💬 Số hội thoại: {len(memory_data['conversations'])}")

    # Backup database hiện tại trước khi import
    if DEFAULT_DB_PATH.exists():
        backup_current = BACKUP_DIR / f"before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        ensure_backup_dir()
        import shutil
        shutil.copy(DEFAULT_DB_PATH, backup_current)
        print(f"   💾 Đã backup database hiện tại: {backup_current.name}")

    # Tạo database mới nếu chưa có
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()

    # Tạo tables nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            device_id TEXT PRIMARY KEY,
            child_name TEXT,
            preferences TEXT,
            created_at TEXT,
            last_seen TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            device_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY,
            device_id TEXT,
            fact_type TEXT,
            fact_value TEXT,
            confidence REAL,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Import profiles
    for profile in memory_data["profiles"]:
        if merge:
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles
                (device_id, child_name, preferences, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (
                profile.get("device_id"),
                profile.get("child_name"),
                profile.get("preferences"),
                profile.get("created_at"),
                profile.get("last_seen")
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profiles
                (device_id, child_name, preferences, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (
                profile.get("device_id"),
                profile.get("child_name"),
                profile.get("preferences"),
                profile.get("created_at"),
                profile.get("last_seen")
            ))

    # Import conversations
    for conv in memory_data["conversations"]:
        cursor.execute("""
            INSERT INTO conversations
            (device_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            conv.get("device_id"),
            conv.get("role"),
            conv.get("content"),
            conv.get("timestamp")
        ))

    # Import facts
    for fact in memory_data["facts"]:
        if merge:
            cursor.execute("""
                INSERT OR REPLACE INTO user_facts
                (device_id, fact_type, fact_value, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fact.get("device_id"),
                fact.get("fact_type"),
                fact.get("fact_value"),
                fact.get("confidence", 1.0),
                fact.get("created_at"),
                fact.get("updated_at")
            ))

    conn.commit()
    conn.close()

    print("✅ Đã nhập ký ức thành công!")
    print("   Mimi đã nhớ lại tất cả!")


def show_stats():
    """Hiển thị thống kê ký ức"""
    print("📊 Thống kê ký ức của Mimi\n")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Đếm profiles
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        profile_count = cursor.fetchone()[0]

        # Đếm conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]

        # Đếm facts
        cursor.execute("SELECT COUNT(*) FROM user_facts")
        fact_count = cursor.fetchone()[0]

        # Lấy thông tin chi tiết
        cursor.execute("SELECT child_name, last_seen FROM user_profiles")
        profiles = cursor.fetchall()

        print(f"👤 Số bé đã nói chuyện: {profile_count}")
        print(f"💬 Tổng số tin nhắn: {conv_count}")
        print(f"🧠 Số điều Mimi nhớ: {fact_count}")
        print()

        if profiles:
            print("📋 Danh sách bé:")
            for name, last_seen in profiles:
                print(f"   - {name or 'Chưa biết tên'} (lần cuối: {last_seen or 'N/A'})")

        # Lấy một số facts
        cursor.execute("SELECT fact_type, fact_value FROM user_facts LIMIT 10")
        facts = cursor.fetchall()

        if facts:
            print("\n🧠 Một số điều Mimi nhớ:")
            for fact_type, fact_value in facts:
                print(f"   - {fact_type}: {fact_value}")

        conn.close()

    except Exception as e:
        print(f"❌ Lỗi: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Công cụ sao lưu và khôi phục ký ức của Mimi"
    )

    subparsers = parser.add_subparsers(dest="command", help="Lệnh")

    # Export command
    export_parser = subparsers.add_parser("export", help="Xuất ký ức ra file")
    export_parser.add_argument("-o", "--output", help="Đường dẫn file xuất")

    # Import command
    import_parser = subparsers.add_parser("import", help="Nhập ký ức từ file")
    import_parser.add_argument("file", help="File backup để nhập")
    import_parser.add_argument("--no-merge", action="store_true",
                               help="Không gộp, ghi đè hoàn toàn")

    # Stats command
    subparsers.add_parser("stats", help="Xem thống kê ký ức")

    args = parser.parse_args()

    if args.command == "export":
        export_memory(args.output)
    elif args.command == "import":
        import_memory(args.file, merge=not args.no_merge)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
