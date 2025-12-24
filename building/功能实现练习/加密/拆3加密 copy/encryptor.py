import os
import py7zr
import keyboard  # 需额外安装：pip install keyboard

def py7zr_recursive_single_file_encrypt(
    # ==============================================
    # 参数区域（可根据需求修改）
    source_dir=r"E:\temp",               # 默认源目录
    encrypt_output_dir=r"E:\encryted",   # 默认加密输出目录
    password="secp256k1",                # 默认密码
    encrypt_filename=True,               # 是否加密文件名（默认开启）
    pause_key='p'                        # 暂停/继续按键（默认p键）
    # ==============================================
):
    """递归单文件加密，支持暂停/继续功能"""
    total_count = 0
    success_count = 0
    failed_files = []
    is_paused = False  # 暂停状态标记

    # 目录创建
    for dir_path in [source_dir, encrypt_output_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    if not os.listdir(source_dir):
        print(f"❌ [错误] 源文件夹 {source_dir} 为空，请放入待加密文件")
        return False

    # 配置提示
    print("=" * 70)
    print(f"📌 加密配置信息（参数区域可直接修改）")
    print(f"   源文件目录：{os.path.abspath(source_dir)}")
    print(f"   加密包目录：{os.path.abspath(encrypt_output_dir)}")
    print(f"   文件名加密：{'✅ 开启' if encrypt_filename else '❌ 关闭'}")
    print(f"   暂停按键：'{pause_key}' 键（按此键暂停/继续）")
    print("=" * 70 + "\n")

    # 定义暂停回调函数
    def toggle_pause():
        nonlocal is_paused
        is_paused = not is_paused
        status = "暂停中" if is_paused else "继续运行"
        print(f"\n 加密任务已{status}（按 '{pause_key}' 切换）")

    # 注册暂停按键监听
    keyboard.add_hotkey(pause_key, toggle_pause)

    try:
        # 递归处理文件
        for root, dirs, files in os.walk(source_dir):
            for file_name in files:
                # 检查暂停状态
                while is_paused:
                    pass

                total_count += 1
                file_abs_path = os.path.join(root, file_name)
                rel_dir = os.path.relpath(root, source_dir)

                # 构建输出路径
                encrypt_subdir = os.path.join(encrypt_output_dir, rel_dir)
                os.makedirs(encrypt_subdir, exist_ok=True)
                output_7z_path = os.path.join(encrypt_subdir, f"{file_name}.7z")

                try:
                    with py7zr.SevenZipFile(output_7z_path, 'w', password=password) as archive:
                        if encrypt_filename:
                            try:
                                archive.set_encrypted_header(True)
                            except Exception:
                                print(f"⚠️  {file_name} - 当前版本不支持文件名加密，仅加密内容")
                        archive.write(file_abs_path, arcname=file_name)
                    print(f"✅ 加密完成 | {file_abs_path} → {output_7z_path}")
                    success_count += 1
                except Exception as e:
                    print(f"❌ 加密失败 | {file_abs_path} → 错误：{str(e)}")
                    failed_files.append(file_abs_path)
                    continue

    except KeyboardInterrupt:
        print("\n⚠️ 检测到强制退出，任务已中断")
    finally:
        keyboard.unhook_all_hotkeys()  # 移除监听

    # 执行结果
    print("=" * 70)
    print(f"🎉 加密任务结束！")
    print(f"📊 统计：总文件数={total_count}，成功={success_count}，失败={len(failed_files)}")
    print(f"💡 加密文件位置：{os.path.abspath(encrypt_output_dir)}")
    if failed_files:
        print("\n❌ 失败文件列表：")
        for idx, path in enumerate(failed_files, 1):
            print(f"   {idx}. {path}")
    print("=" * 70)
    return True if success_count > 0 else False

# 直接运行时使用参数区域的默认配置
if __name__ == "__main__":
    py7zr_recursive_single_file_encrypt()

    # 如需临时修改参数，可在调用时传入，例如：
    # py7zr_recursive_single_file_encrypt(
    #     source_dir=r"E:\my_files",
    #     password="my_new_password"
    # )