import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes

def aes256_file_batch_decrypt(
    source_enc_dir=r"E:\encryted\无耻之徒S03.Shameless.US.2013.1080p.Blu-ray.x265.AC3￡cXcY@FRDS",    # 加密文件所在目录
    decrypt_output_dir=r"E:\decrypted", # 解密输出目录
    password="secp256k1",             # 与加密一致的密码
    chunk_size=1024 * 1024 * 4,       # 4MB 分块，与加密保持一致
    enc_suffix=".enc"                 # 加密文件后缀
):
    total_count = 0
    success_count = 0
    failed_files = []

    # 创建输出目录
    os.makedirs(decrypt_output_dir, exist_ok=True)
    
    if not os.listdir(source_enc_dir):
        print(f"❌ 加密文件目录 {source_enc_dir} 为空")
        return False

    # 配置提示
    print("=" * 90)
    print(f"📌 AES-256 批量解密配置")
    print(f"   加密文件目录：{os.path.abspath(source_enc_dir)}")
    print(f"   解密输出目录：{os.path.abspath(decrypt_output_dir)}")
    print(f"   分块大小：{chunk_size // 1024 // 1024}MB | 加密文件后缀：{enc_suffix}")
    print(f"   解密模式：AES-256-CBC | 密钥来源：密码 SHA-256 哈希")
    print("=" * 90 + "\n")

    # 格式化文件大小
    def format_size(bytes_size):
        units = ['B', 'KB', 'MB', 'GB']
        unit_idx = 0
        while bytes_size >= 1024 and unit_idx < len(units)-1:
            bytes_size /= 1024
            unit_idx += 1
        return f"{bytes_size:.2f} {units[unit_idx]}"

    # 生成 AES-256 密钥（与加密逻辑一致）
    def generate_key(password_str):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(password_str.encode('utf-8'))
        return digest.finalize()  # 32 字节密钥

    key = generate_key(password)

    try:
        # 递归遍历加密目录下的所有 .enc 文件
        for root, dirs, files in os.walk(source_enc_dir):
            for file_name in files:
                # 只处理 .enc 后缀的加密文件
                if not file_name.endswith(enc_suffix):
                    continue

                total_count += 1
                enc_file_abs_path = os.path.join(root, file_name)
                # 匹配对应的 .iv 文件（加密时生成的）
                iv_file_path = enc_file_abs_path + ".iv"
                if not os.path.exists(iv_file_path):
                    print(f"❌ 解密失败 | 文件名：{file_name} | 错误：缺少配套 IV 文件 {iv_file_path}")
                    failed_files.append((file_name, "缺少IV文件"))
                    continue

                # 构建解密后文件路径（去掉 .enc 后缀，保持原目录结构）
                rel_dir = os.path.relpath(root, source_enc_dir)
                output_subdir = os.path.join(decrypt_output_dir, rel_dir)
                os.makedirs(output_subdir, exist_ok=True)
                decrypted_file_name = file_name[:-len(enc_suffix)]  # 去掉 .enc 后缀
                output_file_path = os.path.join(output_subdir, decrypted_file_name)

                # 获取加密文件大小
                enc_file_size = os.path.getsize(enc_file_abs_path)

                try:
                    # 记录单个文件解密开始时间
                    file_start_time = time.time()

                    # 读取 IV 向量
                    with open(iv_file_path, 'rb') as iv_f:
                        iv = iv_f.read()
                    if len(iv) != 16:
                        raise ValueError(f"IV 文件长度错误，必须为16字节")

                    # 初始化 AES-256 CBC 解密器
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    decryptor = cipher.decryptor()
                    unpadder = padding.PKCS7(128).unpadder()  # 对应加密时的填充方式

                    # 分块解密
                    with open(enc_file_abs_path, 'rb') as f_in, open(output_file_path, 'wb') as f_out:
                        while True:
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            # 解密 + 去填充
                            decrypted_chunk = decryptor.update(chunk)
                            unpadded_chunk = unpadder.update(decrypted_chunk)
                            f_out.write(unpadded_chunk)
                        # 处理最后一块的剩余数据
                        f_out.write(unpadder.finalize())
                        f_out.write(decryptor.finalize())

                    # 计算解密耗时和速度
                    file_elapsed_time = time.time() - file_start_time
                    # 速度按加密文件大小计算（与原文件大小接近）
                    file_avg_speed = enc_file_size / file_elapsed_time / 1024 / 1024
                    file_size_str = format_size(enc_file_size)

                    # 即时输出单文件解密结果
                    print(f"✅ 解密完成 | 文件名：{decrypted_file_name} | 大小：{file_size_str} | 耗时：{file_elapsed_time:.2f}s | 平均速度：{file_avg_speed:.2f} MB/s | 保存至：{output_file_path}")
                    success_count += 1

                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ 解密失败 | 文件名：{file_name} | 错误信息：{error_msg}")
                    failed_files.append((file_name, error_msg))
                    continue

    except KeyboardInterrupt:
        print("\n\n⚠️  检测到强制退出，解密任务已中断")

    # 最终统计
    print("\n" + "=" * 90)
    print(f"🎉 AES-256 批量解密任务结束！ | 总加密文件数：{total_count} | 成功数：{success_count} | 失败数：{len(failed_files)}")
    print(f"💡 解密文件存放位置：{os.path.abspath(decrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件列表：")
        for idx, (name, err) in enumerate(failed_files, 1):
            print(f"   {idx}. {name} | 错误：{err}")
    print("=" * 90)
    return success_count > 0

if __name__ == "__main__":
    # 执行批量解密
    aes256_file_batch_decrypt()

    # 如需自定义参数，可修改调用方式：
    # aes256_file_batch_decrypt(
    #     source_enc_dir=r"你的加密文件目录",
    #     decrypt_output_dir=r"你的解密输出目录",
    #     password="你的加密密码",
    #     chunk_size=8*1024*1024  # 8MB 分块
    # )