@echo off
chcp 65001 >nul

setlocal

:: 创建虚拟环境
echo 正在创建虚拟环境...
python -m venv venv

:: 检查是否成功创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境失败，请确认 Python 是否已正确安装。
    exit /b 1
)

:: 安装依赖
echo 正在安装依赖...
call venv\Scripts\activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt6 numpy scipy pydub pyqtgraph

:: 检查是否成功安装依赖
if errorlevel 1 (
    echo 依赖安装失败，请检查网络连接。
    exit /b 1
)

echo 安装完成！虚拟环境已创建并配置完成。
endlocal
pause