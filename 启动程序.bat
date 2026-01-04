@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动暴雪战网账号管理器...
python main.py
pause
