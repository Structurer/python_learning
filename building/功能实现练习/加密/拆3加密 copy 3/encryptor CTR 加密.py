import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

def aes256_ctr_file_encrypt(
    source_dir=r"E:\无耻之徒字幕重置",
    encrypt_output_dir=r"E:\encryted",
    password="secp256k1",
    chunk_size=1024 * 1024 * 4,  # 4MB
    output_suffix=".enc"
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
    print(f"📌 AES-256-CTR 加密配置（流式加密，适合视频边读边解密）")
    print(f"   源目录：{os.path.abspath(source_dir)}")
    print(f"   输出目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   分块大小：{chunk_size // 1024 // 1024}MB | 输出后缀：{output_suffix}")
    print("   加密模式：AES-256-CTR | 密钥来源：密码 SHA-256 哈希")
    print("=" * 90 + "\n")

    def format_size(bytes_size):
        units = ['B', 'KB', 'MB', 'GB']
        unit_idx = 0
        while bytes_size >= 1024 and unit_idx < len(units)-1:
            bytes_size /= 1024
            unit_idx += 1
        return f"{bytes_size:.2f} {units[unit_idx]}"

    # 从密码生成 32 字节密钥
    def generate_key(password_str):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(password_str.encode('utf-8'))
        return digest.finalize()

    key = generate_key(password)

    try:
        for root, dirs, files in os.walk(source_dir):
            for file_name in files:
                total_count += 1
                file_abs_path = os.path.join(root, file_name)
                rel_dir = os.path.relpath(root, source_dir)
                encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
                os.makedirs(encrypt_subdir, exist_ok=True)
                output_enc_path = os.path.join(encrypt_subdir, file_name + output_suffix)
                nonce_path = output_enc_path + ".nonce"

                file_total_size = os.path.getsize(file_abs_path)
                if file_total_size == 0:
                    print(f"⚠️  跳过空文件 | 文件名：{file_name}")
                    continue

                try:
                    file_start_time = time.time()

                    # CTR 模式：通常 nonce 长度为 16 字节（和块大小相同）
                    # 这里用 16 字节随机 nonce，保存到 .nonce 文件
                    nonce = os.urandom(16)
                    with open(nonce_path, 'wb') as f:
                        f.write(nonce)

                    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                    encryptor = cipher.encryptor()

                    with open(file_abs_path, 'rb') as f_in, open(output_enc_path, 'wb') as f_out:
                        while True:
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            encrypted_chunk = encryptor.update(chunk)
                            f_out.write(encrypted_chunk)
                        # 收尾（CTR 一般没有 finalize 数据，但接口还是要调用）
                        f_out.write(encryptor.finalize())

                    file_elapsed_time = time.time() - file_start_time
                    file_avg_speed = file_total_size / file_elapsed_time / 1024 / 1024
                    file_size_str = format_size(file_total_size)

                    print(f"✅ 加密完成 | 文件名：{file_name} | 大小：{file_size_str} | 耗时：{file_elapsed_time:.2f}s | 平均速度：{file_avg_speed:.2f} MB/s | 保存至：{output_enc_path}")
                    success_count += 1

                except Exception as e:
                    print(f"❌ 加密失败 | 文件名：{file_name} | 错误信息：{str(e)}")
                    failed_files.append((file_name, str(e)))
                    continue

    except KeyboardInterrupt:
        print("\n\n⚠️  检测到强制退出，任务已中断")

    print("\n" + "=" * 90)
    print(f"🎉 AES-256-CTR 加密任务结束！ | 总文件数：{total_count} | 成功数：{success_count} | 失败数：{len(failed_files)}")
    print(f"💡 注意：解密时需要 密码 + 对应 .nonce 文件 | 输出目录：{os.path.abspath(encrypt_output_dir)}")
    print("=" * 90)
    return success_count > 0

if __name__ == "__main__":
    aes256_ctr_file_encrypt()