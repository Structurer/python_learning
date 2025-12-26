import pyautogui
import pyperclip
import time

# ===================== 核心配置（改这2处就行） =====================
BTN_IMG_PATH = r"./copy_btn.png"  # 你的复制按钮截图路径（和代码同文件夹直接写文件名）
CLICK_DELAY = 0.8  # 点击后等待复制到剪贴板的时间（0.5-1秒足够）
CONFIDENCE = 0.8   # 匹配相似度（0.8=80%相似就识别，不用100%，适配轻微样式变化）
# ==================================================================

def click_btn_by_img():
    try:
        # 1. 图像识别定位按钮位置（返回按钮中心坐标）
        print(f"🔍 正在屏幕上识别按钮截图 {BTN_IMG_PATH}...")
        # 开启灰度匹配，提速+提高兼容性；confidence设置相似度，避免识别失败
        btn_pos = pyautogui.locateCenterOnScreen(
            BTN_IMG_PATH,
            confidence=CONFIDENCE,
            grayscale=True
        )
        
        if not btn_pos:
            print("❌ 未识别到按钮！请检查：1.按钮是否在屏幕可见 2.截图是否准确 3.相似度是否过低")
            return False
        
        # 2. 鼠标移动到按钮中心+点击（模拟真人点击，更稳定）
        pyautogui.moveTo(btn_pos, duration=0.3)  # 鼠标缓慢移动过去（duration=移动耗时，可选）
        pyautogui.click(btn_pos)  # 左键点击按钮
        print(f"✅ 按钮识别成功！坐标：{btn_pos}，已点击1次")
        time.sleep(CLICK_DELAY)  # 必加延迟，给网页复制到剪贴板的时间
        
        # 3. 读取剪贴板内容并终端打印
        clip_content = pyperclip.paste()
        print("\n📋 剪贴板复制的内容：")
        print("-" * 50)
        print(clip_content if clip_content else "⚠️ 剪贴板为空（可能点击位置偏差/按钮没触发复制）")
        print("-" * 50)
        return True
    
    except Exception as e:
        print(f"❌ 运行出错：{str(e)}")
        return False

# 执行主函数
if __name__ == "__main__":
    click_btn_by_img()