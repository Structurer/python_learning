import requests
requests.packages.urllib3.disable_warnings()

# 只改这1个API Key，其余全对
API_KEY = ""
# 正确模型名，固定死，别再改了
MODEL_NAME = "Doubao-1.5-Lite-32K"
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

def test_doubao():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,  # 这里是关键，已改正确
        "messages": [{"role": "user", "content": "你好，你是谁？"}],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }

    try:
        res = requests.post(API_URL, headers=headers, json=data, timeout=30, verify=False)
        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"]
            print("✅ 调用成功！")
            print("模型回复：", reply)
        else:
            print(f"❌ 状态码：{res.status_code}，详情：{res.text}")
    except Exception as e:
        print(f"❌ 异常：{str(e)}")

if __name__ == "__main__":
    test_doubao()