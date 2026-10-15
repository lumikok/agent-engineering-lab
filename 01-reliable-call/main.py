# 产生模拟响应
def fake_provider(messages,mode="ok"):
    if mode == "ok":
        user_content = messages[-1]["content"]
        return {"text": f"模拟回复：{user_content}"}
    elif(mode == "timeout"):
        raise TimeoutError("模拟超时错误")
    elif mode == "bad_response":
        return {"text": 123}  # 错误的响应类型
    else:
        raise ValueError("未知的模式")

# 检查响应
def validate_response(response):
    if not isinstance(response, dict):
        raise ValueError("响应不是字典类型")
    if "text" not in response:
        raise ValueError("响应缺少 text 字段")
    content = response["text"]
    if not isinstance(content, str):
        raise ValueError("响应的 text 字段不是字符串类型")
    if content.strip() == "":
        raise ValueError("响应的 text 字段为空字符串")
    return content

# 模拟提供者
messages = [
    {"role": "system", "content": "请简要回答"},
    {"role": "user", "content": "什么是Agent？"}
]

# 测试超时错误
try:
    response = fake_provider(messages, mode="timeout")
    content = validate_response(response)
    print(content)
except TimeoutError as e:
    print(f"请求超时: {e}")

# 测试未知模式错误
try:
    response = fake_provider(messages, mode="oks")
    content = validate_response(response)
    print(content)
except ValueError as e:
    print(f"发生错误: {e}")

# 测试合法的响应
try:
    response = fake_provider(messages, mode="ok")
    content = validate_response(response)
    print(content)
except ValueError as e:
    print(f"发生错误: {e}")

# 测试响应不是字典类型
try:
    response = "这是一个字符串响应"
    content = validate_response(response)
    print(content)
except ValueError as e:
    print(f"发生错误: {e}")

# 测试响应缺少 text 字段
try:
    response = {"message": "这是一个响应"}
    content = validate_response(response)
    print(content)
except ValueError as e:
    print(f"发生错误: {e}")

# 测试bad_response模式
try:
    response = fake_provider(messages, mode="bad_response")
    content = validate_response(response)
    print(content)
except ValueError as e:
    print(f"发生错误: {e}")