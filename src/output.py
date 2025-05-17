import os
import json
import shutil
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import re
from collections import Counter

def merge_text_from_list(file_path):
    """解析.list文件，合并成一个文本并返回"""
    merged_text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                text = line.split('|')[-1]
                if text:
                    merged_text += text
    except FileNotFoundError:
        print(f"[错误] 文件 {file_path} 未找到")
        return ""
    except Exception as e:
        print(f"[错误] 读取文件时出错: {e}")
        return ""
    return merged_text

def string_stats(text):
    # 总字符数
    total_chars = len(text)
    
    # 不重复字符数
    unique_chars = len(set(text))
    
    # 字符频率统计（从多到少排列）
    char_counter = Counter(text)
    char_freq = dict(char_counter.most_common())
    
    # 汉字相关统计
    # 匹配所有中文字符（包括基本汉字和扩展汉字区）
    hanzi_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]', text)
    total_hanzi = len(hanzi_chars)
    unique_hanzi = len(set(hanzi_chars))
    hanzi_coverage = unique_hanzi / 21886 # GBK收录21886个汉字，含简体、繁体及部分异体字
    
    # 中文数字覆盖率
    chinese_digits = "零一二三四五六七八九十百千万亿兆"
    found_digits = [c for c in hanzi_chars if c in chinese_digits]
    unique_found_digits = len(set(found_digits))
    digit_coverage = unique_found_digits / len(chinese_digits) if len(chinese_digits) > 0 else 0.0
    
    # 其他统计信息
    # 统计空格数
    space_count = text.count(' ')
    
    # 统计数字数（阿拉伯数字）
    digit_count = sum(c.isdigit() for c in text)
    
    # 统计标点符号数（简单统计常见中英文标点）
    punctuation = re.findall(r'[，。！？、；："\'‘’“”《》【】（）〔〕…—~`!@#$%^&*()_+\-=\[\]{};:\\|,.<>/?]', text)
    punctuation_count = len(punctuation)
    
    # 统计字母数
    letter_count = sum(c.isalpha() for c in text if not re.match(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]', c))
    
    # 构建结果字典
    result = {
        '总字符数': total_chars,
        '不重复字符数': unique_chars,
        '字符频率': char_freq,
        '总汉字数': total_hanzi,
        '不重复汉字数': unique_hanzi,
        'GBK汉字覆盖率': f"{round(hanzi_coverage, 4) * 100}%",
        '中文数字覆盖率': f"{round(digit_coverage, 4) * 100}%",
        '空格数': space_count,
        '阿拉伯数字数': digit_count,
        '字母数': letter_count,
        '标点符号数': punctuation_count,
    }
    
    return result

def increase_audio_volume(directory, volume_boost=2, silence_thresh=-40):
    """
    提高指定目录下所有 .wav 文件的音频音量，但不增强低于 silence_thresh 的静音部分。
    
    参数:
        directory (str): 包含 .wav 文件的目录路径
        volume_boost (int 或 float): 提高音量的 dB 值，默认为 2 dB
        silence_thresh (int): 静音阈值(dBFS)，默认-40dB，低于此值的部分不会被增强
    """
    # 设置 ffmpeg 路径（如果 ffmpeg.exe 在当前目录）
    AudioSegment.converter = os.path.abspath("src/ffmpeg.exe")

    # 遍历目录下的所有文件
    for filename in os.listdir(directory):
        if filename.lower().endswith('.wav'):
            filepath = os.path.join(directory, filename)

            try:
                # 加载音频文件
                audio = AudioSegment.from_wav(filepath)

                # 检测非静音部分
                nonsilent_parts = detect_nonsilent(
                    audio,
                    min_silence_len=50,
                    silence_thresh=silence_thresh,
                )

                # 创建一个新的空音频段用于拼接
                boosted_audio = AudioSegment.silent(duration=0)

                # 上一个片段的结束位置
                prev_end = 0

                # 只对非静音部分进行音量增强
                for start, end in nonsilent_parts:
                    # 添加当前静音部分（从上一个片段结束到当前片段开始）
                    silent_segment = audio[prev_end:start]
                    boosted_audio += silent_segment

                    # 增强当前非静音部分的音量
                    nonsilent_segment = audio[start:end] + volume_boost
                    boosted_audio += nonsilent_segment

                    prev_end = end

                # 添加最后一段静音之后的部分
                boosted_audio += audio[prev_end:]

                # 导出并覆盖原文件
                boosted_audio.export(filepath, format="wav")
                print(f"音量提升成功: {filename}")

            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

def remove_silence_from_audio_files(directory, silence_thresh=-40, keep_silence=200):
    """
    读取指定目录下所有.wav文件，去掉其音频收尾的静音部分，然后以原文件名保存。
    
    参数:
        directory (str): 包含.wav文件的目录路径
        silence_thresh (int): 静音阈值(dBFS)，默认-40dB
        keep_silence (int): 音频前后保留的静音时长(毫秒)，默认200ms(0.2秒)
    """
    # 设置 ffmpeg 路径（如果 ffmpeg.exe 在当前目录）
    AudioSegment.converter = os.path.abspath("src/ffmpeg.exe")
    
    # 确保 keep_silence 是毫秒为单位
    if isinstance(keep_silence, float):
        keep_silence = int(keep_silence * 1000)  # 转换秒到毫秒
    
    # 遍历目录下的所有文件
    for filename in os.listdir(directory):
        if filename.lower().endswith('.wav'):
            filepath = os.path.join(directory, filename)
            
            try:
                # 加载音频文件
                audio = AudioSegment.from_wav(filepath)
                
                # 检测非静音部分
                nonsilent_parts = detect_nonsilent(
                    audio,
                    min_silence_len=50,
                    silence_thresh=silence_thresh,
                )
                
                if not nonsilent_parts:
                    print(f"警告: {filename} 可能是全静音，跳过处理")
                    continue
                
                # 计算裁剪范围（前后保留 keep_silence 毫秒）
                start = max(0, nonsilent_parts[0][0] - keep_silence)
                end = min(len(audio), nonsilent_parts[-1][1] + keep_silence)
                
                # 裁剪并保存
                processed_audio = audio[start:end]
                processed_audio.export(filepath, format="wav")
                print(f"首尾静音去除成功: {filename}")
                
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

def save_string_to_file(content, file_path, overwrite=True):
    """将字符串保存为文本文件，可选是否覆盖，并确保父目录存在"""
    if not overwrite and Path(file_path).exists():
        return False
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    Path(file_path).write_text(content, encoding='utf-8')
    return True

def copy_file(src, dst, overwrite=True):
    """复制文件从src到dst，可选是否覆盖"""
    if not overwrite and Path(dst).exists():
        return False
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True

def read_json(file_path):
    """读取JSON文件为字典"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path, indent=4):
    """将字典保存为JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def find_wav_files(directory):
    """递归查找目录下的所有WAV文件"""
    return [f for _, _, files in os.walk(directory) 
            for f in files if f.lower().endswith('.wav')]

def merge_wav_files(directory, output_file, max_duration=9999999):
    """
    遍历指定目录下的所有 .wav 文件，并将其合并为一个 .wav 文件并导出，支持设置最大音频时长。

    参数:
        directory (str): 包含 .wav 文件的目录路径
        output_file (str): 合并后的输出文件路径（包含文件名）
        max_duration (int 或 float): 最大音频时长(秒)，默认为 9999999 秒
    """
    # 创建一个空音频段用于拼接
    combined_audio = AudioSegment.silent(duration=0)

    # 转换最大时长为毫秒（AudioSegment 使用毫秒作为时间单位）
    max_duration_ms = max_duration * 1000

    # 遍历目录下的所有文件
    for filename in os.listdir(directory):
        if filename.lower().endswith('.wav'):
            filepath = os.path.join(directory, filename)
            try:
                # 加载音频文件
                audio = AudioSegment.from_wav(filepath)

                # 检查当前合并后的音频是否超过最大时长
                if len(combined_audio) + len(audio) > max_duration_ms:
                    print(f"警告: 已达到最大时长 {max_duration} 秒，停止合并")
                    break

                # 合并音频
                combined_audio += audio
                print(f"已合并: {filename}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

    # 确保输出目录存在
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # 导出合并后的音频文件
    combined_audio.export(output_file, format="wav")
    print(f"所有音频已合并并保存至: {output_file}")

def main(project_name='default', json_file='corpus/zh_corpus_v1.json', wav_dir='wav', silence_thresh=-40, keep_silence=500, volume_boost=0):
    """
    主流程函数，用于整理音频文件、生成列表并处理音频。
    
    参数:
        project_name (str): 项目名称，默认为 'default'
        json_file (str): 存储句子内容的 JSON 文件路径，默认为 'corpus/zh_corpus_v1.json'
        wav_dir (str): WAV 文件所在目录，默认为 'wav'
        silence_thresh (int): 静音阈值(dBFS)，默认-40dB
        keep_silence (int): 音频前后保留的静音时长(毫秒)，默认500ms
        volume_boost (int 或 float): 提高音量的 dB 值，默认为 0 dB
    """
    projects_dir = f'projects/{project_name}'
    
    # 读取数据
    sentences = read_json(json_file)
    print("句子数:", len(sentences))
    
    # 查找WAV文件
    wav_files = find_wav_files(wav_dir)
    print("WAV文件数:", len(wav_files))
    print("完成率:", f"{len(wav_files)/len(sentences)*100:.2f}%")

    # 整理数据到项目文件
    slicer_opt_path = f'{projects_dir}/gptsovits_dataset/slicer_opt'
    list_path = f'{projects_dir}/gptsovits_dataset/asr_opt/slicer_opt.list'
    list_data = ""
    n = 0
    for wav_file in wav_files:
        n += 1
        word = wav_file.split('.wav')[0]
        wav_path = f"{wav_dir}/{wav_file}"
        copy_path = f"{slicer_opt_path}/{wav_file}"
        copy_file(wav_path, copy_path)
        print(f"({n}/{len(wav_files)}) {wav_path} -> {copy_path}")
        if word in sentences:
            list_data += f"output\slicer_opt\{wav_file}|slicer_opt|ZH|{sentences[word]}\n"
    
    save_string_to_file(list_data, list_path)
    print("LIST文件位置:", list_path)

    # 删除音频前后空白
    remove_silence_from_audio_files(slicer_opt_path, silence_thresh=silence_thresh, keep_silence=keep_silence)

    # 调高音频音量
    if volume_boost > 0:
        increase_audio_volume(slicer_opt_path, volume_boost=volume_boost)

    # 合并音频
    merge_wav_files(slicer_opt_path, f"{projects_dir}/all.wav")
    merge_wav_files(slicer_opt_path, f"{projects_dir}/2min.wav", 120)

    # CosyVoice数据集
    cosyvoice_path = f'{projects_dir}/cosyvoice_dataset/libritts/LibriTTS'
    tts_text_path = f'{projects_dir}/cosyvoice_dataset/tts_text.json'
    cosyvoice_test_path = f'{cosyvoice_path}/test-clean/{project_name}/all'
    cosyvoice_dev_path = f'{cosyvoice_path}/dev-clean/{project_name}/all'
    cosyvoice_train_path = f'{cosyvoice_path}/train-clean-100/{project_name}/all'
    wav_files = find_wav_files(slicer_opt_path)
    n = 0
    for wav_file in wav_files:
        n += 1
        print(f"构建CosyVoice数据集({n}/{len(wav_files)})")
        word = wav_file.split('.wav')[0]
        if word not in sentences:
            continue
        wav_name = f"{project_name}_{word}"
        wav_path = f"{slicer_opt_path}/{wav_file}"
        copy_path = f"{cosyvoice_train_path}/{wav_name}.wav"
        copy_file(wav_path, copy_path)
        text_path = f"{cosyvoice_train_path}/{wav_name}.normalized.txt"
        save_string_to_file(sentences[word], text_path)
        if n <= 5:
            if n == 1:
                tts_text = {}
                tts_text[wav_name] = [sentences[word]]
                save_json(tts_text, tts_text_path)
            copy_path = f"{cosyvoice_test_path}/{wav_name}.wav"
            copy_file(wav_path, copy_path)
            text_path = f"{cosyvoice_test_path}/{wav_name}.normalized.txt"
            save_string_to_file(sentences[word], text_path)
            copy_path = f"{cosyvoice_dev_path}/{wav_name}.wav"
            copy_file(wav_path, copy_path)
            text_path = f"{cosyvoice_dev_path}/{wav_name}.normalized.txt"
            save_string_to_file(sentences[word], text_path)
        
    output_info = string_stats(merge_text_from_list(list_path))
    output_info["项目名称"] = project_name
    output_info["项目目录"] = projects_dir
    output_info["录制音频数"] = len(wav_files)
    output_info["完成率"] = f"{len(wav_files)/len(sentences)*100:.2f}%"
    return output_info

if __name__ == '__main__':
    main()