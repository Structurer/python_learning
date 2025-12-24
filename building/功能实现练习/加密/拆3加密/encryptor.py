import os
import py7zr

def py7zr_recursive_single_file_encrypt(
    source_dir,
    encrypt_output_dir,
    password,
    encrypt_filename=True  # 保留文件名加密开关
):
    """递归单文件加密，支持选择是否加密文件名"""
    total_count = 0
    success_count = 0
    failed_files = []

    # 目录创建
    for dir_path in [source_dir, encrypt_output_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    if not os.listdir(source_dir):
        print(f"❌ [错误] 源文件夹 {source_dir} 为空，请放入待加密文件")
        return False

    # 配置提示（明确显示文件名加密状态）
    print("=" * 70)
    print(f"📌 加密配置信息")
    print(f"   加密算法：AES-256-CBC")
    print(f"   源文件目录：{os.path.abspath(source_dir)}")
    print(f"   加密包目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   文件名加密：{'✅ 开启' if encrypt_filename else '❌ 关闭'}")  # 显示开关状态
    print("=" * 70 + "\n")

    # 递归加密
    for root, dirs, files in os.walk(source_dir):
        for file_name in files:
            total_count += 1
            file_abs_path = os.path.join(root, file_name)
            rel_dir = os.path.relpath(root, source_dir)

            # 构建输出路径
            encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
            os.makedirs(encrypt_subdir, exist_ok=True)
            output_7z_path = os.path.join(encrypt_subdir, f"{file_name}.7z")

            try:
                with py7zr.SevenZipFile(output_7z_path, 'w', password=password) as archive:
                    # 根据开关决定是否加密文件名（核心逻辑保留）
                    if encrypt_filename:
                        try:
                            archive.set_encrypted_header(True)  # 加密文件名（头部信息）
                        except Exception:
                            print(f"⚠️  提示 | {file_name} - 当前py7zr版本不支持文件名加密，仅加密内容")
                    archive.write(file_abs_path, arcname=file_name)  # 写入文件
                print(f"✅ 加密完成 | {file_abs_path} → {output_7z_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ 加密失败 | {file_abs_path} → 错误原因：{str(e)}")
                failed_files.append(file_abs_path)
                continue

    # 执行结果
    print("=" * 70)
    task_desc = "加密+文件名加密" if encrypt_filename else "纯加密（仅内容）"  # 描述随开关变化
    print(f"🎉 {task_desc}任务全部完成！")
    print(f"📊 执行统计：总文件数 = {total_count} | 成功数 = {success_count} | 失败数 = {len(failed_files)}")
    print(f"💡 加密包位置：{os.path.abspath(encrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件完整路径列表：")
        for idx, failed_path in enumerate(failed_files, 1):
            print(f"   {idx}. {failed_path}")
    print("=" * 70)
    return True if success_count > 0 else False

# 主程序（测试用，可通过修改ENCRYPT_FILENAME控制开关）
if __name__ == "__main__":
    SOURCE_DIR = r"E:\temp"
    ENCRYPT_OUTPUT_DIR = r"E:\encryted"
    PASSWORD = "secp256k1"
    ENCRYPT_FILENAME = True  # 此处可设置True/False控制是否加密文件名

    py7zr_recursive_single_file_encrypt(
        source_dir=SOURCE_DIR,
        encrypt_output_dir=ENCRYPT_OUTPUT_DIR,
        password=PASSWORD,
        encrypt_filename=ENCRYPT_FILENAME  # 传入开关参数
    )