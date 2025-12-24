import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

def aes256_ctr_file_batch_decrypt(
    source_enc_dir=r"E:\encryted",
    decrypt_output_dir=r"E:\decrypted",
    password="secp256k1",
    chunk_size=1024 * 1024 * 4,
    enc_suffix=".enc"
):
    total_count = 0
    success_count = 0
    failed_files = []

    os.makedirs(decrypt_output_dir, exist_ok=True)

    if not os.listdir(source_enc_dir):
        print(f"❌ 加密文件目录 {source_enc_dir} 为空")
        return False

    print("=" * 90)
    print(f"📌 AES-256-CTR 批量解密配置")
    print(f"   加密文件目录：{os.path.abspath(source_enc_dir)}")
    print(f"   解密输出目录：{os.path.abspath(decrypt_output_dir)}")
    print(f"   分块大小：{chunk_size // 1024 // 1024}MB | 加密文件后缀：{enc_suffix}")
    print("   解密模式：AES-256-CTR | 密钥来源：密码 SHA-256 哈希")
    print("=" * 90 + "\n")

    def format_size(bytes_size):
        units = ['B', 'KB', 'MB', 'GB']
        unit_idx = 0
        while bytes_size >= 1024 and unit_idx < len(units)-1:
            bytes_size /= 1024
            unit_idx += 1
        return f"{bytes_size:.2f} {units[unit_idx]}"

    def generate_key(password_str):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(password_str.encode('utf-8'))
        return digest.finalize()

    key = generate_key(password)

    try:
        for root, dirs, files in os.walk(source_enc_dir):
            for file_name in files:
                if not file_name.endswith(enc_suffix):
                    continue

                total_count += 1
                enc_file_abs_path = os.path.join(root, file_name)
                nonce_path = enc_file_abs_path + ".nonce"

                if not os.path.exists(nonce_path):
                    print(f"❌ 解密失败 | 文件名：{file_name} | 错误：缺少配套 nonce 文件 {nonce_path}")
                    failed_files.append((file_name, "缺少 nonce 文件"))
                    continue

                rel_dir = os.path.relpath(root, source_enc_dir)
                output_subdir = os.path.join(decrypt_output_dir, rel_dir)
                os.makedirs(output_subdir, exist_ok=True)
                decrypted_file_name = file_name[:-len(enc_suffix)]
                output_file_path = os.path.join(output_subdir, decrypted_file_name)

                enc_file_size = os.path.getsize(enc_file_abs_path)

                try:
                    file_start_time = time.time()

                    with open(nonce_path, 'rb') as f:
                        nonce = f.read()
                    if len(nonce) != 16:
                        raise ValueError(f"nonce 长度错误，必须为 16 字节，当前为 {len(nonce)} 字节")

                    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                    decryptor = cipher.decryptor()

                    with open(enc_file_abs_path, 'rb') as f_in, open(output_file_path, 'wb') as f_out:
                        while True:
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            decrypted_chunk = decryptor.update(chunk)
                            f_out.write(decrypted_chunk)
                        f_out.write(decryptor.finalize())

                    file_elapsed_time = time.time() - file_start_time
                    file_avg_speed = enc_file_size / file_elapsed_time / 1024 / 1024
                    file_size_str = format_size(enc_file_size)

                    print(f"✅ 解密完成 | 文件名：{decrypted_file_name} | 大小：{file_size_str} | 耗时：{file_elapsed_time:.2f}s | 平均速度：{file_avg_speed:.2f} MB/s | 保存至：{output_file_path}")
                    success_count += 1

                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ 解密失败 | 文件名：{file_name} | 错误信息：{error_msg}")
                    failed_files.append((file_name, error_msg))
                    continue

    except KeyboardInterrupt:
        print("\n\n⚠️  检测到强制退出，解密任务已中断")

    print("\n" + "=" * 90)
    print(f"🎉 AES-256-CTR 批量解密任务结束！ | 总加密文件数：{total_count} | 成功数：{success_count} | 失败数：{len(failed_files)}")
    print(f"💡 解密文件存放位置：{os.path.abspath(decrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件列表：")
        for idx, (name, err) in enumerate(failed_files, 1):
            print(f"   {idx}. {name} | 错误：{err}")
    print("=" * 90)
    return success_count > 0

if __name__ == "__main__":
    aes256_ctr_file_batch_decrypt()