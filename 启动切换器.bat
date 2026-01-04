@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动暴雪战网账号切换器...
"c:\Users\Administrator\Desktop\py\.venv\Scripts\python.exe" switcher_gui.py
pause
