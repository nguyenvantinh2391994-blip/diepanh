@echo off
chcp 65001 >nul
title Mimi Robot Server

echo.
echo  ╔══════════════════════════════════════╗
echo  ║     🧸 MIMI ROBOT - BACKEND SERVER   ║
echo  ╚══════════════════════════════════════╝
echo.

:: Lấy đường dẫn thư mục hiện tại
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set BACKEND_DIR=%PROJECT_DIR%\backend

:: Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Không tìm thấy Python!
    echo    Tải từ: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Kiểm tra Ollama
echo 🔍 Kiểm tra Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ollama chưa chạy!
    echo    Hãy mở Ollama trước khi chạy server.
    echo.
    echo    Nếu chưa cài Ollama:
    echo    1. Tải từ: https://ollama.ai/download
    echo    2. Cài đặt và mở Ollama
    echo    3. Chạy: ollama pull qwen2.5:7b
    echo.
    pause
    exit /b 1
)
echo ✅ Ollama đang chạy!

:: Tạo virtual environment nếu chưa có
if not exist "%BACKEND_DIR%\venv" (
    echo 📦 Tạo môi trường Python...
    python -m venv "%BACKEND_DIR%\venv"
)

:: Kích hoạt virtual environment
call "%BACKEND_DIR%\venv\Scripts\activate.bat"

:: Cài đặt dependencies nếu chưa có
if not exist "%BACKEND_DIR%\venv\installed.flag" (
    echo 📦 Cài đặt thư viện cần thiết...
    pip install -r "%BACKEND_DIR%\requirements.txt"
    pip install edge-tts aiohttp
    echo. > "%BACKEND_DIR%\venv\installed.flag"
)

:: Tạo file .env nếu chưa có
if not exist "%BACKEND_DIR%\.env" (
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo ✅ Đã tạo file .env
)

:: Chạy server
echo.
echo 🚀 Khởi động Mimi Server...
echo.
echo    URL: http://localhost:8080
echo    WebSocket: ws://localhost:8080/ws
echo.
echo    Nhấn Ctrl+C để dừng server
echo.

cd "%BACKEND_DIR%\src"
python main.py

pause
