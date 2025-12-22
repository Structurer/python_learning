import subprocess
import re
import pysrt
import os
import sys

def get_ffmpeg_path():
    """获取FFmpeg路径，虚拟机中若未配环境变量，取消注释填绝对路径"""
    # return r"C:\Program Files (x86)\ffmpeg-2025-12-18-git-78c75d546a-essentials_build\bin\ffmpeg.exe"
    return "ffmpeg"

def get_video_info(video_path, ffmpeg_path):
    """获取字幕轨的索引、格式、语言信息"""
    cmd = [ffmpeg_path, '-i', video_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    output = result.stderr
    sub_info = []
    pattern = re.compile(r'Stream #0:(\d+).*?Subtitle: (\w+).*?\((\w+)\)')
    matches = pattern.findall(output)
    for idx, fmt, lang in matches:
        sub_info.append({"index": idx, "format": fmt, "language": lang})
    return sub_info

def extract_subtitle(video_path, sub_index, sub_fmt, output_file, ffmpeg_path):
    """根据格式提取字幕，ASS输出.ass，SRT输出.srt"""
    if sub_fmt in ['ass', 'ssa']:
        output_file = output_file.replace('.srt', '.ass')
        codec = 'copy'
    elif sub_fmt in ['srt', 'subrip']:
        codec = 'copy'
    else:
        raise Exception(f"不支持的字幕格式：{sub_fmt}")

    cmd = [
        ffmpeg_path, '-i', video_path,
        '-map', f'0:{sub_index}',
        '-c:s', codec,
        output_file,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        raise Exception(f"提取轨道{sub_index}失败！日志：{result.stderr}")
    print(f"✅ 提取成功：{output_file}（格式：{sub_fmt}）")
    return output_file

def convert_ass_to_srt(ass_file, srt_file, ffmpeg_path):
    """ASS转SRT，方便拆分英文"""
    cmd = [
        ffmpeg_path, '-i', ass_file,
        '-c:s', 'srt',
        srt_file,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    if not os.path.exists(srt_file):
        raise Exception(f"ASS转SRT失败！日志：{result.stderr}")
    print(f"✅ ASS转SRT成功：{srt_file}")
    return srt_file

def split_bilingual_to_english(bilingual_srt, output_en_srt):
    """拆分双语SRT为纯英文SRT（含样式标签的非标准格式）"""
    try:
        subs = pysrt.open(bilingual_srt, encoding='utf-8')
    except UnicodeDecodeError:
        subs = pysrt.open(bilingual_srt, encoding='gbk')

    en_subs = pysrt.SubRipFile()
    empty_count = 0
    for sub in subs:
        lines = [line.strip() for line in sub.text.split('\n') if line.strip()]
        if len(lines) >= 2:
            en_text = lines[1].strip()
            if en_text:
                sub.text = en_text
                en_subs.append(sub)
            else:
                empty_count += 1
        else:
            empty_count += 1

    en_subs.save(output_en_srt, encoding='utf-8')
    print(f"✅ 拆分纯英文成功：{output_en_srt}（跳过{empty_count}个无英文的条目）")
    return output_en_srt

def clean_non_standard_srt(input_srt_path, output_srt_path):
    """将非标准SRT转换为标准SRT，清理样式标签"""
    tag_pattern = re.compile(r'<[^>]+>')  # 匹配所有HTML/ASS样式标签
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')  # 匹配SRT时间轴
    number_pattern = re.compile(r'^\d+$')  # 匹配SRT序号

    # 读取原文件
    try:
        with open(input_srt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(input_srt_path, 'r', encoding='gbk') as f:
            lines = f.readlines()

    # 清理并重组内容
    cleaned_lines = []
    current_sub = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if current_sub:
                cleaned_lines.extend(current_sub)
                cleaned_lines.append('\n')
                current_sub = []
            continue
        if number_pattern.match(line_stripped):
            current_sub.append(f"{line_stripped}\n")
        elif time_pattern.match(line_stripped):
            current_sub.append(f"{line_stripped}\n")
        else:
            clean_text = tag_pattern.sub('', line_stripped).strip()
            if clean_text:
                current_sub.append(f"{clean_text}\n")

    # 处理最后一个字幕块
    if current_sub:
        cleaned_lines.extend(current_sub)
        cleaned_lines.append('\n')

    # 写入标准SRT
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    print(f"✅ 非标准SRT转标准成功：{input_srt_path} → {output_srt_path}")
    return output_srt_path

def merge_subtitles_to_mkv(video_path, output_video, subtitle_files, ffmpeg_path):
    """修复语法错误：用字符串拼接替代f-string的流指定符，避免FFmpeg解析失败"""
    cmd = [ffmpeg_path, '-i', video_path, '-y']
    # 添加所有字幕文件作为输入
    for sub_file in subtitle_files:
        cmd.extend(['-i', sub_file])
    
    # 映射视频和音频流
    cmd.extend(['-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'copy'])
    
    # 逐个映射字幕轨
    subtitle_names = ["原始中英双语(ASS)", "纯中文(SRT)", "纯英文(SRT)"]
    for i in range(len(subtitle_files)):
        sub_input_idx = i + 1
        sub_track_idx = str(i)
        sub_name = subtitle_names[i] if i < len(subtitle_names) else f"字幕轨{int(sub_track_idx)+1}"
        sub_file = subtitle_files[i]

        # 拼接字幕轨相关参数
        if sub_file.endswith('.ass'):
            cmd.extend([
                '-map', f'{sub_input_idx}:s:0',
                '-c:s:' + sub_track_idx, 'copy',
                '-disposition:s:' + sub_track_idx, 'default',
                '-metadata:s:s:' + sub_track_idx, f'title={sub_name}',
                '-metadata:s:s:' + sub_track_idx, 'encoder=ass'
            ])
        else:
            cmd.extend([
                '-map', f'{sub_input_idx}:s:0',
                '-c:s:' + sub_track_idx, 'srt',
                '-metadata:s:s:' + sub_track_idx, f'title={sub_name}'
            ])
    
    # 添加输出文件
    cmd.append(output_video)

    # 执行命令并验证
    result = subprocess.run(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore'
    )
    if not os.path.exists(output_video):
        print(f"❌ FFmpeg错误日志：{result.stderr}")
        raise Exception("合并失败：未生成输出文件")
    if os.path.getsize(output_video) < 1024 * 1024:
        os.remove(output_video)
        print(f"❌ FFmpeg错误日志：{result.stderr}")
        raise Exception("合并失败：文件体积过小，未包含视频/音频流")
    
    print(f"✅ 新视频生成成功：{output_video}（大小：{os.path.getsize(output_video)//1024//1024}MB）")
    return output_video

if __name__ == "__main__":
    # 配置区：你的视频文件名
    VIDEO_FILE = "Shameless.US.S10E09.2019.1080p.WEB_DL.x265.10bit.AC3￡cXcY@FRDS.mkv"
    FFMPEG_PATH = get_ffmpeg_path()
    VIDEO_PATH = os.path.join(os.getcwd(), VIDEO_FILE)

    # 检查视频文件
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ 未找到视频：{VIDEO_PATH}")
        sys.exit(1)

    # 1. 获取字幕轨信息
    sub_info_list = get_video_info(VIDEO_PATH, FFMPEG_PATH)
    if not sub_info_list:
        print("❌ 未检测到字幕轨！")
        sys.exit(1)
    print("📌 检测到的字幕轨：")
    for sub in sub_info_list:
        print(f"   轨道{sub['index']} | 格式：{sub['format']} | 语言：{sub['language']}")

    # 2. 提取ASS双语轨（轨道2）和SRT中文轨（轨道3）
    ass_sub_index = "2"
    srt_sub_index = "3"
    ass_bilingual_file = "bilingual_sub.ass"
    srt_chinese_file = "chinese_only.srt"
    extract_subtitle(VIDEO_PATH, ass_sub_index, "ass", ass_bilingual_file, FFMPEG_PATH)
    extract_subtitle(VIDEO_PATH, srt_sub_index, "srt", srt_chinese_file, FFMPEG_PATH)

    # 3. ASS转SRT并拆分纯英文（非标准格式）
    bilingual_srt = "bilingual_sub.srt"
    convert_ass_to_srt(ass_bilingual_file, bilingual_srt, FFMPEG_PATH)
    raw_english_srt = "english_only_raw.srt"  # 拆分出的非标准英文SRT
    split_bilingual_to_english(bilingual_srt, raw_english_srt)

    # 4. 清理非标准英文SRT为标准格式
    cleaned_english_srt = "english_only.srt"  # 最终合并用的标准英文SRT
    clean_non_standard_srt(raw_english_srt, cleaned_english_srt)

    # 5. 合并三个字幕文件（ASS+纯中文SRT+标准英文SRT）回MKV，保留ASS样式
    subtitle_files_to_merge = [ass_bilingual_file, srt_chinese_file, cleaned_english_srt]
    output_video = f"final_video_with_3_subs_{os.path.basename(VIDEO_FILE)}"
    merge_subtitles_to_mkv(VIDEO_PATH, output_video, subtitle_files_to_merge, FFMPEG_PATH)

    # 输出生成文件列表
    print("\n📂 最终生成的所有文件：")
    all_files = [ass_bilingual_file, srt_chinese_file, bilingual_srt, raw_english_srt, cleaned_english_srt, output_video]
    for f in all_files:
        if os.path.exists(f):
            print(f"   - {f}")

    print("\n🎉 全部操作完成！新视频包含3个字幕轨，英文轨为标准SRT格式无样式标签")