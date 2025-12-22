import re
import os

def clean_srt(input_srt_path, output_srt_path):
    """
    将非标准SRT转换为标准SRT
    :param input_srt_path: 输入的非标准SRT文件路径
    :param output_srt_path: 输出的标准SRT文件路径
    """
    # 1. 正则表达式定义
    tag_pattern = re.compile(r'<[^>]+>')  # 匹配所有HTML/ASS样式标签
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')  # 匹配SRT时间轴
    number_pattern = re.compile(r'^\d+$')  # 匹配SRT序号

    # 2. 读取原文件内容
    try:
        with open(input_srt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # 若utf-8解码失败，尝试gbk编码（中文Windows常见）
        with open(input_srt_path, 'r', encoding='gbk') as f:
            lines = f.readlines()

    # 3. 清理并重组内容
    cleaned_lines = []
    current_sub = []  # 存储当前字幕块（序号、时间轴、文本）
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            # 空行：表示一个字幕块结束，写入并重置
            if current_sub:
                cleaned_lines.extend(current_sub)
                cleaned_lines.append('\n')  # 标准SRT字幕块间用空行分隔
                current_sub = []
            continue

        # 匹配序号行
        if number_pattern.match(line_stripped):
            current_sub.append(f"{line_stripped}\n")
        # 匹配时间轴行
        elif time_pattern.match(line_stripped):
            current_sub.append(f"{line_stripped}\n")
        # 字幕文本行：清理标签并保留纯文本
        else:
            clean_text = tag_pattern.sub('', line_stripped).strip()
            if clean_text:  # 仅保留非空文本
                current_sub.append(f"{clean_text}\n")

    # 处理最后一个字幕块（文件末尾无空行的情况）
    if current_sub:
        cleaned_lines.extend(current_sub)
        cleaned_lines.append('\n')

    # 4. 写入标准SRT文件
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

    print(f"✅ 转换完成：{input_srt_path} → {output_srt_path}")

def batch_clean_srt(input_dir):
    """
    批量处理指定目录下的所有SRT文件
    :param input_dir: 包含非标准SRT的目录路径
    """
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.srt'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(input_dir, f"cleaned_{filename}")
            clean_srt(input_path, output_path)

if __name__ == "__main__":
    # 方式1：处理单个文件
    input_file = "english_only.srt"  # 你的非标准SRT文件路径
    output_file = "cleaned_english_only.srt"  # 输出的标准SRT路径
    clean_srt(input_file, output_file)

    # 方式2：批量处理目录下所有SRT（取消注释启用）
    # input_directory = "./"  # 当前目录
    # batch_clean_srt(input_directory)