# 只读工具调用

使用自造的本地题库，按主题返回练习名称。程序提供工具描述，接收模型生成的调用请求，解析和校验参数，执行白名单中的查询，再按原`tool_call_id`回送结果，让模型回答。

## 运行

只使用Python标准库。在仓库根目录运行：

```powershell
python -X utf8 .\03-tool-calling\01-tool_demo.py
```

脚本先做本地查询示例，再从`DEEPSEEK_API_KEY`环境变量或隐藏输入读取密钥，发送真实DeepSeek请求；不需要启动本地HTTP服务。示例问题是“我的题库里有哪些二分查找练习？”，预期回答包含查找目标位置、寻找左边界和二分答案入门。

## 行为与边界

- `get_exercise_list`要求非空字符串主题，去掉首尾空格后查询；未知主题抛`ValueError`。
- `execute_tool`只允许`get_exercise_list`，参数必须是JSON对象且仅含`topic`；成功返回`exercises`字典，拒绝时返回`error`字典，不查询题库。
- 同轮有多个工具请求时，先追加全部结果再请求模型，每条结果使用对应的原调用编号。
- `run_tool_loop`默认最多3轮模型请求，包含第一次；最后一轮仍请求工具则停止，不再执行该轮工具。HTTP临时失败另有每轮最多3次尝试，因此模型轮数不等于网络请求次数，也不保证总耗时上限。
- 无工具请求、结束标记为`stop`且回答为非空字符串时成功返回；异常结束标记或空回答报错。`tool_calls`缺失或为`None`均按无工具请求处理。
- 仅查询内存中的自造数据，不写入文件或数据库；未实现取消、持久化或框架集成。

## 参考

- [Microsoft AI Agents for Beginners 第4课：工具使用](https://github.com/microsoft/ai-agents-for-beginners/blob/main/04-tool-use/README.md)：工具描述、执行职责与消息往返。
- [DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)：非思考模式下的调用与结果回送格式。
