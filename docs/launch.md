# Discovery and first-user validation / 展示与首轮试用

This is a maintainer checklist, not evidence of publication or growth. No repository setting, user outreach, or telemetry is changed by running Repoize.

本文件是维护清单，不代表已经发布或取得增长。运行 Repoize 不修改仓库设置、不联系他人、不加入遥测。

## Repository metadata / 仓库信息

Suggested description:

> Generate, inspect, and safely maintain AI coding configurations from repository facts.

建议使用与真实能力一致的描述，说明“从仓库事实生成、检查和安全维护 AI 编程配置”。

Relevant topics to review manually: `agents-md`, `ai-coding`, `developer-tools`, `python-cli`, `claude-code`, `cursor`. Repoize is not an MCP server; do not tag it as one. Use the existing GitHub README as the documentation entry until a separate site is justified.

可手动选择上述相关 topics。Repoize 不是 MCP 服务器，不使用误导标签；先让 README 作为文档入口，不急于建立独立网站。

## Demonstrate a real task / 展示真实任务

Use the public Python, TypeScript, or Go fixture. Record the exact source/package version and a local run of analysis, generation, a handwritten note, a repository declaration change, preview, update, and drift check. Share only reviewed outputs without personal paths or credentials.

使用公开 Python、TypeScript 或 Go 样例，记录精确版本及真实操作：分析、生成、增加手写说明、修改仓库声明、预览、更新、漂移检查。分享前移除个人路径和凭据。

Keep the README's short example separate from detailed terminal output. If the published package is older than the demonstration, state source-install requirements clearly. Do not attribute stars in other projects to an unmeasured feature or presentation change.

The [recorded workflow](../examples/README.md) supplies a real local run and English/Chinese generated examples. Its [verification record](../examples/verification.md) states the version, checked behavior, and remaining gaps.

首屏演示保持简短，详细输出另链。公开包落后于演示时明确源码安装要求，不把竞品 stars 归因于未经实验的功能或展示设计。

[演示流程](../examples/README.zh-CN.md)提供真实本地记录与中英文生成文件，[验证记录](../examples/verification.md)列明版本、实测范围和缺口。

## Pilot / 小规模试用

Ask 5–8 willing individual developers or small-team maintainers to use their own repository. This is a qualitative pilot, not a statistical estimate. Outreach is a separate human-authorized activity; this checklist sends no messages.

邀请 5–8 位愿意参与的个人开发者或小团队维护者，用自己的项目试用。只作定性判断，不估计统计转化率；联系他人需另行明确安排，本清单不发送消息。

Record whether they can independently:

1. Install or run the intended version.
2. Understand one command source and one diagnostic.
3. Choose an output type and generate it.
4. Add a handwritten note.
5. Change a project declaration and understand the preview.
6. Update while keeping the handwritten note.
7. Re-run the check later without assistance.

记录是否能独立完成版本安装、理解依据与诊断、选择输出、增加手写说明、修改声明、审阅更新、保留手写内容，以及后续再次使用。

Capture the version, task, point of confusion, expected/actual outcome, and a safe minimal reproduction. Ask about repeat use after a week. Do not request a full private repository or environment dump.

记录版本、任务、卡点、预期与实际结果、脱敏最小复现，并在一周后询问是否再次使用。不要索取完整私有仓库或环境全集。

## Decide what to build next / 决定下一轮

- Prioritize unintended modifications, false findings, and unreproducible updates before target count.
- Add persistent preferences when several users repeatedly need the same type/language choices.
- Start Monorepo work from multiple real package-scope cases, not an assumed universal inheritance model.
- Add integrations or a dedicated Action only after ordinary CLI usage shows repeated demand.
- Use stars and downloads as supporting signals alongside completed tasks and repeat use; do not promise a growth percentage.

优先修复意外修改、误报和不可复现更新，再考虑扩目标。重复参数形成真实负担后增加配置持久化；Monorepo 基于多个实际作用域案例；CLI 集成反复被需要后再做独立 Action。Stars、下载只作辅助信号，不承诺增长比例。
