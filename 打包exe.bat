@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在打包 国服战网账号切换器...
echo.

REM 激活虚拟环境并安装pyinstaller
call "c:\Users\Administrator\Desktop\py\.venv\Scripts\activate.bat"

REM 检查pyinstaller是否安装
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

REM 使用spec文件打包
echo 开始打包...
pyinstaller build.spec --clean

echo.
echo 打包完成！
echo exe文件位置: dist\国服战网账号切换.exe
echo.
pause
