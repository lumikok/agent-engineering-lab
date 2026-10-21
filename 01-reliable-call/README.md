# 01｜可靠调用起步

## 当前问题

如何把消息校验、JSON编码、HTTP请求、响应解析与校验连成一条可观察的调用链路，并区分输入错误、网络等待失败和坏响应？

## 已有实现

- `fake_provider(messages, mode="ok")`：从最后一条消息读取内容，返回包含 `text` 的字典。
- `mode="timeout"`：主动抛出 `TimeoutError`，由调用方捕获。
- 未知模式：抛出 `ValueError`，由调用方捕获。
- `mode="bad_response"`：返回 `{"text": 123}`，用于验证提供者正常返回但数据不合格的情况。
- `validate_response(response)`：依次检查响应为字典、包含 `text`、值为字符串且不为空或全空白；不合格时抛出说明原因的 `ValueError`，合格时返回原始文本。
- `strip()` 只用于检查空白，校验成功不会移除原文本的两端空白或添加前缀。
- 调用方按“获取响应 → 校验 → 展示”处理数据，捕获调用或校验产生的异常。
- `validate_messages(messages)`：检查非空列表、每项字典、role/content字段及类型、允许的角色和非空白内容，成功保留原消息。
- `http_provider(messages, url, timeout=3.0)`：先校验消息，再把 `{"messages": messages}` 转为JSON文本和UTF-8字节，发送POST请求，读取并解析JSON响应。服务端按此包装结构取消息，直接发送列表会得到HTTP400。
- `local_server.py`：只绑定 `127.0.0.1:8765` 的标准库实验服务，提供正常回显、延迟响应和错误字段类型。

## 运行

在仓库根目录的第一个终端启动服务：

```powershell
python -X utf8 .\01-reliable-call\local_server.py
```

第二个终端运行客户端：

```powershell
python -X utf8 .\01-reliable-call\main.py
```

客户端先运行原有消息/fake响应示例，再执行四组真实HTTP对照：

| POST路径 | 客户端timeout | 预期结果 |
|---|---:|---|
| `/generate` | 3秒 | 立即返回回显文本，校验通过 |
| `/slow` | 0.5秒 | 服务等待2秒才回复，客户端约0.5秒后等待超时 |
| `/slow` | 3秒 | 约2秒后成功 |
| `/bad-response` | 3秒 | HTTP200且JSON解析成功，但text为数字，响应校验拒绝 |

输出包含场景、失败阶段、异常类型和耗时。耗时在finally中计算，失败也会留下记录；具体数值随机器负载变化。

实验结束，在服务端终端按 Ctrl+C 停止服务。

## DeepSeek真实调用

在仓库根目录运行，无需启动本地回显服务：

```powershell
python -X utf8 .\01-reliable-call\deepseek_demo.py
```

使用本机环境变量`DEEPSEEK_API_KEY`，未设置时按提示隐藏输入密钥。脚本向DeepSeek发送非流式请求，默认模型`deepseek-flash`、关闭思考、输出上限128 Token；提取回答并复用text校验，展示`finish_reason`与`usage`。模型名和参数以使用时的官方文档为准。

正常调用和固定假密钥实验都经过`call_with_retry`。假密钥预期HTTP401并立即停止；正常调用在有限尝试内仍失败时，异常向上传播，不继续执行后面的鉴权实验。

## 有限重试实验

```powershell
python -X utf8 .\01-reliable-call\retry_demo.py
```

此脚本仅使用本地模拟函数，不读取密钥或访问网络。七组场景覆盖401立即停止、503后恢复、持续503到上限停止、ValueError直接传播、模拟超时后恢复、503后遇到400停止，以及上限改为2后的停止行为。

`call_with_retry(provider, messages, api_key, max_attempts=3, base_delay=0.1)`接收提供者函数，成功时原样返回结果。`max_attempts`包含首次调用，小于1时抛ValueError。仅HTTP429/500/503和直接抛出的TimeoutError允许重试，其他异常直接传播；最后一次失败保留原始异常，不再等待。

重试前的等待为`base_delay * 2 ** (attempt - 1)`。默认三次尝试最多等待0.1、0.2秒；真实调用入口使用base_delay=1.0，对应1、2秒。输出记录尝试序号、错误和安排的等待时间。

## 实现边界与下一步

这里已进行真实本地HTTP通信和阻塞等待超时，服务内容仍是回显文本。`urlopen`的timeout针对阻塞操作，不是整个业务的总时限。

客户端超时只说明没有及时取得完整结果，不能据此判断服务端是否执行成功，也不会自动取消服务端工作。对创建等有副作用的操作，应查询结果或在幂等保障下重发，避免重复执行。

HTTP200、JSON可解析、响应契约合格及任务结果正确是不同层次。真实模型调用和有限重试已接入，尚未实现幂等、取消、总业务截止时间或完整的网络错误分类。重试可能增加模型调用费用，也不保证得到相同回答；当前策略不能直接套用于有副作用的工具操作。

后续继续结构化输出及工具调用，并在具体操作中验证幂等与权限等边界。

## 参考

- [DeepSeek首次API调用](https://api-docs.deepseek.com/)
- [DeepSeek错误码](https://api-docs.deepseek.com/quick_start/error_codes/)

- [Python 3.14 JSON](https://docs.python.org/3.14/library/json.html)
- [Python 3.14 urllib.request](https://docs.python.org/3.14/library/urllib.request.html)
- [Python 3.14 http.server](https://docs.python.org/3.14/library/http.server.html)
