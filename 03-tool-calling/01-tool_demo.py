"""工具调用实验
本地题库只读查询工具调用
"""
import json
import os
import sys
from getpass import getpass
from pathlib import Path

CALL_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "01-reliable-call"
sys.path.insert(0, str(CALL_EXAMPLES_DIR))

from deepseek_demo import deepseek_provider
from retry_demo import call_with_retry

# 自造示例数据
EXERCISE_BANK = {
    "二分查找": ["查找目标位置", "寻找左边界", "二分答案入门"],
    "排序": ["成绩排序", "合并有序数组"],
}

# tool-function -> 根据主题获取题目列表
def get_exercise_list(topic,limit=None):
    """根据主题获取题目列表"""
    if not isinstance(topic, str):
        raise ValueError("主题必须是字符串类型")
    if topic is None or topic.strip() == "":
        raise ValueError("主题不能为空")
    # 去掉首尾空白（防止用户输入时不小心加了空格，导致无法对应）
    topic = topic.strip()
    if topic not in EXERCISE_BANK:
        raise ValueError(f"主题 '{topic}' 不存在于题库中")
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("limit 必须是正整数，不能是布尔值或其他类型")
    exercises = EXERCISE_BANK.get(topic, [])
    if limit is not None:
        exercises = exercises[:limit]
    return exercises

# 工具描述
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_exercise_list",
            "description": "按主题查询本地题库中的练习名称；未知主题会报错。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "练习主题，例如二分查找或排序",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回的练习数量限制，省略时则返回所有练习，如果数量不足时返回所有练习并告知用户数量不足",
                    }
                },
                "required": ["topic"],
                "additionalProperties": False,
            },
        },
    }
]

def tool_provider(messages, api_key):
    """调用DeepSeek接口，传入工具列表"""
    return deepseek_provider(messages, api_key, tools=TOOLS)

def execute_tool(tool_call):
    """检查模型请求，并执行工具调用"""
    if not isinstance(tool_call, dict):
        return {"error": "工具调用请求必须是字典"}
    function = tool_call.get("function")
    if function is None:
        return {"error": "工具调用请求中缺少 'function' 字段"}
    if not isinstance(function, dict):
        return {"error": "工具调用请求中 'function' 字段必须是字典"}
    function_name = function.get("name")                    # 键不存在默认返回None
    if function_name == "get_exercise_list":
        arguments_text = function.get("arguments")
        if arguments_text is None:
            return {"error": "工具调用请求中缺少 'arguments' 字段"}
        if not isinstance(arguments_text, str):
            return {"error": "工具调用请求中 'arguments' 字段必须是字符串类型"}
        try:
            arguments = json.loads(arguments_text)
        except json.JSONDecodeError as e:
            return {"error": f"工具调用请求中 'arguments' 字段必须是有效的JSON格式: {e}"}
        # 键集合必须是 {"topic"} 或 {"topic", "limit"}
        if isinstance(arguments, dict) and (set(arguments.keys()) == {"topic"} or set(arguments.keys()) == {"topic","limit"}):
            topic = arguments["topic"]
            if "limit" in arguments:
                if arguments["limit"] is None:
                    return {"error": "limit 参数不能为显示null"}
                limit = arguments["limit"]
            else:
                limit = None
            try:
                exercises = get_exercise_list(topic, limit=limit)
                return {"exercises": exercises}
            except ValueError as e:
                return {"error": str(e)}
        else:
            return {"error": "参数格式错误，必须包含'topic'"}
    else:
        return {"error": f"未知的工具调用: {function_name}"}

def run_tool_loop(messages, api_key, provider=tool_provider, max_rounds=3):
    """运行工具调用循环"""
    if type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("max_rounds 必须是大于等于1的整数")
    for round_num in range(1, max_rounds + 1):

        # 1.请求模型
        raw = call_with_retry(provider, messages, api_key, base_delay=1.0)

        choice = raw["choices"][0]
        assistant_message = choice["message"]
        finish_reason = choice.get("finish_reason", "unknown")

        if finish_reason not in ["stop", "tool_calls"]:
            raise RuntimeError(f"模型异常结束，finish_reason: {finish_reason}")

        print(
            f"第{round_num}轮模型消息：",
            json.dumps(assistant_message, ensure_ascii=False, indent=2)
        )
        print("结束标记：", finish_reason)

        # 2. 获取工具调用请求
        tool_calls = assistant_message.get("tool_calls")
        if tool_calls is None:
            tool_calls = []

        if not isinstance(tool_calls, list):
            raise RuntimeError("模型返回的 tool_calls 格式错误")

        # 3. 有工具调用请求
        if tool_calls:
            # 最后一轮仍然调用工具，停止循环
            if round_num == max_rounds:
                raise RuntimeError("达到最大轮数，但模型仍然请求调用工具")

            # 保存模型信息
            messages.append(assistant_message)

            # 逐条执行工具调用并追加对应结果
            for tool_call in tool_calls:
                result = execute_tool(tool_call)
                label = f"第{round_num}轮 | 调用{tool_call['id']} | {tool_call['function']['name']}"
                if "error" in result:
                    print(f"{label} | 拒绝：{result['error']}")
                else:
                    print(f"{label} | 成功：返回{len(result['exercises'])}道练习")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })
            continue  # 继续下一轮循环，重新请求模型
        # 4. 没有工具调用请求，正常结束循环
        if finish_reason == "stop":
            answer = assistant_message.get("content")
            if not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("模型返回的 content 必须是非空字符串")
            return answer

        # 5. 其他结束标记，抛出异常
        raise RuntimeError(f"模型异常结束，finish_reason: {finish_reason}")
    raise RuntimeError("工具调用循环异常结束")


# 运行入口
if __name__ == "__main__":
    """本地检查get_exercise_list函数"""

    topics = ["二分查找", "排序", "不存在的主题"]
    for topic in topics:
        try:
            exercises = get_exercise_list(topic)
            if exercises:
                print(f"主题: {topic}, 题目列表: {exercises}")
            else:
                print(f"主题: {topic}, 题目列表为空")
        except ValueError as e:
            print(f"主题: {topic}, 错误: {e}")

    """本地检查limit参数"""
    limits = [None, 1, 2, 10, -1, True, False]
    for limit in limits:
        try:
            exercises = get_exercise_list("二分查找", limit=limit)
            print(f"limit: {limit}, 题目列表: {exercises}")
        except ValueError as e:
            print(f"limit: {limit}, 错误: {e}")
    # 调用DeepSeek接口，传入工具列表
    api_key = os.getenv("DEEPSEEK_API_KEY") or getpass("DeepSeek API key: ")

    messages = [
        {
            "role": "system",
            "content":"查询本地题库时，请使用提供的工具，根据查询结果回答。",
        },
        {"role": "user", "content": "我的题库里有哪些二分查找练习？"},
    ]
    answer = run_tool_loop(messages, api_key)
    print("最终模型回答：", answer)
