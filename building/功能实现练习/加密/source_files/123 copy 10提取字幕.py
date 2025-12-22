import subprocess
import re
import os
import gc

def get_ffmpeg_path():
    """获取FFmpeg路径（Debian系统默认已安装可直接调用）"""
    return "ffmpeg"

def get_all_subtitle_tracks(video_path, ffmpeg_path):
    """
    识别视频内所有字幕轨，区分ASS/SSA和SRT格式
    :param video_path: 视频文件路径
    :param ffmpeg_path: FFmpeg路径
    :return: list[dict] 字幕轨信息，含index/format/language
    """
    cmd = [ffmpeg_path, '-i', video_path]
    result = subprocess.run(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
        encoding='utf-8', errors='ignore'
    )
    output = result.stderr
    sub_tracks = []

    # 正则匹配字幕轨信息，精准识别ASS/SSA/SRT格式
    pattern = re.compile(
        r'Stream #0:(\d+)(?:\[.*?\])?.*?Subtitle: (\w+)(?:\s*\(\w+\))?.*?(?:\((\w+)\))?',
        re.IGNORECASE
    )
    matches = pattern.findall(output)

    for idx, fmt, lang in matches:
        fmt_lower = fmt.lower()
        # 统一格式标识，区分核心两类格式
        if fmt_lower in ["ass", "ssa"]:
            sub_format = "ass"
            suffix = "ass"
        elif fmt_lower in ["srt", "subrip"]:
            sub_format = "srt"
            suffix = "srt"
        else:
            sub_format = "unknown"
            suffix = "srt"  # 未知格式默认转SRT
        
        sub_tracks.append({
            "index": idx,
            "format": sub_format,
            "language": lang.lower() if lang else "unknown",
            "suffix": suffix
        })
    return sub_tracks

def extract_single_subtitle_track(video_path, sub_track, output_dir, ffmpeg_path):
    """
    无损提取单个字幕轨，按格式命名
    :param video_path: 视频路径
    :param sub_track: 字幕轨信息dict
    :param output_dir: 输出目录
    :param ffmpeg_path: FFmpeg路径
    :return: 提取的字幕文件路径
    """
    track_idx = sub_track["index"]
    track_format = sub_track["format"]
    track_suffix = sub_track["suffix"]
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    output_file = os.path.join(
        output_dir,
        f"{video_name}_track{track_idx}_{track_format}.{track_suffix}"
    )

    # FFmpeg提取命令：无损复制字幕流
    cmd = [
        ffmpeg_path, '-i', video_path,
        '-map', f'0:{track_idx}',  # 指定字幕轨索引
        '-c:s', 'copy',            # 无损复制，不转码
        '-y', output_file          # 覆盖已存在文件
    ]

    result = subprocess.run(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
        encoding='utf-8', errors='ignore'
    )

    # 校验提取结果
    if not os.path.exists(output_file) or os.path.getsize(output_file) < 10:
        raise Exception(f"字幕轨{track_idx}提取失败！FFmpeg日志：{result.stderr}")
    
    print(f"  ✅ 提取成功：{os.path.basename(output_file)}")
    return output_file

def process_single_video_subtitles(video_path, root_output_dir, ffmpeg_path):
    """
    处理单个视频：识别+提取所有字幕轨
    :param video_path: 输入视频路径
    :param root_output_dir: 根输出目录
    :param ffmpeg_path: FFmpeg路径
    """
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    # 为每个视频创建字幕专属文件夹
    sub_output_dir = os.path.join(root_output_dir, f"{video_name}_subtitle_tracks")
    if not os.path.exists(sub_output_dir):
        os.makedirs(sub_output_dir)

    try:
        print(f"\n📌 处理视频：{os.path.basename(video_path)}")
        # 1. 识别所有字幕轨
        sub_tracks = get_all_subtitle_tracks(video_path, ffmpeg_path)
        if not sub_tracks:
            print(f"  ❌ 未检测到任何字幕轨，跳过")
            return
        
        # 2. 输出识别结果，区分格式
        print(f"  📋 检测到 {len(sub_tracks)} 个字幕轨：")
        for track in sub_tracks:
            print(f"    - 轨道{track['index']} | 格式：{track['format']} | 语言：{track['language']}")
        
        # 3. 逐个提取字幕轨
        for track in sub_tracks:
            extract_single_subtitle_track(video_path, track, sub_output_dir, ffmpeg_path)
        
        print(f"  📁 字幕保存路径：{sub_output_dir}")
    
    except Exception as e:
        print(f"  ❌ 处理失败：{str(e)}")
    finally:
        gc.collect()

def batch_process_subtitle_tracks(input_root_dir, output_root_dir):
    """
    批量处理所有视频的字幕轨识别与提取
    :param input_root_dir: 输入视频根目录（videos_new）
    :param output_root_dir: 输出根目录（processed_videos_new）
    """
    ffmpeg_path = get_ffmpeg_path()
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)

    # 递归遍历所有子文件夹
    for root, dirs, files in os.walk(input_root_dir):
        for filename in files:
            if filename.lower().endswith('.mkv'):
                video_path = os.path.join(root, filename)
                process_single_video_subtitles(video_path, output_root_dir, ffmpeg_path)

    print("\n" + "="*60)
    print(f"🎉 字幕轨批量提取完成！所有文件已保存至：{output_root_dir}")
    print("="*60)

if __name__ == "__main__":
    # -------------------------- 配置区 --------------------------
    INPUT_ROOT_DIR = "./videos_new"        # 输入视频根目录
    OUTPUT_ROOT_DIR = "./processed_videos_new"  # 输出字幕根目录
    # -----------------------------------------------------------

    # 执行批量处理
    batch_process_subtitle_tracks(INPUT_ROOT_DIR, OUTPUT_ROOT_DIR)