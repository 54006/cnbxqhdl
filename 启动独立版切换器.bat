@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动暴雪战网账号切换器（独立目录版）...
echo 如需管理员权限，请右键选择"以管理员身份运行"
"c:\Users\Administrator\Desktop\py\.venv\Scripts\python.exe" isolated_gui.py
pause
