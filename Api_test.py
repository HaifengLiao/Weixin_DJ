import pyperclip
import requests
from typing import List, Optional, Dict, Any

# 内置示例文本
EXAMPLE_TEXT = """20点抢李宁1000-250
21点/22点/23点 提前四五秒放
https://coupon.m.jd.com/coupons/show.action?linkKey=AAROH_xIpeffAs_-naABEFoeY8Gt8bWOLkz98mz0C_AAPGI-nE-ZeMx7_-WQxMwC0Qn8TyoItPZ8NKQ9aPDAjVnn_Hmplg
领400券
[玫瑰] https://coupon.m.jd.com/coupons/show.action?linkKey=AAROH_xIpeffAs_-naABEFoemKFrdEEQFr-dMPUMfclN3hOEgRRTP2yNHSYxMV98RmZfTlt4WKXPrLqmaleHvYX03WWZag"""

API_URL = "http://192.168.3.70:3000/api/receive"
TOKEN = "your_token_here"   # 请替换为实际token
ACCOUNT_IDS = ["2", "5"]          # 固定对账号5操作

def claim_coupons(
    text: str,
    account_ids: Optional[List[str]] = None,
    api_url: str = API_URL,
    token: Optional[str] = None
) -> Dict[str, Any]:
    if account_ids is None:
        account_ids = ['1', '2', '3', '4', '5']
    payload = {
        "link": text,
        "accountIds": account_ids
    }
    if token:
        payload["token"] = token
    try:
        resp = requests.post(api_url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("📋 使用内置示例文本")
    result = claim_coupons(
        text=EXAMPLE_TEXT,
        account_ids=ACCOUNT_IDS,
        api_url=API_URL,
        token=TOKEN
    )
    print(result)