# 产生模拟响应
def fake_provider(messages,mode="ok"):
    if mode == "ok":
        user_content = messages[-1]["content"]
        return {"text": f"模拟回复：{user_content}"}
    elif(mode == "timeout"):
        raise TimeoutError("模拟超时错误")
    else:
        raise ValueError("未知的模式")

# 检查响应

# 模拟提供者
messages = [
    {"role": "system", "content": "请简要回答"},
    {"role": "user", "content": "什么是Agent？"}
]

try:
    response = fake_provider(messages, mode="ok")
    if response is not None:
        content = response["text"]
        print(content)
    else:
        print("没有收到回复")
except TimeoutError as e:
    print(f"请求超时: {e}")

try:
    response = fake_provider(messages, mode="timeout")
    print(response)
except TimeoutError as e:
    print(f"请求超时: {e}")

try:
    response = fake_provider(messages, mode="oks")
    print(response)
except ValueError as e:
    print(f"发生错误: {e}")