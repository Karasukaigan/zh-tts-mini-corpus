@echo off
chcp 65001 >nul

setlocal

:: 检查是否存在虚拟环境
if not exist "venv" (
    echo 虚拟环境不存在，请先运行“0.安装依赖.cmd”安装依赖。
    exit /b 1
)

:: 进入虚拟环境并启动 ui.py
echo 正在启动音频录制工具...
call venv\Scripts\activate
python ui.py

:: 检查是否成功启动
if errorlevel 1 (
    echo 启动失败，请检查 ui.py 或依赖是否完整。
    exit /b 1
)

echo 已退出音频录制工具。
endlocal