import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time
import datetime

# ===================== 已填好你的配置 仅补授权码即可用 =====================
# 1. 163发件邮箱配置（已修正格式错误，仅补授权码）
SEND_EMAIL = "tempceshi@163.com"  # 修正多的小数点，已填好你的邮箱
SEND_SMTP_SERVER = "smtp.163.com"   # 163固定不变，不用改
SEND_SMTP_PWD = "BPtZs8ggaD7LehSs"  # 只需要填你163邮箱获取的16位SMTP授权码，填这里就行

# 2. CF收件中转触发邮箱（已完整填好你的邮箱）
CF_TRIGGER_EMAIL = "dingo12345@ceshi.autos"  # 你的CF中转触发邮箱，直接用

# 3. 核心发送规则（秒级间隔，直接调数字就行）
TOTAL_SEND_TIMES = 10  # 总发送次数，想改直接调数字（推荐10-30封）
SEND_INTERVAL_SEC = 10  # 间隔秒数，默认60秒=1分钟，调数字就改间隔，简单直接
# ===============================================================================

def send_single_test_mail(send_idx):
    mail_content = f"""CF收件中转连续测试邮件（第{send_idx+1}/{TOTAL_SEND_TIMES}封）
发送时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
发送规则：每隔{SEND_INTERVAL_SEC}秒发送1封，共发送{TOTAL_SEND_TIMES}封
CF触发中转邮箱：{CF_TRIGGER_EMAIL}"""
    try:
        msg = MIMEText(mail_content, "plain", "utf-8")
        # ========== 终极修正信头（全163合规，删所有自定义，只留必要字段）==========
        msg["From"] = SEND_EMAIL  # 1. 彻底删掉Header，直接填纯发件邮箱，163强制认可
        msg["To"] = CF_TRIGGER_EMAIL  # 2. 同样纯邮箱，不加任何修饰
        msg["Subject"] = f"CF中转测试{send_idx+1}"  # 3. 主题极简，无特殊符号（避免误判）
        msg["Date"] = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')  # 4. 加标准时间头，补全163要求的信头
        # ===========================================================================

        with smtplib.SMTP_SSL(SEND_SMTP_SERVER, 465) as server:
            server.login(SEND_EMAIL, SEND_SMTP_PWD)
            # 关键：发送时指定from_addr和to_addrs，和信头完全一致，双重校验合规
            server.sendmail(from_addr=SEND_EMAIL, to_addrs=[CF_TRIGGER_EMAIL], msg=msg.as_string())
        print(f"✅ 第{send_idx+1}封发送成功 | 发送时间：{time.strftime('%H:%M:%S')} | 下次间隔{SEND_INTERVAL_SEC}秒")
    except Exception as e:
        print(f"❌ 第{send_idx+1}封发送失败 | 错误：{str(e)}")

def continuous_send_task():
    """核心功能：按秒级间隔连续发送，发完总次数自动结束，无多余操作"""
    print("="*70)
    print(f"🚀 CF收件中转 秒级间隔连续发送任务启动")
    print(f"📤 发件邮箱：{SEND_EMAIL} | 🎯 CF中转触发邮箱：{CF_TRIGGER_EMAIL}")
    print(f"📊 发送规则：总{TOTAL_SEND_TIMES}封 | 每隔{SEND_INTERVAL_SEC}秒发送1封")
    print(f"⏰ 任务启动时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 循环发送，最后1封发完直接结束，非最后1封发送后等待指定秒数
    for i in range(TOTAL_SEND_TIMES):
        send_single_test_mail(i)
        if i != TOTAL_SEND_TIMES - 1:
            time.sleep(SEND_INTERVAL_SEC)

    print("="*70)
    print(f"🎉 全部{TOTAL_SEND_TIMES}封测试邮件发送完成！")
    print(f"💡 核对方法：到你的中转接收邮箱，搜索关键词【CF收件中转连续测试】查看接收情况")

if __name__ == "__main__":
    continuous_send_task()