import json
import os
import sys
from getpass import getpass
from pathlib import Path

"""
导入01-reliable-call/deepseek_demo.py 中的 deepseek_provider 函数
导入01-reliable-call/retry_demo.py 中的 call_with_retry 函数
"""
CALL_EXAMPLES_DIR = (
    Path(__file__).resolve().parents[1] / "01-reliable-call"
)
sys.path.insert(0, str(CALL_EXAMPLES_DIR))

from deepseek_demo import deepseek_provider
from retry_demo import call_with_retry

# 解析模型返回的任务字符串，完成JSON解析和业务校验
def parse_task(content):
    """
    接收模型回复的字符串，完成JSON解析和业务校验（null会被解析为None）
    成功返回解析后的字典，失败抛出异常
    规则：
    1.整体必须是字典，包含title、exercise_count两个键
    2.title必须是非空白字符串
    3.exercise_count可为None或者必须为非负整数
    """
        # 解析JSON
    data = json.loads(content)

    # 校验规则
    if not isinstance(data, dict):
        raise ValueError("整体必须是字典")
    if 'title' not in data or not isinstance(data['title'],str) or not data['title'].strip():
        raise ValueError("title必须是非空白字符串")
    if 'exercise_count' not in data:
        raise ValueError("缺少 exercise_count")

    value = data['exercise_count']
    if value is not None and(type(value) is not int or value < 0):
        raise ValueError("exercise_count必须为None或者非负整数")

    return data

# 本地验证
content1 = '{"title": "数学练习", "exercise_count": 2}'     # 合法值，数量为2
content2 = '{"title": "数学练习", "exercise_count": null}'  # 合法值，数量为null
content3 = '{"title": "数学练习"}'                          # 缺字段
content4 = '{"title": "数学练习", "exercise_count": -1}'    # 坏字段值
content5 = '{"title": "数学练习", "exercise_count":}'       # 非法json

contents = [content1, content2, content3, content4, content5]

for c in contents:
    try:
        result = parse_task(c)
        print(f"解析成功: {result}")
    except Exception as e:
        print(f"解析失败: {type(e).__name__}: {e}")

# 为现有的deepseek_provider增加一个包装函数，返回原始响应字典
def task_provider(messages, api_key):
    response_format = {
        "type": "json_object",}
    # 调用DeepSeek接口，得到原始响应字典
    raw = deepseek_provider(
        messages,
        api_key,
        response_format=response_format
    )
    return raw

if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY") or getpass("DeepSeek API key: ")

    messages = [
        {
            "role": "system",
            "content": """
从用户输入中提取学习任务，只输出一个 JSON 对象。
必须包含：
- title：非空白字符串，保留任务含义。
- exercise_count：非负整数；用户未说明数量时填 null，不得猜测。

示例输入：复习排序，做3道题
示例输出：{"title": "复习排序", "exercise_count": 3}
""",
        },
        {"role": "user", "content": "复习二分查找"},
    ]

    raw = call_with_retry(task_provider, messages, api_key, base_delay=1.0)
    answer = raw["choices"][0]["message"]["content"]

    print("模型回答：", repr(answer))
    print("结束标记：", raw["choices"][0]["finish_reason"])

    # 解析模型回答
    task = parse_task(answer)
    print("校验后的任务：", task)

