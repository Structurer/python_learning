import os
import hashlib

def calculate_file_hash(file_path, algorithm="sha256"):
    """计算文件哈希值"""
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"❌ 计算哈希失败 | {file_path} → 错误原因：{str(e)}")
        return None

def compare_two_dirs_hash(
    dir1,
    dir2,
    algorithm="sha256"
):
    """对比两个目录（结构一致）下所有文件的哈希值"""
    total_count = 0
    match_count = 0
    mismatch_files = []
    missing_files = []

    # 检查目录是否存在
    for d in [dir1, dir2]:
        if not os.path.exists(d):
            print(f"❌ [错误] 目录 {d} 不存在")
            return False

    # 配置提示
    print("=" * 70)
    print(f"📌 目录哈希对比配置")
    print(f"   对比目录1：{os.path.abspath(dir1)}")
    print(f"   对比目录2：{os.path.abspath(dir2)}")
    print(f"   哈希算法：{algorithm}")
    print("=" * 70 + "\n")

    # 递归对比
    for root, dirs, files in os.walk(dir1):
        rel_dir = os.path.relpath(root, dir1)
        dir2_subdir = os.path.join(dir2, rel_dir)

        # 检查dir2中对应子目录是否存在
        if not os.path.exists(dir2_subdir):
            print(f"⚠️  目录缺失 | dir2中无对应目录：{dir2_subdir}")
            missing_files.extend([os.path.join(root, f) for f in files])
            continue

        for file_name in files:
            total_count += 1
            file1_path = os.path.join(root, file_name)
            file2_path = os.path.join(dir2_subdir, file_name)

            # 检查dir2中对应文件是否存在
            if not os.path.exists(file2_path):
                print(f"❌ 文件缺失 | dir2中无对应文件：{file2_path}")
                missing_files.append(file1_path)
                continue

            # 计算哈希并对比
            hash1 = calculate_file_hash(file1_path, algorithm)
            hash2 = calculate_file_hash(file2_path, algorithm)
            if not hash1 or not hash2:
                mismatch_files.append((file1_path, file2_path))
                continue

            if hash1 == hash2:
                print(f"✅ 哈希匹配 | {file_name} → {hash1}")
                match_count += 1
            else:
                print(f"❌ 哈希不匹配 | {file1_path}({hash1}) vs {file2_path}({hash2})")
                mismatch_files.append((file1_path, file2_path))

    # 执行结果
    print("=" * 70)
    print(f"🎉 目录哈希对比完成！")
    print(f"📊 统计：总文件数 = {total_count} | 匹配数 = {match_count} | 不匹配数 = {len(mismatch_files)} | 缺失数 = {len(missing_files)}")
    if mismatch_files:
        print("\n❌ 不匹配文件列表：")
        for idx, (f1, f2) in enumerate(mismatch_files, 1):
            print(f"   {idx}. {f1} ↔ {f2}")
    if missing_files:
        print("\n❌ 缺失文件列表（dir2中无对应文件）：")
        for idx, f in enumerate(missing_files, 1):
            print(f"   {idx}. {f}")
    print("=" * 70)
    return match_count == total_count and len(missing_files) == 0

# 主程序（测试用）
if __name__ == "__main__":
    DIR1 = r"E:\无耻之徒字幕重置"
    DIR2 = r"E:\decrypted"
    compare_two_dirs_hash(DIR1, DIR2)