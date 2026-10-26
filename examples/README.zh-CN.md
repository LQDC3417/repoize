# 复现本地工作流

[English](README.md) · [真实终端记录](demo.txt) · [验证范围](verification.md)

示例要求 **0.3.0 开发源码**，公开 0.1.0 包没有本轮新命令。先在源码仓库的虚拟环境中运行 `python -m pip install -e ".[dev]"`。

## 1. 复制样例

从 Repoize 源码仓库根目录运行，创建仓库同级演示目录。若目标已存在，复制直接失败，不覆盖之前的实验。

```bash
python -c "import shutil; shutil.copytree('tests/fixtures/languages/python', '../repoize-demo/python-fixture', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))"
repoize --version
repoize analyze ../repoize-demo/python-fixture
repoize init ../repoize-demo/python-fixture --dry-run
repoize init ../repoize-demo/python-fixture
repoize doctor ../repoize-demo/python-fixture --type agents
repoize update ../repoize-demo/python-fixture --check --type agents
```

上述命令均应退出 0，默认只生成 `AGENTS.md`。中文内容在 `init` 及后续每次 `update` 添加 `--lang zh`。

## 2. 更新时保留手写说明

打开演示目录的 `AGENTS.md`，在首个 `<!-- repoize:generated-start -->` 之前增加团队说明。在复制的 `pyproject.toml` 中，将 `greet = "app:main"` 改成 `hello = "app:main"`。

```bash
repoize update ../repoize-demo/python-fixture --check --type agents
repoize update ../repoize-demo/python-fixture --dry-run --diff --type agents
repoize update ../repoize-demo/python-fixture --type agents
repoize update ../repoize-demo/python-fixture --check --type agents
```

首次检查因漂移退出 **1**；预览、更新和最后检查均退出 **0**。核对命令来源变化，并确认手写说明仍在。只改手写区不算漂移。

## 3. 查看真实输出

- [初始英文 AGENTS.md](generated/python/AGENTS.en.md)
- [初始中文 AGENTS.md](generated/python/AGENTS.zh.md)
- [保留手写说明的更新结果](generated/python/AGENTS.updated.en.md)
- [真实终端输出](demo.txt)：2026-10-26，Windows / Python 3.13.12，Repoize 0.3.0。临时工作目录路径统一替换为 `<demo>`，提示符、编辑说明和退出码是记录注记；存储时已去除行尾空白，其余输出保留原文。当前终端分析界面仍为中文，生成内容默认英文。

[Python](../tests/fixtures/languages/python)、[TypeScript](../tests/fixtures/languages/typescript)、[Go](../tests/fixtures/languages/go) 样例用于验证 Repoize 证据提取。其他语言复制对应目录后执行相同流程。TypeScript 声明提供脚本证据，但不证明脚本涉及的全部工具已安装；这些目录不是经过完整工具链验收的应用。

只在明确的样例验证中执行过 Python 的 `python app.py` 与 `python -m pytest`。Repoize 本身没有执行提取出的项目命令；未执行 TypeScript / Go 的构建、测试。格式检查也不证明客户端发现或模型遵守。

Repoize 仓库自身保留历史手工配置，本示例不迁移、不覆盖。另见[迁移说明](../docs/migration.zh-CN.md)、[支持范围](../docs/support.zh-CN.md)和 [MCP 空模板](mcp/README.zh-CN.md)。
