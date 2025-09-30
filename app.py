# v2 增加系统身份

from wxauto import WeChat
import re
import db
import requests
import json
import config
import time


# ---------------- 配置 ----------------
API_KEY = config.API_KEY
API_URL = config.API_URL
MODEL = config.MODEL
CHECK_INTERVAL = config.CHECK_INTERVAL
# --------------------------------------


# 初始化微信和数据库
wx = WeChat()
db.create_db()

def clean_response(content: str) -> str:
    """清理AI输出中的格式标记"""
    content = re.sub(r'\[.*?\]', '', content, flags=re.DOTALL)
    content = re.sub(r'\*\*\*', '', content)
    content = re.sub(r'\*\*', '', content)
    content = re.sub(r'\*', '', content)
    content = re.sub(r'^\t*[#-]+', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n+', '\n', content)
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    return content.strip()

def chat(user: str, prompt: str) -> str:
    """调用云端模型生成回复"""
    db.add_history(user, "user", prompt)
    messages = db.get_history(user)
    file = open("prompt/chaojia.txt","r",encoding="utf-8")

    # 如果是第一次聊天（上下文中没有 system），加入 system 提示
    if not any(msg['role'] == 'system' for msg in messages):
        system_prompt = {
            "role": "system",
            "content": (
                file.read()
            )
        }
        messages.insert(0, system_prompt)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "stream": False
    }

    try:
        resp = requests.post(API_URL, headers=headers, data=json.dumps(data))
        if resp.status_code != 200:
            return f"请求失败: {resp.status_code}"
        content = resp.json()["choices"][0]["message"]["content"]
        content = clean_response(content)
        db.add_history(user, "assistant", content)
        return content
    except Exception as e:
        return f"调用出错: {e}"

def main_loop(friend_names):
    """监听并回复来自多个好友的消息"""
    last_handled = {}  # 使用字典为每个好友记录最后处理的消息

    while True:
        for friend_name in friend_names:
            wx.ChatWith(friend_name)
            msgs = wx.GetAllMessage()
            if not msgs:
                continue

            last_msg = msgs[-1]

            # 忽略自己发送的消息，避免自我回复
            if last_msg.sender == "self":
                continue

            # 避免重复处理同一条消息
            if last_handled.get(friend_name) == last_msg:
                continue
            
            last_handled[friend_name] = last_msg

            print(f"收到来自 {friend_name} 的消息: {last_msg.content}")

            # 调用 AI 回复
            reply = chat(friend_name, last_msg.content)
            wx.SendMsg(reply)
            print(f"已向 {friend_name} 回复: {reply}")
        
        # 在检查完所有好友后等待一段时间
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 从配置中获取要聊天的联系人列表
    friend_list = config.CONTACT_NAMES
    if not isinstance(friend_list, list):
        print("错误: config.py 中的 CONTACT_NAMES 应该是一个列表。")
    else:
        print(f"开始监听 {len(friend_list)} 位好友的消息: {', '.join(friend_list)}")
        main_loop(friend_list)