import re
import pyperclip
import sys
import subprocess

# 定义需要过滤的关键词
FILTER_KEYWORDS = ['拍1', '拍2', '拍3', '[聊天记录]']

def extract_urls(text):
    # 检查整个文本是否包含特定关键词
    if any(keyword in copied_content for keyword in FILTER_KEYWORDS):
        print("检测到关键词，程序结束。")
        sys.exit()  # 如果包含关键词，则结束程序
    # 提取密码
    inputpassword = 'error'  # 初始化密码为 "error"
    password_pattern = r'密([a-zA-Z0-9]{6})'  # 只提取“密”后面的6个字符
    match = re.search(password_pattern, text)
    if match:
        inputpassword = match.group(1)  # 提取密码

    # 正则表达式匹配网址
    url_pattern = r'https?://[^\s]+|coupon.m.jd.com[^\s]+|http?://[^\s]+'
    urls = re.findall(url_pattern, text)

    # 处理每个 URL，去掉最后的多余部分（如果有的话）
    cleaned_urls = []
    for url in urls:
        if not url.startswith('https://') and not url.startswith('http://') and 'coupon.m.jd.com' in url:
            url = 'https://' + url
        # 只保留到最后一个斜杠之前的部分
        cleaned_url = re.sub(r'Adidas.*$', '', url)  # 去掉包含"Adidas"后面的部分
        cleaned_url = cleaned_url.rstrip('/')  # 去掉 URL 末尾的斜杠（如果有）
        cleaned_urls.append(cleaned_url)

    # 过滤 URL，确保没有重复项
    unique_urls = list(set(cleaned_urls))
    return inputpassword, unique_urls



# 获取剪贴板内容
copied_content = pyperclip.paste()
print("复制的内容:", copied_content)
# 提取网址
inputpassword, extracted_urls = extract_urls(copied_content)

# 打印提取到的网址
for url in extracted_urls:
    print(url)
    print(inputpassword)
    # 调用 Node.js 脚本处理复制的内容
    if 0:
        try:
            # 指定编码为 UTF-8
            result = subprocess.run(
                ["node", "auto_login.js", url, inputpassword],
                capture_output=True,
                text=True,
                encoding='utf-8',  # 确保以 UTF-8 编码读取输出
                timeout=2000  # 设置超时，防止长时间等待
            )
            
            # 打印 Node.js 的标准输出
            if result.stdout:
                print(result.stdout)
            else:
                print("Node.js 没有输出。")

            # 打印 Node.js 的错误输出
            if result.stderr:
                print("Node.js 错误输出:")
                print( result.stderr)

        except subprocess.TimeoutExpired:
            print("运行 Node.js 脚本超时。")
        except Exception as e:
            print("运行 Node.js 脚本时出错:", e)
    else:
        print("剪贴板中没有内容，请复制网址。")

