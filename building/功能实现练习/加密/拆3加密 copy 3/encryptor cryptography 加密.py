import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64

def aes256_file_encrypt(
    source_dir=r"E:\temp",
    encrypt_output_dir=r"E:\encryted",
    password="secp256k1",  # 密码会被 SHA-256 处理为 32 字节密钥
    chunk_size=1024 * 1024 * 4,  # 4MB 分块，平衡速度和内存
    output_suffix=".enc"  # 加密文件后缀
):
    total_count = 0
    success_count = 0
    failed_files = []

    # 创建目录
    for dir_path in [source_dir, encrypt_output_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    if not os.listdir(source_dir):
        print(f"❌ 源文件夹 {source_dir} 为空")
        return False

    # 配置提示
    print("=" * 90)
    print(f"📌 AES-256 加密配置（无压缩，直接加密文件）")
    print(f"   源目录：{os.path.abspath(source_dir)}")
    print(f"   输出目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   分块大小：{chunk_size // 1024 // 1024}MB | 输出后缀：{output_suffix}")
    print("   加密模式：AES-256-CBC | 密钥来源：密码 SHA-256 哈希")
    print("=" * 90 + "\n")

    # 格式化文件大小
    def format_size(bytes_size):
        units = ['B', 'KB', 'MB', 'GB']
        unit_idx = 0
        while bytes_size >= 1024 and unit_idx < len(units)-1:
            bytes_size /= 1024
            unit_idx += 1
        return f"{bytes_size:.2f} {units[unit_idx]}"

    # 生成 AES-256 密钥和 IV
    def generate_key_iv(password_str):
        # 密码 SHA-256 哈希 → 32 字节密钥（AES-256 要求密钥长度 32B）
        from cryptography.hazmat.primitives import hashes
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(password_str.encode('utf-8'))
        key = digest.finalize()  # 32 字节密钥
        iv = os.urandom(16)  # 16 字节随机 IV（CBC 模式必须）
        return key, iv

    try:
        for root, dirs, files in os.walk(source_dir):
            for file_name in files:
                total_count += 1
                file_abs_path = os.path.join(root, file_name)
                rel_dir = os.path.relpath(root, source_dir)
                encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
                os.makedirs(encrypt_subdir, exist_ok=True)
                # 加密后文件名：原文件名 + .enc
                output_enc_path = os.path.join(encrypt_subdir, file_name + output_suffix)
                # IV 存储路径：加密文件同目录 + .iv（解密时必须）
                iv_path = output_enc_path + ".iv"

                file_total_size = os.path.getsize(file_abs_path)
                if file_total_size == 0:
                    print(f"⚠️  跳过空文件 | 文件名：{file_name}")
                    continue

                try:
                    # 记录单个文件加密开始时间
                    file_start_time = time.time()

                    # 生成密钥和 IV
                    key, iv = generate_key_iv(password)
                    # 保存 IV 到文件（解密时需要读取此文件）
                    with open(iv_path, 'wb') as iv_f:
                        iv_f.write(iv)

                    # 初始化 AES-256 CBC 加密器
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    encryptor = cipher.encryptor()
                    # PKCS7 填充（AES 要求明文长度是 16 字节倍数）
                    padder = padding.PKCS7(128).padder()  # 128 bits = 16 bytes

                    # 分块读取源文件 → 加密 → 写入目标文件
                    with open(file_abs_path, 'rb') as f_in, open(output_enc_path, 'wb') as f_out:
                        while True:
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            # 填充 + 加密
                            padded_chunk = padder.update(chunk)
                            encrypted_chunk = encryptor.update(padded_chunk)
                            f_out.write(encrypted_chunk)
                        # 处理最后一块的填充和加密
                        f_out.write(encryptor.update(padder.finalize()))
                        f_out.write(encryptor.finalize())

                    # 计算耗时和平均速度
                    file_elapsed_time = time.time() - file_start_time
                    file_avg_speed = file_total_size / file_elapsed_time / 1024 / 1024  # MB/s
                    file_size_str = format_size(file_total_size)

                    # 即时输出单文件统计
                    print(f"✅ 加密完成 | 文件名：{file_name} | 大小：{file_size_str} | 耗时：{file_elapsed_time:.2f}s | 平均速度：{file_avg_speed:.2f} MB/s | 保存至：{output_enc_path}")
                    success_count += 1

                except Exception as e:
                    print(f"❌ 加密失败 | 文件名：{file_name} | 错误信息：{str(e)}")
                    failed_files.append((file_name, str(e)))
                    continue

    except KeyboardInterrupt:
        print("\n\n⚠️  检测到强制退出，任务已中断")

    # 最终极简统计
    print("\n" + "=" * 90)
    print(f"🎉 AES-256 加密任务结束！ | 总文件数：{total_count} | 成功数：{success_count} | 失败数：{len(failed_files)}")
    print(f"💡 注意：解密时需要 密码 + 对应 .iv 文件 | 输出目录：{os.path.abspath(encrypt_output_dir)}")
    print("=" * 90)
    return success_count > 0

# 配套解密函数（可选，用于验证加密结果）
def aes256_file_decrypt(
    enc_file_path,
    password="secp256k1",
    output_path=None,
    chunk_size=1024 * 1024 * 4
):
    """
    解密 .enc 文件
    :param enc_file_path: 加密文件路径
    :param password: 加密密码
    :param output_path: 解密后文件路径，默认同目录去掉 .enc 后缀
    """
    iv_path = enc_file_path + ".iv"
    if not os.path.exists(iv_path):
        raise FileNotFoundError(f"IV 文件不存在：{iv_path}")
    
    if output_path is None:
        output_path = enc_file_path.replace(".enc", "")

    # 读取 IV
    with open(iv_path, 'rb') as iv_f:
        iv = iv_f.read()
    
    # 生成密钥
    from cryptography.hazmat.primitives import hashes
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password.encode('utf-8'))
    key = digest.finalize()

    # 初始化解密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(128).unpadder()

    # 分块解密
    with open(enc_file_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        while True:
            chunk = f_in.read(chunk_size)
            if not chunk:
                break
            decrypted_chunk = decryptor.update(chunk)
            unpadded_chunk = unpadder.update(decrypted_chunk)
            f_out.write(unpadded_chunk)
        f_out.write(unpadder.finalize())
        f_out.write(decryptor.finalize())
    
    print(f"✅ 解密完成：{output_path}")

if __name__ == "__main__":
    # 执行加密
    aes256_file_encrypt()

    # 示例解密（需替换为实际加密文件路径）
    # aes256_file_decrypt(
    #     enc_file_path=r"E:\encryted\test.txt.enc",
    #     password="secp256k1"
    # )