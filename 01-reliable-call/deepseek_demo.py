"""DeepSeek首次调用实验：发送鉴权请求并提取回答与用量。

参考：https://api-docs.deepseek.com/api/create-chat-completion/
密钥从进程环境或本机隐藏输入读取。
"""

# json.dumps() ：Python对象转为JSON字符串
# json.loads() ：JSON字符串转为Python对象
# json.dump() ：Python对象转为JSON字符串并写入文件
# json.load() ：从文件读取JSON字符串并转为Python对象
# urlopen() ：发送HTTP请求并返回响应对象

import json
import os
from getpass import getpass
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from main import validate_messages, validate_response

from retry_demo import call_with_retry

def deepseek_provider(messages, api_key, model="deepseek-flash", timeout=30.0):
    """发送非流式请求，返回解析后的原始响应字典。"""

    validate_messages(messages)
    body = json.dumps({"model": model,
                       "messages": messages,
                       "stream": False,
                       "thinking": {"type": "disabled"},
                       "max_tokens": 128,
                       })
    request = Request(
        url="https://api.deepseek.com/chat/completions",
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY") or getpass("DeepSeek API key: ")
    if not api_key.strip():
        raise ValueError("缺少DeepSeek API key")

    messages = [
        {"role": "system", "content": "请简短回答。"},
        {"role": "user", "content": "只回复：连接成功。"},
    ]
    raw = call_with_retry(deepseek_provider, messages, api_key,base_delay=1.0)

    answer = raw["choices"][0]["message"]["content"]
    text = {"text": answer}
    validate_response(text)
    print(f"回答: {answer}")
    print(f"结束标记: {raw['choices'][0]['finish_reason']}")
    print(f"Usage: {raw['usage']}")

    # 失败实验
    try:
        call_with_retry(deepseek_provider, messages, "invalid-key-for-test", base_delay=1.0)
    except HTTPError as e:
        print(f"鉴权实验：HTTP{e.code}")
