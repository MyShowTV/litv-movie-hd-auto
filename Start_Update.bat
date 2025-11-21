@echo off
title LITV Auto Update Service
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo 🚀 正在啟動 LITV 自動更新系統...
echo 📂 執行檔案: LITV_TWTV_AutoUpdate.py
echo ==========================================

:: ==============================
:: 嘗試使用 venv (虛擬環境) 的 Python
:: ==============================
if exist "venv\Scripts\python.exe" (
    echo 🐍 偵測到虛擬環境，使用 venv Python...
    "venv\Scripts\python.exe" "LITV_TWTV_AutoUpdate.py"
) else (
    echo 🐍 未偵測到 venv，使用系統 Python...
    python "LITV_TWTV_AutoUpdate.py"
)

echo.
echo ⚠️ 程式已停止運行。
pause