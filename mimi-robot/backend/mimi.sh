#!/bin/bash
# Mimi Robot - Quick Start Script
# Sử dụng: ./mimi.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/src/main.py"
LOG_FILE="$SCRIPT_DIR/data/mimi.log"

cd "$SCRIPT_DIR/src"

case "$1" in
    start)
        echo "🚀 Khởi động Mimi..."
        python3 main.py
        sleep 1
        python3 main.py --status
        ;;
    stop)
        echo "🛑 Dừng Mimi..."
        python3 main.py --stop
        ;;
    restart)
        echo "🔄 Khởi động lại Mimi..."
        python3 main.py --stop
        sleep 1
        python3 main.py
        sleep 1
        python3 main.py --status
        ;;
    status)
        python3 main.py --status
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📝 Hiển thị log (Ctrl+C để thoát)..."
            tail -f "$LOG_FILE"
        else
            echo "❌ Chưa có file log"
        fi
        ;;
    foreground|fg)
        echo "🚀 Chạy Mimi ở chế độ foreground..."
        python3 main.py --foreground
        ;;
    *)
        echo "Mimi Robot - Backend Server"
        echo ""
        echo "Sử dụng: $0 {start|stop|restart|status|logs|foreground}"
        echo ""
        echo "  start      - Khởi động server (chạy ẩn)"
        echo "  stop       - Dừng server"
        echo "  restart    - Khởi động lại server"
        echo "  status     - Kiểm tra trạng thái"
        echo "  logs       - Xem log realtime"
        echo "  foreground - Chạy hiển thị log (debug)"
        ;;
esac
