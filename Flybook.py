import requests
import json


def send_message_to_feishu(content):
    # 构造消息体
    data = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    # 替换为你的 Webhook 地址
    
    WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/183e96f4-7662-49d5-9e27-852451cf1969"

    # 发送 POST 请求
    response = requests.post(WEBHOOK_URL, json=data)
    
    # 检查响应
    if response.status_code == 200:
        print("消息发送成功")
    else:
        print(f"消息发送失败: {response.status_code}, {response.text}")


if __name__ == "__main__":
    message = "这是从自定义服务推送的消息！"
    send_message_to_feishu(message)

