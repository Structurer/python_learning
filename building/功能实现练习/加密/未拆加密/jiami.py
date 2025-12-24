import os
import py7zr

def py7zr_encrypt_folder(source_dir, output_7z_path, password, encrypt_filename=True):
    """
    基于 py7zr 的基础加密（适配所有旧版本，无高级参数依赖）
    :param source_dir: 待加密文件夹路径
    :param output_7z_path: 输出 7z 压缩包路径
    :param password: 加密密码
    :param encrypt_filename: True=加密文件名，False=仅加密文件内容
    """
    # 基础校验：文件夹存在且非空
    if not os.path.isdir(source_dir):
        print(f"❌ 错误：源文件夹不存在 → {source_dir}")
        return False
    if not os.listdir(source_dir):
        print(f"❌ 错误：源文件夹为空 → {source_dir}")
        return False

    # 自动创建输出目录
    output_dir = os.path.dirname(output_7z_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 旧版 py7zr 最简配置：仅传入路径和密码，移除所有高级参数
        with py7zr.SevenZipFile(output_7z_path, 'w', password=password) as archive:
            # 若支持文件名加密，则启用；不支持则忽略（避免报错）
            try:
                if encrypt_filename:
                    archive.set_encrypted_header(True)
            except:
                print(f"⚠️  提示：当前 py7zr 版本不支持文件名加密，仅加密文件内容")
            # 递归添加整个文件夹，保持原目录结构
            archive.writeall(source_dir, arcname=os.path.basename(source_dir))
        print(f"✅ 加密成功！压缩包路径：\n{output_7z_path}")
        return True
    except Exception as e:
        print(f"❌ 加密失败：{str(e)}")
        return False

if __name__ == "__main__":
    # ====================== 配置区域（按需修改） ======================
    SOURCE_DIR = r".\my_source_files"          # 待加密的文件夹（需存在且非空）
    OUTPUT_7Z = r".\my_encrypted_zips\my_encrypted.7z"  # 输出压缩包路径
    PASSWORD = "YourStrongPassword123!"        # 加密密码（避免特殊符号）
    ENCRYPT_FILENAME = True                    # 是否尝试加密文件名
    # =================================================================

    # 执行加密
    py7zr_encrypt_folder(SOURCE_DIR, OUTPUT_7Z, PASSWORD, ENCRYPT_FILENAME)