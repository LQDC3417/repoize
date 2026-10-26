# 贡献指南

[English](CONTRIBUTING.md)

欢迎提交范围明确的小贡献：一种误识别声明文件、命令来源回归、配置格式样例，或附版本记录的客户端发现结果。

## 开发

使用 Python 3.10 及以上虚拟环境，安装项目和开发工具：

```bash
git clone https://github.com/LQDC3417/repoize.git
cd repoize
python -m venv .venv
```

Windows 使用 `.venv\Scripts\activate`，Linux/macOS 使用 `source .venv/bin/activate` 激活，然后运行：

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/
```

覆盖率报告可使用 `python -m pytest --cov=src/repoize --cov-report=term-missing`。在专用分支工作，提交信息使用描述明确的 `feat:`、`fix:`、`docs:` 或 `test:`，再创建 Pull Request 审查。

保持最小改动，遵循现有风格：中文注释与 docstring、英文标识符、清楚直接的函数。修复前先增加能复现问题的失败测试。CLI 行为变化还需验证退出状态及 stdout/stderr。

## 安全与兼容

- 不执行被扫描仓库的脚本来识别命令。
- 保留手写正文、已有 frontmatter 和用户维护的 MCP 服务器定义。
- 保留分析 JSON v1，新报告使用独立 Schema 和测试。
- 隐私测试使用合成凭据，不读取真实环境变量全集。
- 预览测试需证明文件、目录和修改时间均未变化。
- 公开行为变化时同步英文和中文文档。
- 格式断言不能当作客户端加载测试；真实客户端版本和观察结果单独记录。

## 复现材料

Issue 包含 Repoize 版本、操作系统、执行命令、预期与实际行为，以及最小公开或脱敏样例。不要上传令牌、服务器环境变量值、私有 URL、专有指令或完整私有仓库。

意外修改问题请在本地保留原文件，说明具体变化；测试修复时不要覆盖唯一的复现材料。

## 客户端验证

[支持矩阵](docs/support.zh-CN.md)区分格式检查与实际加载。有效记录包含精确版本、操作系统、日期、最小安全输入、是否发现文件及警告。发现成功不能保证模型遵守指令。

## Pull Request

描述具体问题、改后行为、相关测试和剩余限制。避免无关重构。新增解析器或目标时提供真实样例，并说明支持的语法和作用域。

发布安装包、修改仓库设置属于独立维护操作；普通分析和生成不得加入自动联网、遥测、MCP 安装或发布副作用。

## 参与和许可证

尊重参与者，接受建设性批评，讨论聚焦项目。贡献按项目的 [MIT 许可证](LICENSE) 提供。

## 构建与发布检查

按[发布说明](docs/releasing.md)构建并核对同一批 wheel / 源码包。`python scripts/check_release.py` 不导入包，只核对源码版本；`--tag v0.3.0` 同时核对计划标签。检查器不执行发布。生成内容变化时，复跑[本地样例流程](examples/README.zh-CN.md)。
