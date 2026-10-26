# 在 CI 检查受管上下文

[English](ci.md)

下面使用开发源码，公开 0.1.0 包没有 `update --check`。正式发布后改为安装已验收的精确版本。若从源码可复现安装，将 `main` 换成已审阅的 Repoize 完整提交 SHA。

先在自己的仓库生成、审阅并提交 `AGENTS.md`。CI 只检查已有受管内容，不初始化项目、不提交更新。

```yaml
name: Repoize context
on: [push, pull_request]
permissions:
  contents: read
jobs:
  context:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install development Repoize
        run: python -m pip install "git+https://github.com/LQDC3417/repoize.git@main"
      - name: Check supported structure
        run: repoize doctor --type agents
      - name: Check managed content
        run: repoize update --check --type agents
```

中文生成内容将最后一条命令改为 `repoize update --check --type agents --lang zh`。本地生成与 CI 使用相同语言。其他已有生成类型显式增加；只用一种工具的项目不必要求全部文件。

## 退出状态

| 命令 | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| `doctor` | 无 error | 存在 error；strict 时 warning 也失败 | 参数或路径错误 | 无法完成诊断 |
| `update --check` | 可比较的受管内容一致 | 漂移或内容冲突 | 参数或路径错误 | 无效文件、运行失败或无可比较内容 |

Doctor 告警默认不导致失败，`--strict` 才将告警作为失败。无配置时明确告警，不宣称全部通过；显式指定类型可要求对应入口存在。

旧 `check` 是覆盖参考报告，不具备这些阻断语义。`validate` 只校验分析 JSON v1，不校验 doctor 或变更报告。

## 漂移含义

- 只比较受管正文，手写区不触发漂移。
- 仓库声明变化可能改变推导命令与生成内容。
- MCP 服务定义归用户维护，不属于受管文本漂移；其已支持结构使用 doctor 检查。
- 没有可比较受管内容时不能通过。
- 生成目录树排除 Repoize 自身输出路径，避免首次生成后的自引用差异。

CI 不自动修复。先在本地运行 `repoize update --dry-run --diff`，审阅后运行 `repoize update`，再自行提交确认过的配置。

已有文本差异可能包含私有指令，分享日志前先本地检查。MCP 报告不打印服务器秘密值。参见[支持边界](support.zh-CN.md)与[迁移说明](migration.zh-CN.md)。
