import os
import py7zr

def py7zr_recursive_single_file_encrypt(source_dir, output_root_dir, password, encrypt_filename=True):
    """
    递归遍历所有子文件夹，单文件对应单压缩包加密（适配旧版 py7zr）
    :param source_dir: 待加密的根文件夹
    :param output_root_dir: 压缩包输出根目录
    :param password: 加密密码
    :param encrypt_filename: 是否尝试加密文件名
    """
    # 基础校验：源文件夹是否存在
    if not os.path.isdir(source_dir):
        print(f"❌ 错误：源文件夹不存在 → {source_dir}")
        return False

    # 递归遍历所有目录和文件
    for root, dirs, files in os.walk(source_dir):
        for file_name in files:
            # 构建当前文件的绝对路径
            file_abs_path = os.path.join(root, file_name)
            # 计算当前文件相对于源根目录的相对路径，用于保持目录结构
            rel_dir = os.path.relpath(root, source_dir)
            # 构建输出目录：输出根目录 + 相对路径
            output_dir = os.path.join(output_root_dir, rel_dir)
            os.makedirs(output_dir, exist_ok=True)
            # 构建单个文件的压缩包路径：原文件名 + .7z
            output_7z_path = os.path.join(output_dir, f"{file_name}.7z")

            try:
                # 旧版 py7zr 最简配置，无高级参数
                with py7zr.SevenZipFile(output_7z_path, 'w', password=password) as archive:
                    # 尝试启用文件名加密，不支持则跳过并提示
                    try:
                        if encrypt_filename:
                            archive.set_encrypted_header(True)
                    except Exception:
                        print(f"⚠️  提示：{file_abs_path} - 当前版本不支持文件名加密，仅加密内容")
                    # 单个文件写入压缩包，压缩包内保留原文件名
                    archive.write(file_abs_path, arcname=file_name)
                print(f"✅ 加密完成：{file_abs_path} → {output_7z_path}")
            except Exception as e:
                print(f"❌ 加密失败：{file_abs_path} - {str(e)}")
                continue  # 单个文件失败不影响其他文件加密

    print("\n📌 所有文件递归加密任务执行完毕！")
    return True

if __name__ == "__main__":
    # ====================== 配置区域（按需修改） ======================
    SOURCE_DIR = r".\my_source_files"          # 待加密的根文件夹
    OUTPUT_ROOT_DIR = r".\single_file_7z_recursive"  # 压缩包输出根目录
    PASSWORD = "123"        # 加密密码
    ENCRYPT_FILENAME = True                    # 是否尝试加密文件名
    # =================================================================

    py7zr_recursive_single_file_encrypt(SOURCE_DIR, OUTPUT_ROOT_DIR, PASSWORD, ENCRYPT_FILENAME)