import subprocess
import re
import pysrt
import os
import sys
import tempfile
import gc

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

def extract_subtitle_to_temp(video_path, sub_index, sub_fmt, ffmpeg_path):
    """提取字幕到内存临时文件，返回临时文件对象"""
    # 创建临时文件，根据格式设置扩展名
    if sub_fmt in ['ass', 'ssa']:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.ass', delete=False)
    elif sub_fmt in ['srt', 'subrip']:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    else:
        raise Exception(f"不支持的字幕格式：{sub_fmt}")
    temp_path = temp_file.name
    temp_file.close()

    # 提取字幕到临时文件
    cmd = [
        ffmpeg_path, '-i', video_path,
        '-map', f'0:{sub_index}',
        '-c:s', 'copy',
        temp_path,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
        os.unlink(temp_path)  # 删除空临时文件
        raise Exception(f"提取轨道{sub_index}失败！日志：{result.stderr}")
    print(f"✅ 提取轨道{sub_index}成功（格式：{sub_fmt}，内存临时文件）")
    return temp_path

def convert_ass_to_srt_temp(ass_temp_path, ffmpeg_path):
    """ASS临时文件转SRT临时文件，返回SRT临时文件路径"""
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
    print(f"✅ ASS转SRT成功（内存临时文件）")
    return srt_temp_path

def split_bilingual_to_english_temp(bilingual_srt_temp, ffmpeg_path):
    """拆分双语SRT临时文件为纯英文SRT（非标准），返回临时文件路径"""
    # 拆分出非标准英文临时文件
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
    print(f"✅ 拆分纯英文成功（跳过{empty_count}个无英文条目，内存临时文件）")
    return raw_en_temp_path

def clean_non_standard_srt_temp(input_srt_temp):
    """清理非标准SRT临时文件为标准格式，返回标准SRT临时文件路径"""
    tag_pattern = re.compile(r'<[^>]+>')
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    number_pattern = re.compile(r'^\d+$')

    # 读取原临时文件
    try:
        with open(input_srt_temp, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(input_srt_temp, 'r', encoding='gbk') as f:
            lines = f.readlines()

    # 清理内容
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

    # 写入标准SRT临时文件
    clean_en_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    clean_en_temp_path = clean_en_temp.name
    clean_en_temp.close()

    with open(clean_en_temp_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    print(f"✅ 非标准SRT转标准成功（内存临时文件）")
    return clean_en_temp_path

def merge_subtitles_to_mkv(video_path, output_video, subtitle_temp_paths, ffmpeg_path):
    """合并临时字幕文件到MKV，返回最终视频路径"""
    cmd = [ffmpeg_path, '-i', video_path, '-y']
    # 添加所有临时字幕文件作为输入
    for sub_temp in subtitle_temp_paths:
        cmd.extend(['-i', sub_temp])
    
    # 映射视频和音频流
    cmd.extend(['-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'copy'])
    
    # 映射字幕轨
    subtitle_names = ["原始中英双语(ASS)", "纯中文(SRT)", "纯英文(SRT)"]
    for i in range(len(subtitle_temp_paths)):
        sub_input_idx = i + 1
        sub_track_idx = str(i)
        sub_name = subtitle_names[i] if i < len(subtitle_names) else f"字幕轨{int(sub_track_idx)+1}"
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
    
    cmd.append(output_video)

    # 执行合并
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

def process_single_video(video_file_path, output_dir='./'):
    """处理单个视频的核心函数，方便后续批量调用"""
    ffmpeg_path = get_ffmpeg_path()
    video_filename = os.path.basename(video_file_path)
    output_video = os.path.join(output_dir, f"final_video_with_3_subs_{video_filename}")

    # 步骤1：获取字幕轨信息
    sub_info_list = get_video_info(video_file_path, ffmpeg_path)
    if not sub_info_list:
        print(f"❌ {video_filename} 未检测到字幕轨，跳过处理")
        return None
    print(f"\n📌 处理视频：{video_filename}")
    print(f"   检测到的字幕轨：")
    for sub in sub_info_list:
        print(f"   轨道{sub['index']} | 格式：{sub['format']} | 语言：{sub['language']}")

    # 步骤2：提取ASS和SRT临时文件
    ass_sub_index = "2"  # 固定轨道2为ASS双语轨
    srt_sub_index = "3"  # 固定轨道3为SRT中文轨
    ass_temp = extract_subtitle_to_temp(video_file_path, ass_sub_index, "ass", ffmpeg_path)
    srt_cn_temp = extract_subtitle_to_temp(video_file_path, srt_sub_index, "srt", ffmpeg_path)

    # 步骤3：ASS转SRT并拆分英文
    bilingual_srt_temp = convert_ass_to_srt_temp(ass_temp, ffmpeg_path)
    raw_en_temp = split_bilingual_to_english_temp(bilingual_srt_temp, ffmpeg_path)

    # 步骤4：清理英文SRT为标准格式
    clean_en_temp = clean_non_standard_srt_temp(raw_en_temp)

    # 步骤5：合并字幕到MKV
    subtitle_temps = [ass_temp, srt_cn_temp, clean_en_temp]
    merge_subtitles_to_mkv(video_file_path, output_video, subtitle_temps, ffmpeg_path)

    # 步骤6：清理所有临时文件 + 回收内存
    temp_files = [ass_temp, srt_cn_temp, bilingual_srt_temp, raw_en_temp, clean_en_temp]
    for temp in temp_files:
        if os.path.exists(temp):
            os.unlink(temp)
    print(f"✅ 清理临时文件完成，释放内存")
    gc.collect()  # 手动触发垃圾回收

    return output_video

def batch_process_videos(input_dir, output_dir='./'):
    """批量处理文件夹中的所有MKV视频"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.mkv'):
            video_path = os.path.join(input_dir, filename)
            process_single_video(video_path, output_dir)

if __name__ == "__main__":
    # 方式1：处理单个视频（替换为你的视频路径）
    # single_video_path = "Shameless.US.S10E09.2019.1080p.WEB_DL.x265.10bit.AC3￡cXcY@FRDS.mkv"
    # process_single_video(single_video_path)

    # 方式2：批量处理文件夹中的所有MKV（取消注释启用，替换输入/输出目录）
    input_directory = "./videos"  # 视频所在文件夹
    output_directory = "./processed_videos"  # 输出视频的文件夹
    batch_process_videos(input_directory, output_directory)

    print("\n🎉 所有视频处理完成！仅保留最终合并的MKV视频文件")