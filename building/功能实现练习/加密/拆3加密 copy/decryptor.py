import os
import py7zr

def py7zr_recursive_single_file_decrypt(
    encrypt_dir,
    decrypt_output_dir,
    password
):
    """递归解压7z加密包，恢复原文件结构"""
    total_count = 0
    success_count = 0
    failed_files = []

    # 目录创建
    os.makedirs(decrypt_output_dir, exist_ok=True)
    
    if not os.listdir(encrypt_dir):
        print(f"❌ [错误] 加密包文件夹 {encrypt_dir} 为空，请放入待解压文件")
        return False

    # 配置提示
    print("=" * 70)
    print(f"📌 解压配置信息")
    print(f"   加密包目录：{os.path.abspath(encrypt_dir)}")
    print(f"   解压输出目录：{os.path.abspath(decrypt_output_dir)}")
    print("=" * 70 + "\n")

    # 递归解压
    for root, dirs, files in os.walk(encrypt_dir):
        for file_name in files:
            if not file_name.endswith(".7z"):
                print(f"⚠️  跳过非7z文件 | {file_name}")
                continue
            total_count += 1
            file_abs_path = os.path.join(root, file_name)
            rel_dir = os.path.relpath(root, encrypt_dir)
            original_file_name = file_name[:-3]  # 去掉.7z后缀

            # 构建解压路径
            decrypt_subdir = os.path.join(decrypt_output_dir, rel_dir)
            os.makedirs(decrypt_subdir, exist_ok=True)
            output_file_path = os.path.join(decrypt_subdir, original_file_name)

            try:
                with py7zr.SevenZipFile(file_abs_path, 'r', password=password) as archive:
                    archive.extractall(decrypt_subdir)
                print(f"✅ 解压完成 | {file_abs_path} → {output_file_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ 解压失败 | {file_abs_path} → 错误原因：{str(e)}")
                failed_files.append(file_abs_path)
                continue

    # 执行结果
    print("=" * 70)
    print(f"🎉 解压任务全部完成！")
    print(f"📊 执行统计：总加密包数 = {total_count} | 成功数 = {success_count} | 失败数 = {len(failed_files)}")
    print(f"💡 解压文件位置：{os.path.abspath(decrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件完整路径列表：")
        for idx, failed_path in enumerate(failed_files, 1):
            print(f"   {idx}. {failed_path}")
    print("=" * 70)
    return True if success_count > 0 else False

# 主程序（测试用）
if __name__ == "__main__":
    ENCRYPT_DIR = r"E:\encryted\无耻之徒S02.Shameless.US.2012.1080p.Blu-ray.x265.AC3￡cXcY@FRDS"
    DECRYPT_OUTPUT_DIR = r"E:\decrypted"
    PASSWORD = "secp256k1"

    py7zr_recursive_single_file_decrypt(
        encrypt_dir=ENCRYPT_DIR,
        decrypt_output_dir=DECRYPT_OUTPUT_DIR,
        password=PASSWORD
    )