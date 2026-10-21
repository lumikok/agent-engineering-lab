"""受控重试实验：用预设失败序列检查调用次数、返回结果和最终异常。

只使用模拟提供者，不访问网络或读取密钥。
"""

import time
from urllib.error import HTTPError


def call_with_retry(provider, messages, api_key, max_attempts=3, base_delay=0.1):
    """成功原样返回；按错误类型决定重试，到上限重新抛出最后一次异常。

    max_attempts包含首次调用；base_delay为第一次重试前的等待秒数。
    HTTP 429/500/503及TimeoutError允许有限重试，其他错误向上传播。
    两次重试前分别等待base_delay和2*base_delay。
    记录尝试序号、失败类型/状态码、实际安排的等待时间。
    """
    if max_attempts < 1:
        raise ValueError("max_attempts必须至少为1")
    for attempt in range(1, max_attempts + 1):
        print(f"  尝试{attempt}/{max_attempts}")
        try:
            return provider(messages, api_key)
        except HTTPError as exc:
            print(f"  第{attempt}次调用失败：HTTP{exc.code}")
            if exc.code not in (429, 500, 503):
                raise
            if attempt == max_attempts:
                raise
        except TimeoutError as exc:
            print(f"  第{attempt}次调用失败：{type(exc).__name__}")
            if attempt == max_attempts:
                raise

        if attempt < max_attempts:
            delay = base_delay * (2 ** (attempt - 1))
            print(f"  等待{delay:.1f}s后重试...")
            time.sleep(delay)


def make_sequence_provider(events):
    """每次调用取出一个事件；整数表示HTTP错误，异常对象直接抛出。"""
    remaining = iter(events)
    calls = []

    def provider(messages, api_key):
        event = next(remaining)
        calls.append(event)
        print(f"  模拟提供者第{len(calls)}次调用：{event}")
        if isinstance(event, int):
            raise HTTPError("https://example.invalid", event, "模拟HTTP失败", None, None)
        if isinstance(event, Exception):
            raise event
        return {"text": "模拟成功"}

    return provider, calls


def run_case(name, events, expected_calls, expected_error=None, expected_code=None,max_attempts=3):
    provider, calls = make_sequence_provider(events)
    print(f"\n{name}")
    try:
        result = call_with_retry(
            provider,
            [{"role": "user", "content": "测试"}],
            api_key="unused-test-key",
            max_attempts=max_attempts
        )
    except Exception as exc:
        if expected_error is None or not isinstance(exc, expected_error):
            raise
        if expected_code is not None:
            assert exc.code == expected_code, f"最后错误应为HTTP{expected_code}"
        print(f"  最终异常：{type(exc).__name__}")
    else:
        assert expected_error is None, "本场景应抛出异常，不能返回None或假成功"
        assert result == {"text": "模拟成功"}, "应原样返回提供者成功结果"
        print(f"  最终结果：{result}")
    assert len(calls) == expected_calls, (
        f"期望调用{expected_calls}次，实际{len(calls)}次"
    )
    print("  场景通过")


if __name__ == "__main__":
    run_case("401立即停止", [401, "ok"], 1, HTTPError, 401)
    run_case("临时失败后恢复", [503, "ok"], 2)
    run_case("持续失败到上限停止", [503, 503, 503, "ok"], 3, HTTPError, 503)
    run_case("本地输入错误直接传播", [ValueError("模拟无效消息"), "ok"], 1, ValueError)
    run_case("无业务写入的调用超时后恢复", [TimeoutError("模拟超时"), "ok"], 2)
    run_case("503后遇到400立即停止", [503, 400, "ok"], 2, HTTPError, 400)
    run_case("非默认重试上限后停止",[503, 503, "ok"],2,HTTPError, 503,max_attempts=2)
