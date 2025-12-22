import os
import py7zr
import hashlib

def calculate_file_hash(file_path, algorithm="sha256"):
    """
    计算文件哈希值，用于校验加密前后内容一致性
    :param file_path: 待计算哈希的文件路径
    :param algorithm: 哈希算法，默认 SHA-256
    :return: 小写哈希字符串
    """
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def py7zr_recursive_single_file_encrypt(
    source_dir,
    encrypt_output_dir,
    check_temp_dir,
    password,
    encrypt_filename=True,
    enable_hash_check=True
):
    """
    递归单文件加密 + 可选哈希校验 + 统计与失败文件列表
    :param source_dir: 源文件目录（与脚本同级）
    :param encrypt_output_dir: 加密包输出目录（与脚本同级）
    :param check_temp_dir: 校验临时解压目录（与脚本同级）
    :param password: 加密密码
    :param encrypt_filename: 是否加密文件名开关
    :param enable_hash_check: 是否启用哈希校验开关
    :return: 执行结果布尔值
    """
    # ========== 新增：初始化统计变量 ==========
    total_count = 0          # 总文件数
    success_count = 0        # 成功数
    failed_files = []        # 失败文件列表（存储完整路径）

    # 基础目录校验与创建
    for dir_path in [source_dir, encrypt_output_dir]:
        os.makedirs(dir_path, exist_ok=True)
    # 仅当校验开关开启时，创建校验目录
    if enable_hash_check:
        os.makedirs(check_temp_dir, exist_ok=True)
    
    if not os.listdir(source_dir):
        print(f"❌ [错误] 源文件夹 {source_dir} 为空，请放入待加密文件")
        return False

    # ========== 动态生成配置信息提示 ==========
    print("=" * 70)
    print(f"📌 加密配置信息（py7zr 1.1.0 版本 | 三目录分离）")
    print(f"   加密算法：AES-256-CBC（固定模式）")
    print(f"   源文件目录：{os.path.abspath(source_dir)}")
    print(f"   加密包目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   文件名加密：{'✅ 开启' if encrypt_filename else '❌ 关闭'}")
    print(f"   哈希校验：{'✅ 开启' if enable_hash_check else '❌ 关闭'}")
    if enable_hash_check:
        print(f"   校验临时目录：{os.path.abspath(check_temp_dir)}")
    print("=" * 70 + "\n")

    # ========== 递归遍历源文件加密 ==========
    for root, dirs, files in os.walk(source_dir):
        for file_name in files:
            total_count += 1  # 每遍历一个文件，总计数+1
            file_abs_path = os.path.join(root, file_name)
            rel_dir = os.path.relpath(root, source_dir)
            
            # 构建加密包输出路径
            encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
            os.makedirs(encrypt_subdir, exist_ok=True)
            output_7z_path = os.path.join(encrypt_subdir, f"{file_name}.7z")

            try:
                # ---------- 1. 加密逻辑 ----------
                with py7zr.SevenZipFile(output_7z_path, 'w', password=password) as archive:
                    # 仅当文件名加密开关开启时，尝试启用该功能
                    if encrypt_filename:
                        try:
                            archive.set_encrypted_header(True)
                        except Exception:
                            print(f"⚠️  提示 | {file_name} - 当前版本不支持文件名加密，仅加密内容")
                    archive.write(file_abs_path, arcname=file_name)
                print(f"✅ 加密完成 | {file_abs_path} → {output_7z_path}")
                success_count += 1  # 加密成功，计数+1

                # ---------- 2. 校验逻辑（仅开关开启时执行） ----------
                if enable_hash_check:
                    # 计算原文件哈希
                    original_hash = calculate_file_hash(file_abs_path)
                    print(f"📝 原文件哈希 | {file_name} → {original_hash}")
                    
                    # 构建校验解压路径
                    check_subdir = os.path.join(check_temp_dir, rel_dir)
                    os.makedirs(check_subdir, exist_ok=True)
                    temp_extract_dir = os.path.join(check_subdir, f"temp_{file_name}")
                    os.makedirs(temp_extract_dir, exist_ok=True)

                    # 解压加密包并计算哈希对比
                    with py7zr.SevenZipFile(output_7z_path, 'r', password=password) as archive:
                        archive.extractall(temp_extract_dir)
                    extracted_file_path = os.path.join(temp_extract_dir, file_name)
                    extracted_hash = calculate_file_hash(extracted_file_path)
                    
                    if original_hash == extracted_hash:
                        print(f"   ✅ 校验通过 | 解压文件哈希 → {extracted_hash}")
                    else:
                        print(f"   ❌ 校验失败 | 原哈希 {original_hash} vs 解压哈希 {extracted_hash}")
                    print(f"   📂 校验文件路径 | {temp_extract_dir}\n")

            except Exception as e:
                print(f"❌ 加密失败 | {file_abs_path} → 错误原因：{str(e)}\n")
                failed_files.append(file_abs_path)  # 失败文件添加到列表
                continue

    # ========== 动态生成执行完毕提示（新增统计和失败列表） ==========
    print("=" * 70)
    # 任务类型描述
    if enable_hash_check and encrypt_filename:
        task_desc = "加密+文件名加密+哈希校验"
    elif enable_hash_check:
        task_desc = "加密+哈希校验"
    elif encrypt_filename:
        task_desc = "加密+文件名加密"
    else:
        task_desc = "纯加密"
    print(f"🎉 {task_desc}任务全部完成！")
    # 核心统计信息
    print(f"📊 执行统计：总文件数 = {total_count} | 成功数 = {success_count} | 失败数 = {len(failed_files)}")
    print(f"💡 加密包位置：{os.path.abspath(encrypt_output_dir)}")
    if enable_hash_check:
        print(f"💡 校验文件位置：{os.path.abspath(check_temp_dir)}（可手动删除）")
    # 输出失败文件列表
    if failed_files:
        print("\n❌ 失败文件完整路径列表：")
        for idx, failed_path in enumerate(failed_files, 1):
            print(f"   {idx}. {failed_path}")
    print("=" * 70)
    return True if success_count > 0 else False

# ========== 主程序配置区域（三目录与脚本同级） ==========
if __name__ == "__main__":
    # 三个同级目录名称（与py脚本放在同一文件夹下）
    SOURCE_DIR = r"E:\processed_videos"          # 待加密文件存放目录
    ENCRYPT_OUTPUT_DIR = r"E:\encryted"  # 加密包输出目录
    CHECK_TEMP_DIR = r"E:\checktemp"   # 校验临时解压目录

    PASSWORD = "secp256k1"                           # 测试用加密密码
    ENCRYPT_FILENAME = True                   # 文件名加密开关（False=关闭）
    ENABLE_HASH_CHECK = True                  # 哈希校验开关（False=关闭）

    # 调用加密函数
    py7zr_recursive_single_file_encrypt(
        source_dir=SOURCE_DIR,
        encrypt_output_dir=ENCRYPT_OUTPUT_DIR,
        check_temp_dir=CHECK_TEMP_DIR,
        password=PASSWORD,
        encrypt_filename=ENCRYPT_FILENAME,
        enable_hash_check=ENABLE_HASH_CHECK
    )