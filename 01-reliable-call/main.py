from urllib.request import Request, urlopen
import json
from time import perf_counter

# HTTP提供者
def http_provider(messages, url,timeout=3.0):
    # 检查消息
    validate_messages(messages)

    text = json.dumps({"messages": messages}, ensure_ascii=False)
    body = text.encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        response_text = response.read().decode("utf-8")
        return json.loads(response_text)


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

# 检查消息
def validate_messages(messages):
    if not isinstance(messages, list):
        raise ValueError("消息列表不是列表类型")
    if len(messages) == 0:
        raise ValueError("消息列表为空")
    for me in messages:
        if not isinstance(me, dict):
            raise ValueError("消息不是字典类型")
        if "role" not in me or "content" not in me:
            raise ValueError("消息缺少 role 或 content 字段")
        if not isinstance(me["role"], str) or not isinstance(me["content"], str):
            raise ValueError("消息的 role 或 content 字段不是字符串类型")
        if me["content"].strip() == "":
            raise ValueError("消息的 content 字段为空字符串")
        if me["role"] not in ["system", "user", "assistant"]:
            raise ValueError("消息的 role 字段不是有效值")
    return messages

# 模拟提供者
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "请简要回答"},
        {"role": "user", "content": "什么是Agent？"}
    ]

    # 测试消息验证（合法消息）
    try:
        valid_messages = validate_messages(messages)
        print("消息验证通过")
    except ValueError as e:
        print(f"消息验证失败: {e}")

    # 测试消息验证（非法消息）
    invalid_messages = [
        {"role": "system", "content": "请简要回答"},
        {"role": "user", "content": ""}  # 空内容
    ]

    try:
        valid_messages = validate_messages(invalid_messages)
        print("消息验证通过")
    except ValueError as e:
        print(f"消息验证失败: {e}")

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

    # HTTP对照：正常、等待超时、允许慢响应、响应内容不合格
    http_cases = [
        ("generate", 3.0),
        ("slow", 0.5),
        ("slow", 3.0),
        ("bad-response", 3.0),
    ]

    for path, timeout in http_cases:
        start = perf_counter()
        stage = "HTTP调用"
        try:
            url = f"http://127.0.0.1:8765/{path}"
            response = http_provider(messages, url, timeout=timeout)
            stage = "响应校验"
            content = validate_response(response)
            print(f"/{path} timeout={timeout}s 成功: {content}")
        except Exception as e:
            print(f"/{path} timeout={timeout}s {stage}失败: {type(e).__name__}: {e}")
        finally:
            elapsed = perf_counter() - start
            print(f"耗时: {elapsed:.3f} 秒")
