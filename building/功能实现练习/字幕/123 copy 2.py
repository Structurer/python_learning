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
    """拆分双语SRT为纯英文SRT"""
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

def merge_subtitles_to_mkv(video_path, output_video, subtitle_files, ffmpeg_path):
    """修复流映射：确保包含视频、音频、字幕所有流"""
    # 1. 构建FFmpeg命令，先输入原视频，再输入所有字幕文件
    cmd = [
        ffmpeg_path,
        '-i', video_path,  # 输入1：原视频（包含视频流、音频流）
        '-y'  # 覆盖已存在的输出文件
    ]
    # 添加所有字幕文件作为额外输入
    for sub_file in subtitle_files:
        cmd.extend(['-i', sub_file])
    
    # 2. 显式映射原视频的视频流和音频流（取第一个视频流、第一个音频流）
    cmd.extend([
        '-map', '0:v:0',  # 映射输入0（原视频）的第一个视频流
        '-map', '0:a:0',  # 映射输入0（原视频）的第一个音频流
        '-c:v', 'copy',   # 视频流原样复制，不重新编码
        '-c:a', 'copy'    # 音频流原样复制，不重新编码
    ])
    
    # 3. 映射每个字幕文件的字幕流，并添加名称标识
    subtitle_names = ["原始中英双语(ASS)", "纯中文(SRT)", "纯英文(SRT)"]
    for i in range(len(subtitle_files)):
        sub_input_idx = i + 1  # 输入0是原视频，1/2/3是字幕文件
        sub_track_idx = i      # 新视频的字幕轨索引从0开始
        sub_name = subtitle_names[i] if i < len(subtitle_names) else f"字幕轨{sub_track_idx+1}"
        
        # 映射字幕流 + 设置编码 + 添加轨道名称
        cmd.extend([
            '-map', f'{sub_input_idx}:s:0',  # 取字幕文件的第一个字幕流
            '-c:s', 'copy' if subtitle_files[i].endswith('.ass') else 'srt',
            f'-metadata:s:s:{sub_track_idx}', f'title="{sub_name}"'
        ])
    
    # 4. 指定输出文件（强制MKV格式，确保兼容多字幕轨）
    cmd.append(output_video)

    # 执行命令并捕获详细日志
    result = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='utf-8',
        errors='ignore'
    )
    
    # 验证输出文件是否为有效视频
    if not os.path.exists(output_video):
        print(f"❌ FFmpeg执行日志：{result.stderr}")
        raise Exception("合并失败：未生成输出文件")
    if os.path.getsize(output_video) < 1024 * 1024:  # 小于1MB则判定为无效视频
        os.remove(output_video)
        print(f"❌ FFmpeg执行日志：{result.stderr}")
        raise Exception("合并失败：生成的文件体积过小，未包含视频/音频流")
    
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

    # 3. ASS转SRT并拆分纯英文
    bilingual_srt = "bilingual_sub.srt"
    convert_ass_to_srt(ass_bilingual_file, bilingual_srt, FFMPEG_PATH)
    english_only_srt = "english_only.srt"
    split_bilingual_to_english(bilingual_srt, english_only_srt)

    # 4. 合并三个字幕文件回MKV视频
    subtitle_files_to_merge = [ass_bilingual_file, srt_chinese_file, english_only_srt]
    output_video = f"final_video_with_3_subs_{os.path.basename(VIDEO_FILE)}"
    merge_subtitles_to_mkv(VIDEO_PATH, output_video, subtitle_files_to_merge, FFMPEG_PATH)

    # 输出生成文件列表
    print("\n📂 最终生成的所有文件：")
    all_files = [ass_bilingual_file, srt_chinese_file, bilingual_srt, english_only_srt, output_video]
    for f in all_files:
        if os.path.exists(f):
            print(f"   - {f}")

    print("\n🎉 全部操作完成！新视频包含3个字幕轨，可在播放器中切换查看")