# Agent Engineering Lab

个人 Agent 工程学习仓库，保存代码实验、必要说明和可复现的实践成果。

学习从模型调用与错误处理开始，逐步进入工具调用、Agent 循环、工作流、状态管理、知识检索与完整应用交付。通过实现、失败实验和需求变化，练习理解、调试、审查与设计可靠的 AI 系统。

## 当前内容

| 单元                                           | 内容               | 当前范围                                              |
| ---------------------------------------------- | ------------------ | ----------------------------------------------------- |
| [01-reliable-call](01-reliable-call/README.md) | 可靠调用的起步实验 | 消息/响应校验、本地HTTP请求、真实等待超时与坏响应对照 |
| [02-structured-output](02-structured-output/) | 结构化输出练习 | 真实JSON模式调用、回答提取与业务字段校验 |
| [03-tool-calling](03-tool-calling/README.md) | 只读工具调用 | 主题查询、参数校验、结果回送与有界循环 |

## 代码阅读顺序

| 序号 | 文件 | 内容 |
| --- | --- | --- |
| 01.01 | [main.py](01-reliable-call/main.py) | 消息/响应校验、模拟提供者与HTTP客户端 |
| 01.02 | [local_server.py](01-reliable-call/local_server.py) | 本地HTTP对照服务 |
| 01.03 | [deepseek_demo.py](01-reliable-call/deepseek_demo.py) | DeepSeek真实调用入口 |
| 01.04 | [retry_demo.py](01-reliable-call/retry_demo.py) | 错误分类、有限重试与受控场景 |
| 02.01 | [01-structured_demo.py](02-structured-output/01-structured_demo.py) | 真实结构化回复的解析与校验练习 |
| 03.01 | [01-tool_demo.py](03-tool-calling/01-tool_demo.py) | 本地题库查询与真实工具调用闭环 |

目录编号表示学习单元，表中编号表示单元内的阅读顺序。可靠调用单元的脚本保留原文件名，使现有模块导入继续有效。

结构化输出练习入口：`python -X utf8 .\02-structured-output\01-structured_demo.py`。脚本从环境变量`DEEPSEEK_API_KEY`或隐藏输入读取密钥，先运行本地解析用例，再发送真实请求；未说明的练习数量保留为`null`，解析后为`None`。

本地回显服务用于HTTP对照，保留的fake示例通过主动抛出异常模拟失败。真实模型接入、基础有限重试、结构化业务结果和最小只读工具调用已实现；JSON可解析与业务字段合格分别检查，HTTP重试不包含本地业务校验。取消尚未实现；工具实验的运行和上限见[单元说明](03-tool-calling/README.md)。

## 运行

当前实验仅使用 Python 标准库。在仓库根目录打开两个终端，第一个启动本地服务：

```powershell
python -X utf8 .\01-reliable-call\local_server.py
```

第二个运行客户端；结束实验后，在服务端终端按 Ctrl+C 停止服务：

```powershell
python -X utf8 .\01-reliable-call\main.py
```

后续需要第三方依赖时，统一在仓库根目录使用 uv 管理环境，并提交 `pyproject.toml` 与 `uv.lock`，同时更新运行说明。不提前建立空模块或安装整套教程依赖。

## 组织方式

按完整学习单元建立目录，同一机制的对照、失败和变式尽量放在同一单元。单元说明保留目标、运行方法、实际实现范围及重要限制；综合项目形成后再依据职责拆分。

长期知识总结另行整理。仓库保存代码、必要说明、人工构造的评测案例和适合公开的实验报告；密钥、原始响应日志、个人数据、模型权重和批量生成文件不提交。

## 学习资源

[Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) 提供概念、代表示例与覆盖参考，配合实际使用的模型服务、SDK 和工程工具官方文档。练习实现注明其来源，不把本地改写或模拟实验记作官方云服务实验完成。
