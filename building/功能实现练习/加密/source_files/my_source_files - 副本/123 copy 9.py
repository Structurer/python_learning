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
    """提取字幕到内存临时文件，自动适配格式，返回临时文件路径"""
    # 根据实际格式设置临时文件后缀
    suffix = f'.{sub_fmt}' if sub_fmt in ['ass', 'ssa', 'srt', 'subrip'] else '.srt'
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False)
    temp_path = temp_file.name
    temp_file.close()

    cmd = [
        ffmpeg_path, '-i', video_path,
        '-map', f'0:{sub_index}',
        '-c:s', 'copy',  # 直接复制字幕流，不强制编码，避免格式不匹配
        temp_path,
        '-y'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8', errors='ignore')
    
    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise Exception(f"轨道{sub_index}提取失败！日志：{result.stderr}")
    print(f"  ✅ 提取轨道{sub_index}成功（{sub_fmt}格式，内存临时文件）")
    return temp_path

def convert_ass_to_srt_temp(ass_temp_path, ffmpeg_path):
    """ASS临时文件转SRT临时文件，确保生成有效SRT"""
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
    
    if not os.path.exists(srt_temp_path) or os.path.getsize(srt_temp_path) == 0:
        if os.path.exists(srt_temp_path):
            os.unlink(srt_temp_path)
        raise Exception(f"ASS转SRT失败！日志：{result.stderr}")
    print(f"  ✅ ASS转SRT成功（内存临时文件）")
    return srt_temp_path

def create_sub_rip_item_copy(original_sub):
    """
    兼容低版本pysrt：手动创建SubRipItem副本，替代copy()方法
    :param original_sub: 原始SubRipItem对象
    :return: 复制后的SubRipItem对象
    """
    new_sub = pysrt.SubRipItem()
    # 复制字幕核心属性
    new_sub.index = original_sub.index
    new_sub.start = original_sub.start
    new_sub.end = original_sub.end
    new_sub.text = original_sub.text
    new_sub.position = original_sub.position
    return new_sub

def split_bilingual_to_cn_en_temp(bilingual_srt_temp):
    """
    优化拆分逻辑：兼容多种双语格式，避免生成空字幕，兼容低版本pysrt
    :param bilingual_srt_temp: 双语SRT临时文件路径
    :return: (纯中文SRT临时路径, 纯英文SRT临时路径)
    """
    # 创建两个临时文件
    cn_srt_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    en_srt_temp = tempfile.NamedTemporaryFile(mode='wb', suffix='.srt', delete=False)
    cn_temp_path = cn_srt_temp.name
    en_temp_path = en_srt_temp.name
    cn_srt_temp.close()
    en_srt_temp.close()

    # 读取SRT文件，兼容多种编码
    try:
        subs = pysrt.open(bilingual_srt_temp, encoding='utf-8')
    except (UnicodeDecodeError, FileNotFoundError):
        try:
            subs = pysrt.open(bilingual_srt_temp, encoding='gbk')
        except:
            subs = pysrt.open(bilingual_srt_temp, encoding='utf-16')

    cn_subs = pysrt.SubRipFile()
    en_subs = pysrt.SubRipFile()
    total_subs = len(subs)
    cn_empty = 0
    en_empty = 0

    for sub in subs:
        # 清理样式标签和空白字符
        clean_text = re.sub(r'<[^>]+>', '', sub.text).strip()
        if not clean_text:
            cn_empty += 1
            en_empty += 1
            continue
        
        # 按换行拆分，兼容「中上英下」「英上中下」「多换行」场景
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        cn_text = ""
        en_text = ""

        # 识别中文（含汉字）和英文（含字母）
        for line in lines:
            if re.search(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]', line):
                if not cn_text:
                    cn_text = line
            elif re.search(r'[a-zA-Z]', line):
                if not en_text:
                    en_text = line

        # 仅添加有效字幕（使用手动复制方法，兼容低版本pysrt）
        if cn_text:
            # sub_cn = sub.copy()  # 注释掉原copy方法
            sub_cn = create_sub_rip_item_copy(sub)  # 使用兼容方法
            sub_cn.text = cn_text
            cn_subs.append(sub_cn)
        else:
            cn_empty += 1

        if en_text:
            # sub_en = sub.copy()  # 注释掉原copy方法
            sub_en = create_sub_rip_item_copy(sub)  # 使用兼容方法
            sub_en.text = en_text
            en_subs.append(sub_en)
        else:
            en_empty += 1

    # 校验是否生成有效字幕，避免空文件
    if len(cn_subs) == 0:
        raise Exception(f"拆分纯中文失败：未识别到有效中文字幕条目")
    if len(en_subs) == 0:
        raise Exception(f"拆分纯英文失败：未识别到有效英文字幕条目")

    # 保存字幕
    cn_subs.save(cn_temp_path, encoding='utf-8')
    en_subs.save(en_temp_path, encoding='utf-8')

    print(f"  ✅ 双语拆分成功：纯中文（有效{len(cn_subs)}/{total_subs}）、纯英文（有效{len(en_subs)}/{total_subs}）")
    return cn_temp_path, en_temp_path

def merge_subtitles_to_mkv(video_path, output_video_path, subtitle_temp_paths, ffmpeg_path):
    """合并临时字幕文件到MKV，保留原视频音视频流"""
    cmd = [ffmpeg_path, '-i', video_path, '-y']
    for sub_temp in subtitle_temp_paths:
        cmd.extend(['-i', sub_temp])

    # 映射视频和音频流，保持原格式
    cmd.extend(['-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-c:a', 'copy'])

    # 映射字幕轨，自动适配格式
    subtitle_names = ["原始中英双语(ASS)", "纯中文(SRT)", "纯英文(SRT)"]
    for i in range(len(subtitle_temp_paths)):
        sub_input_idx = i + 1
        sub_track_idx = str(i)
        sub_name = subtitle_names[i] if i < len(subtitle_names) else f"字幕轨{sub_track_idx+1}"
        sub_file = subtitle_temp_paths[i]

        # 根据字幕文件后缀判断格式
        if sub_file.endswith(('.ass', '.ssa')):
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

    # 校验输出文件
    if not os.path.exists(output_video_path):
        raise Exception(f"合并失败：未生成输出文件！FFmpeg日志：{result.stderr}")
    if os.path.getsize(output_video_path) < 1024 * 1024:  # 小于1MB视为无效
        os.remove(output_video_path)
        raise Exception(f"合并失败：文件体积过小！FFmpeg日志：{result.stderr}")
    
    print(f"  ✅ 合并完成：{os.path.basename(output_video_path)}（大小：{os.path.getsize(output_video_path)//1024//1024}MB）")
    return output_video_path

def process_single_video(video_file_path, output_video_path, target_ass_track_idx="2"):
    """
    处理单个视频：兼容你的视频格式，避免空字幕和格式错误，兼容低版本pysrt
    :param video_file_path: 输入视频路径
    :param output_video_path: 输出视频路径
    :param target_ass_track_idx: 目标ASS双语轨道索引
    """
    ffmpeg_path = get_ffmpeg_path()
    temp_files = []

    try:
        # 1. 检查目标轨道是否存在且为ASS格式
        sub_info_list = get_video_info(video_file_path, ffmpeg_path)
        target_track = None
        for sub in sub_info_list:
            if sub["index"] == target_ass_track_idx and sub["format"] in ["ass", "ssa"]:
                target_track = sub
                break
        if not target_track:
            print(f"  ❌ 轨道{target_ass_track_idx}不是ASS格式或不存在，跳过该视频")
            return None
        print(f"  检测到目标轨道：{target_ass_track_idx}（{target_track['format']}格式）")

        # 2. 提取ASS双语临时文件
        ass_temp = extract_subtitle_to_temp(video_file_path, target_ass_track_idx, "ass", ffmpeg_path)
        temp_files.append(ass_temp)

        # 3. ASS转SRT（先转SRT再拆分，提高兼容性）
        bilingual_srt_temp = convert_ass_to_srt_temp(ass_temp, ffmpeg_path)
        temp_files.append(bilingual_srt_temp)

        # 4. 拆分纯中文、纯英文SRT
        cn_srt_temp, en_srt_temp = split_bilingual_to_cn_en_temp(bilingual_srt_temp)
        temp_files.extend([cn_srt_temp, en_srt_temp])

        # 5. 合并3个字幕轨（ASS+纯中文SRT+纯英文SRT）
        subtitle_temps = [ass_temp, cn_srt_temp, en_srt_temp]
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

def batch_process_recursive(input_root_dir, output_root_dir, target_ass_track_idx="2"):
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
                process_single_video(input_video_path, output_video_path, target_ass_track_idx)

    print("\n" + "="*50)
    print("🎉 全部批量处理完成！输出目录：" + output_root_dir)
    print("="*50)

if __name__ == "__main__":
    # -------------------------- 配置区 --------------------------
    INPUT_ROOT_DIR = "./videos_new"       # 新视频组的输入根目录
    OUTPUT_ROOT_DIR = "./processed_videos_new"  # 新视频组的输出目录
    TARGET_ASS_TRACK_INDEX = "2"          # 待处理的ASS双语轨道索引
    # -----------------------------------------------------------

    # 执行递归批量处理
    batch_process_recursive(INPUT_ROOT_DIR, OUTPUT_ROOT_DIR, TARGET_ASS_TRACK_INDEX)