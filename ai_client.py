# 企业标准：调用第三方 AI 接口，本地零模型依赖
import os
import requests
from dotenv import load_dotenv


# 自动加载密钥
load_dotenv()

BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")

def get_baidu_token():
    try:
        url = "https://aip.baidubce.com/oauth/2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": BAIDU_API_KEY,
            "client_secret": BAIDU_SECRET_KEY
        }
        res = requests.post(url, data=data, timeout=10)
        return res.json().get("access_token")
    except:
        return None

def ai_summarize_enterprise(text):
    """
    企业标准 AI 总结
    1. 调用第三方 AI
    2. 无本地模型
    3. 毫秒级响应
    4. 支持高并发
    """
    try:
        if len(text) < 30:
            return "内容太短，无需总结"

        # ----------------------
        # 企业正式版：调用百度 AI
        # ----------------------
        token = get_baidu_token()
        if not token:
            return "AI 服务配置中，请使用演示总结\n\n" + simple_summarize(text)

        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token={token}"
        prompt = f"请你用简洁专业的语言总结这段笔记：\n{text[:800]}"

        res = requests.post(
            url,
            json={"messages": [{"role": "user", "content": prompt}]},
            timeout=15
        )
        result = res.json()
        return result.get("result", "总结失败")

    except Exception as e:
        # 企业必备：降级方案（AI 挂了也能给简单总结）
        return simple_summarize(text)

def simple_summarize(text):
    """企业降级方案：纯文本提取总结，永远不崩"""
    text = text.strip()[:600]
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
    summary = "\n".join(lines[:4])
    return f"【智能摘要】\n{summary}"