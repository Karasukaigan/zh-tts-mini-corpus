import json
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
import os
import re

def make_valid_filename(filename: str) -> str:
    """
    将任意字符串转换为合法的文件名
    
    参数:
        filename (str): 原始文件名
        
    返回:
        str: 合法的文件名
    """
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    valid_name = re.sub(invalid_chars, '_', filename)
    base_name = valid_name.split('.')[0].upper()
    if base_name in reserved_names:
        valid_name = '_' + valid_name
    max_length = 255
    if len(valid_name) > max_length:
        if '.' in valid_name:
            name, ext = valid_name.rsplit('.', 1)
            valid_name = name[:max_length - len(ext) - 1] + '.' + ext
        else:
            valid_name = valid_name[:max_length]
    valid_name = valid_name.strip('. ')
    if not valid_name:
        valid_name = 'default'
    return valid_name

def load_sentences(file_path="zh_corpus_v1.json"):
    """
    从指定路径加载 JSON 格式的句子数据。
    
    参数:
        file_path (str): 要加载的 JSON 文件的路径，默认值为 "zh_corpus_v1.json"
        
    返回值:
        dict: 如果文件成功加载，则返回解析后的字典对象；
              如果文件未找到或格式不正确，则返回空字典 {}
              
    异常处理:
        - FileNotFoundError: 打印错误信息并返回空字典
        - JSONDecodeError: 打印错误信息并返回空字典
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[错误] 未找到 {file_path} ，无法加载句子数据")
        return {}
    except json.JSONDecodeError:
        print("[错误] {file_path} 文件格式不正确，无法加载句子数据")
        return {}

def open_directory(directory_path):
    """
    打开指定的目录，如果路径中的父目录不存在，则递归创建它们。

    参数:
        directory_path (str): 要打开的目录路径

    返回值:
        bool: 如果成功创建并打开了目录路径，返回 True；
              如果发生异常（如权限不足等），打印错误信息并返回 False

    异常处理:
        - 捕获通用异常 Exception，并打印具体的错误信息
    """
    try:
        directory_path = os.path.abspath(directory_path)
        os.makedirs(directory_path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory_path))
        return True
    except Exception as e:
        print(f"[错误] 无法创建或打开目录: {e}")
        return False