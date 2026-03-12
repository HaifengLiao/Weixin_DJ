import lark_oapi as lark
from lark_oapi.api.im.v1 import *
import time
import json
import requests
import re
from datetime import datetime, timedelta
import subprocess
from threading import Thread
# 定义需要过滤的关键词
# 替换为你的 Webhook 地址
def send_webhook(message):
    WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/33d62460-9e00-475f-80d0-37be8f40acef"
    # 构造消息体
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    
    # 发送 POST 请求
    response = requests.post(WEBHOOK_URL, json=data)
    
    # 检查响应
    if response.status_code == 200:
        print("消息发送成功")
    else:
        print(f"消息发送失败: {response.status_code}, {response.text}")

FILTER_KEYWORDS = ['拍1', '拍2', '拍3', '拍4', '拍5', '[聊天记录]','JORDAN','专卖店','淘宝','.tb.cn','.Tb.cn']
def run_node_script(url, inputpassword, timestamp):
    try:
        start_time = time.time()
        result = subprocess.run(
            ["node", "auto_login_flybook.js", url, inputpassword],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        end_time = time.time()
        duration = end_time - start_time
        if result.stdout:
            modified_output = result.stdout.replace("领取成功！感谢您的参与，祝您购物愉快~", "领取成功")
            message_with_time = f"{duration:.1f}s to{timestamp}\n {modified_output}"
            print(message_with_time)
            # 发送Webhook（如果需要）
            send_webhook(message_with_time)
    except Exception as e:
        print(f"执行Node.js脚本错误: {e}")

def extract_urls(text):
    # 检查整个文本是否包含特定关键词
    if any(keyword in text for keyword in FILTER_KEYWORDS):
        print("检测到过滤关键词，跳过处理。")
        return 'error', -1
    inputpassword = 'error'  # 初始化密码为 "error"
    password_pattern = r'密\s*([a-zA-Z0-9\s]{6})'  # 支持空格并提取6个字符
    match = re.search(password_pattern, text)
    if match:
        inputpassword = match.group(1).replace(" ", "")  # 提取密码并去掉空格
    print(f"提取的密码: {inputpassword}")

    # 正则表达式匹配网址
    url_pattern = r'https?://[^\s]+|coupon.m.jd.com[^\s]+'
    urls = re.findall(url_pattern, text)

    # 处理每个 URL
    cleaned_urls = []
    for url in urls:
        if not url.startswith('https://') and not url.startswith('http://') and 'coupon.m.jd.com' in url:
            url = 'https://' + url
        # 清理URL
        cleaned_url = re.sub(r'Adidas.*$', '', url)  # 去掉包含"Adidas"后面的部分
        cleaned_url = cleaned_url.rstrip('/')  # 去掉 URL 末尾的斜杠
        cleaned_urls.append(cleaned_url)

    # 过滤 URL，确保没有重复项
    unique_urls = list(set(cleaned_urls))
    return inputpassword, unique_urls


# 注册接收消息事件，处理接收到的消息。
# Register event handler to handle received messages.
# https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/events/receive
def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    res_content = ""
    if data.event.message.message_type == "text":
        res_content = json.loads(data.event.message.content)["text"]
    else:
        res_content = "解析消息失败，请发送文本消息\nparse message failed, please send text message"
    print(f"收到消息: \n{res_content}\n")
    inputpassword, extracted_urls = extract_urls(res_content)
    for url in extracted_urls:
        if url:
            timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
            # 异步执行Node.js脚本
            Thread(target=run_node_script, args=(url, inputpassword, timestamp)).start()
    
        

# 注册事件回调
# Register event handler.
event_handler = (
    lark.EventDispatcherHandler.builder("", "")
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1)
    .build()
)


# 创建 LarkClient 对象，用于请求OpenAPI, 并创建 LarkWSClient 对象，用于使用长连接接收事件。
# Create LarkClient object for requesting OpenAPI, and create LarkWSClient object for receiving events using long connection.
client = lark.Client.builder().app_id(lark.APP_ID).app_secret(lark.APP_SECRET).build()
wsClient = lark.ws.Client(
   "cli_a87c4a021ba7d00d",
   "RpVHzJEGnFkMLjxAumkpkb43GRGBNLky",
    event_handler=event_handler,
    log_level=lark.LogLevel.DEBUG,
)


def main():
    #  启动长连接，并注册事件处理器。
    #  Start long connection and register event handler.
    wsClient.start()


if __name__ == "__main__":
    main()
