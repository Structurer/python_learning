import subprocess
import re
import pysrt
import os
import sys

def get_ffmpeg_path():
    return "ffmpeg"  # 虚拟机中若未配环境变量，填FFmpeg绝对路径

def get_video_info(video_path, ffmpeg_path):
    cmd = [ffmpeg_path, '-i', video_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    output = result.stderr
    sub_info = []
    # 匹配字幕轨：同时提取索引、格式、语言
    pattern = re.compile(r'Stream #0:(\d+).*?Subtitle: (\w+).*?\((\w+)\)')
    matches = pattern.findall(output)
    for idx, fmt, lang in matches:
        sub_info.append({"index": idx, "format": fmt, "language": lang})
    return sub_info

def extract_subtitle(video_path, sub_index, sub_fmt, output_file, ffmpeg_path):
    """根据字幕格式正确提取，ASS输出为.ass，SRT输出为.srt"""
    # 确定输出扩展名和编码方式
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
    
    # 检查文件是否有效
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        raise Exception(f"提取轨道{sub_index}失败！日志：{result.stderr}")
    print(f"✅ 提取成功：{output_file}（格式：{sub_fmt}）")
    return output_file

def convert_ass_to_srt(ass_file, srt_file):
    """将ASS字幕转换为SRT格式（方便拆分英文）"""
    cmd = [
        get_ffmpeg_path(), '-i', ass_file,
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
    """拆分双语字幕（第一行中文、第二行英文）为纯英文"""
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

if __name__ == "__main__":
    # 配置区：你的视频文件名
    VIDEO_FILE = "Shameless.Hall.of.Shame.E01.2021.1080p.WEB-DL.x265.10bit.AC3￡cXcY@FRDS.mkv"
    FFMPEG_PATH = get_ffmpeg_path()
    VIDEO_PATH = os.path.join(os.getcwd(), VIDEO_FILE)

    # 检查视频文件
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ 未找到视频：{VIDEO_PATH}")
        sys.exit(1)

    # 1. 获取字幕轨详细信息
    sub_info_list = get_video_info(VIDEO_PATH, FFMPEG_PATH)
    if not sub_info_list:
        print("❌ 未检测到字幕轨！")
        sys.exit(1)
    print("📌 检测到的字幕轨：")
    for sub in sub_info_list:
        print(f"   轨道{sub['index']} | 格式：{sub['format']} | 语言：{sub['language']}")

    # 2. 提取ASS双语轨（轨道2）和SRT中文轨（轨道3）
    ass_sub_index = "2"  # ASS格式的双语轨
    srt_sub_index = "3"  # SRT格式的中文轨
    ass_file = "bilingual_sub.ass"
    srt_chinese_file = "chinese_only.srt"

    # 提取ASS双语轨
    extract_subtitle(VIDEO_PATH, ass_sub_index, "ass", ass_file, FFMPEG_PATH)
    # 提取SRT中文轨
    extract_subtitle(VIDEO_PATH, srt_sub_index, "srt", srt_chinese_file, FFMPEG_PATH)

    # 3. 将ASS双语轨转换为SRT，再拆分纯英文
    bilingual_srt = "bilingual_sub.srt"
    convert_ass_to_srt(ass_file, bilingual_srt)
    english_only_srt = "english_only.srt"
    split_bilingual_to_english(bilingual_srt, english_only_srt)

    # 输出生成的文件
    print("\n📂 最终生成的文件：")
    for f in [ass_file, srt_chinese_file, bilingual_srt, english_only_srt]:
        if os.path.exists(f):
            print(f"   - {f}")

    print("\n🎉 操作完成！english_only.srt为拆分后的纯英文字幕，chinese_only.srt为纯中文字幕")