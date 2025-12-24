import os
import pyzipper
import time

def pyzipper_recursive_single_file_encrypt(
    source_dir=r"E:\temp",
    encrypt_output_dir=r"E:\encryted",
    password="secp256k1",
    chunk_size=1024 * 1024 * 2  # 2MB 块
):
    total_count = 0
    success_count = 0
    failed_files = []

    for dir_path in [source_dir, encrypt_output_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    if not os.listdir(source_dir):
        print(f"❌ 源文件夹 {source_dir} 为空")
        return False

    print("=" * 90)
    print(f"📌 加密配置信息")
    print(f"   源目录：{os.path.abspath(source_dir)}")
    print(f"   输出目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   压缩模式：STORE（仅打包不压缩）")
    print(f"   块大小：{chunk_size // 1024 // 1024}MB")
    print("=" * 90 + "\n")

    def format_size(bytes_size):
        units = ['B', 'KB', 'MB', 'GB']
        unit_idx = 0
        while bytes_size >= 1024 and unit_idx < len(units)-1:
            bytes_size /= 1024
            unit_idx += 1
        return f"{bytes_size:.2f} {units[unit_idx]}"

    try:
        for root, dirs, files in os.walk(source_dir):
            for file_name in files:
                total_count += 1
                file_abs_path = os.path.join(root, file_name)
                rel_dir = os.path.relpath(root, source_dir)
                encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
                os.makedirs(encrypt_subdir, exist_ok=True)
                output_zip_path = os.path.join(encrypt_subdir, f"{file_name}.zip")

                file_total_size = os.path.getsize(file_abs_path)
                if file_total_size == 0:
                    print(f"⚠️  跳过空文件：{file_abs_path}")
                    continue

                processed_size = 0
                start_time = time.time()
                progress_bar_length = 40

                try:
                    with pyzipper.AESZipFile(
                        output_zip_path,
                        'w',
                        compression=pyzipper.ZIP_STORED,
                        encryption=pyzipper.WZ_AES,
                        compresslevel=0
                    ) as zf:
                        zf.setpassword(password.encode('utf-8'))
                        zip_info = pyzipper.ZipInfo.from_file(file_abs_path, arcname=file_name)
                        zip_info.compress_type = pyzipper.ZIP_STORED

                        with open(file_abs_path, 'rb') as f_in:
                            # 先写入空数据，然后追加？不，这里直接用 writestr + 分块
                            # 修正：使用 writestr 接收文件内容
                            content = b''
                            while True:
                                chunk = f_in.read(chunk_size)
                                if not chunk:
                                    break
                                content += chunk
                                processed_size += len(chunk)

                                elapsed_time = max(time.time() - start_time, 0.001)
                                speed = processed_size / elapsed_time / 1024 / 1024
                                progress = processed_size / file_total_size
                                progress_percent = progress * 100
                                filled_length = int(progress_bar_length * progress)
                                progress_bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)

                                print(f"\r📤 {file_name} | {format_size(processed_size)}/{format_size(file_total_size)} | "
                                      f"[{progress_bar}] {progress_percent:.1f}% | 速度：{speed:.2f} MB/s", end='', flush=True)
                            zf.writestr(zip_info, content)

                    total_time = time.time() - start_time
                    avg_speed = file_total_size / total_time / 1024 / 1024
                    print(f"\n✅ 加密完成 | 耗时：{total_time:.2f}s | 平均速度：{avg_speed:.2f} MB/s | 保存至：{output_zip_path}")
                    success_count += 1

                except Exception as e:
                    print(f"\n❌ 加密失败 | {file_abs_path} → 错误：{str(e)}")
                    failed_files.append((file_abs_path, str(e)))
                    continue

    except KeyboardInterrupt:
        print("\n\n⚠️  检测到强制退出，任务已中断")

    print("\n" + "=" * 90)
    print(f"🎉 加密任务结束！")
    print(f"📊 统计：总文件数={total_count}，成功={success_count}，失败={len(failed_files)}")
    print(f"💡 输出目录：{os.path.abspath(encrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件列表：")
        for idx, (path, err) in enumerate(failed_files, 1):
            print(f"   {idx}. {path} | 错误：{err}")
    print("=" * 90)
    return success_count > 0

if __name__ == "__main__":
    pyzipper_recursive_single_file_encrypt()