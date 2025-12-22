import subprocess
import re
import pysrt
import os
import sys
import tempfile
import gc

def get_ffmpeg_path():
    """获取FFmpeg路径，未配置环境变量则填写绝对路径"""
    # return r"C:\Program Files (x86)\ffmpeg-2025-12-18-git-78c75d546a-essentials_build\bin\ffmpeg.exe"
    return "ffmpeg"

def get_video_info(video_path, ffmpeg_path):
    """获取视频内字幕轨的索引、格式、语言信息"""
    cmd = [ffmpeg_path, '-i', video_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    output = result.stderr
    sub_info = []
    pattern = re.compile(r'Stream #0:(\d+).*?Subtitle: (\w+).*?\((\w+)\)')
    matches = pattern.findall(output)
    for idx, fmt, lang in matches:
        sub_info.append({"index": idx, "format": fmt, "language": lang})
    return sub_info

def extract_subtitle_to_temp(video_path, sub_index, sub_fmt, ffmpeg_path):
    """提取字幕到内存临时文件，返回临时文件路径"""
    if sub_fmt in ['ass', 'ssa']:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.ass', delete=False)
    elif sub_fmt in ['srt', 'subrip']:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    else:
        raise Exception(f"不支持的字幕格式：{sub_fmt}")
    
    temp_path = temp_file.name
    temp_file.close()

    cmd = [
        ffmpeg_path, '-i', video_path,
        '-map', f'0:{sub_index}',
        '-c:s', 'copy',
        temp_path,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    
    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
        os.unlink(temp_path)
        raise Exception(f"轨道{sub_index}提取失败！日志：{result.stderr}")
    print(f"  ✅ 提取轨道{sub_index}成功（{sub_fmt}格式，内存临时文件）")
    return temp_path

def convert_ass_to_srt_temp(ass_temp_path, ffmpeg_path):
    """ASS临时文件转SRT临时文件"""
    srt_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    srt_temp_path = srt_temp.name
    srt_temp.close()

    cmd = [
        ffmpeg_path, '-i', ass_temp_path,
        '-c:s', 'srt',
        srt_temp_path,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    
    if not os.path.exists(srt_temp_path):
        os.unlink(srt_temp_path)
        raise Exception(f"ASS转SRT失败！日志：{result.stderr}")
    print(f"  ✅ ASS转SRT成功（内存临时文件）")
    return srt_temp_path

def split_bilingual_to_english_temp(bilingual_srt_temp):
    """拆分双语SRT临时文件为纯英文非标准SRT临时文件"""
    raw_en_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    raw_en_temp_path = raw_en_temp.name
    raw_en_temp.close()

    try:
        subs = pysrt.open(bilingual_srt_temp, encoding='utf-8')
    except UnicodeDecodeError:
        subs = pysrt.open(bilingual_srt_temp, encoding='gbk')

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

    en_subs.save(raw_en_temp_path, encoding='utf-8')
    print(f"  ✅ 拆分纯英文成功（跳过{empty_count}个无效条目）")
    return raw_en_temp_path

def clean_non_standard_srt_temp(input_srt_temp):
    """清理非标准SRT临时文件为标准格式"""
    tag_pattern = re.compile(r'<[^>]+>')
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    number_pattern = re.compile(r'^\d+$')

    try:
        with open(input_srt_temp, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(input_srt_temp, 'r', encoding='gbk') as f:
            lines = f.readlines()

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

    if current_sub:
        cleaned_lines.extend(current_sub)
        cleaned_lines.append('\n')

    clean_en_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    clean_en_temp_path = clean_en_temp.name
    clean_en_temp.close()

    with open(clean_en_temp_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    print(f"  ✅ 非标准SRT转标准成功")
    return clean_en_temp_path

def merge_subtitles_to_mkv(video_path, output_video_path, subtitle_temp_paths, ffmpeg_path):
    """合并临时字幕文件到MKV，保留原视频音视频流"""
    cmd = [ffmpeg_path, '-i', video_path, '-y']
    for sub_temp in subtitle_temp_paths:
        cmd.extend(['-i', sub_temp])

    cmd.extend(['-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'copy'])

    subtitle_names = ["原始中英双语(ASS)", "纯中文(SRT)", "纯英文(SRT)"]
    for i in range(len(subtitle_temp_paths)):
        sub_input_idx = i + 1
        sub_track_idx = str(i)
        sub_name = subtitle_names[i] if i < len(subtitle_names) else f"字幕轨{sub_track_idx+1}"
        sub_file = subtitle_temp_paths[i]

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

    cmd.append(output_video_path)

    result = subprocess.run(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore'
    )

    if not os.path.exists(output_video_path):
        print(f"❌ FFmpeg错误日志：{result.stderr}")
        raise Exception("合并失败：未生成输出文件")
    if os.path.getsize(output_video_path) < 1024 * 1024:
        os.remove(output_video_path)
        print(f"❌ FFmpeg错误日志：{result.stderr}")
        raise Exception("合并失败：文件体积过小，未包含音视频流")
    
    print(f"  ✅ 合并完成：{os.path.basename(output_video_path)}（大小：{os.path.getsize(output_video_path)//1024//1024}MB）")
    return output_video_path

def process_single_video(video_file_path, output_video_path, ass_track_idx="2", srt_cn_track_idx="3"):
    """处理单个视频，保持文件名不变"""
    ffmpeg_path = get_ffmpeg_path()
    temp_files = []

    try:
        # 1. 获取字幕轨信息
        sub_info_list = get_video_info(video_file_path, ffmpeg_path)
        if not sub_info_list:
            print(f"  ❌ 未检测到字幕轨，跳过该视频")
            return None
        print(f"  检测到字幕轨：")
        for sub in sub_info_list:
            print(f"    轨道{sub['index']} | 格式：{sub['format']} | 语言：{sub['language']}")

        # 2. 提取临时字幕文件
        ass_temp = extract_subtitle_to_temp(video_file_path, ass_track_idx, "ass", ffmpeg_path)
        srt_cn_temp = extract_subtitle_to_temp(video_file_path, srt_cn_track_idx, "srt", ffmpeg_path)
        temp_files.extend([ass_temp, srt_cn_temp])

        # 3. ASS转SRT并拆分英文
        bilingual_srt_temp = convert_ass_to_srt_temp(ass_temp, ffmpeg_path)
        raw_en_temp = split_bilingual_to_english_temp(bilingual_srt_temp)
        temp_files.extend([bilingual_srt_temp, raw_en_temp])

        # 4. 清理英文SRT为标准格式
        clean_en_temp = clean_non_standard_srt_temp(raw_en_temp)
        temp_files.append(clean_en_temp)

        # 5. 合并字幕到新视频
        subtitle_temps = [ass_temp, srt_cn_temp, clean_en_temp]
        merge_subtitles_to_mkv(video_file_path, output_video_path, subtitle_temps, ffmpeg_path)

    except Exception as e:
        print(f"  ❌ 处理失败：{str(e)}")
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        return None
    finally:
        # 清理所有临时文件 + 回收内存
        for temp in temp_files:
            if os.path.exists(temp):
                os.unlink(temp)
        gc.collect()
    
    return output_video_path

def batch_process_recursive(input_root_dir, output_root_dir, ass_track_idx="2", srt_cn_track_idx="3"):
    """递归遍历输入目录所有子文件夹，保持目录结构批量处理MKV视频"""
    # 确保输出根目录存在
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)

    # 递归遍历所有文件和子文件夹
    for root, dirs, files in os.walk(input_root_dir):
        # 计算当前目录相对于输入根目录的相对路径
        relative_path = os.path.relpath(root, input_root_dir)
        # 构建输出目录路径，保持目录结构一致
        output_dir = os.path.join(output_root_dir, relative_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 处理当前目录下的所有MKV文件
        for filename in files:
            if filename.lower().endswith('.mkv'):
                input_video_path = os.path.join(root, filename)
                output_video_path = os.path.join(output_dir, filename)

                print(f"\n📌 处理文件：{input_video_path}")
                process_single_video(input_video_path, output_video_path, ass_track_idx, srt_cn_track_idx)

    print("\n" + "="*50)
    print("🎉 全部批量处理完成！输出目录：" + output_root_dir)
    print("="*50)

if __name__ == "__main__":
    # -------------------------- 配置区 --------------------------
    INPUT_ROOT_DIR = "E:\无耻之徒"          # 输入根目录：存放所有待处理视频（含子文件夹）
    OUTPUT_ROOT_DIR = "./processed_videos"  # 输出根目录：处理后视频保持原目录结构
    ASS_TRACK_INDEX = "2"                # ASS双语字幕轨索引
    SRT_CN_TRACK_INDEX = "3"             # 纯中文SRT字幕轨索引
    # -----------------------------------------------------------

    # 执行递归批量处理
    batch_process_recursive(INPUT_ROOT_DIR, OUTPUT_ROOT_DIR, ASS_TRACK_INDEX, SRT_CN_TRACK_INDEX)