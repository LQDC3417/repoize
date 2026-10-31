# Local verification / 本机验证

Demo recorded on 2026-10-26; acceptance record updated on 2026-10-29 for the 0.3.0 development source. The demo used product source at `a8d5fc3` plus the Task 5 delivery working tree. Final local acceptance used `c7c8f35a54e63c04a8fe9e65ef9dcad6c258752f`, as recorded below. Neither result is a tagged release or a hosted CI pass.

演示录于 2026-10-26，验收记录于 2026-10-29 补齐。演示基于 `a8d5fc3` 产品实现和 Task 5 工作区交付文件，最终本地验收基于下述 `c7c8f35` 提交；两者均不代表已打标签发布或托管 CI 通过。

The stored terminal record has trailing whitespace stripped; its output text is otherwise preserved as described in the [example guide](README.md).

终端记录存储时已去除行尾空白，其余整理方式见[示例说明](README.zh-CN.md)。

## Verified locally / 本机已验证

- Initial delivery snapshot on Windows, Python 3.13.12: `python -m pytest -q` — **427 passed, 2 skipped**. The skipped cases require POSIX filesystem behavior unavailable on this platform.
- After the final ordering correction, the main thread reran the full suite on Windows with Python 3.10.20 and 3.13.12: **430 passed, 2 skipped** on each. Three new regressions cover language-count ties, count precedence, and filename case ties; the implementation changes only the two sort keys. 最终固定排序补正后，主线程在 Python 3.10/3.13 各复验 430 项通过、2 项 POSIX 用例跳过。
- `ruff check src tests scripts`, `ruff format --check src tests scripts`, and `git diff --check` passed. The formatter checked 49 Python files.
- The release checker has 15 tests: consistent batch/hash output, static version reading, tag/source mismatch, missing/extra artifacts, metadata mismatch, corrupt archives, checksum output, and uv's `.gitignore` build marker. Initial checker tests and the later uv-marker regression were observed failing before implementation.
- Python, TypeScript, and Go disposable copies completed analysis, default generation, `doctor --type agents`, and `update --check --type agents`. Python English and Chinese generation both passed immediate drift checks. The English demonstration then changed the declared entry point, observed drift status 1, previewed and applied the update, preserved a handwritten prefix, and finished with status 0. Dry-run bytes and change-report schema were checked.
- The Python sample printed `Hello, world!`; its focused test passed (1 test). This is an explicit fixture check outside Repoize's extraction logic. TypeScript/Go project scripts were not executed.
- A working-tree `uv build` produced a real wheel and sdist in an external directory. `python scripts/check_release.py --dist <that directory> --tag v0.3.0` accepted their names/metadata and printed SHA-256 lines. This batch was a checker probe; the final clean-commit artifacts are recorded below.
- That exact wheel was installed into a fresh external Python 3.13.5 environment. `tests/smoke_installed.py` passed, including installed CLI/version, packaged templates and JSON schemas, default/explicit generation, preservation, preview, and drift behavior. This probe is separate from the final clean-commit cross-version acceptance.
- The documented PowerShell checksum-saving method was run against that real artifact batch, using ASCII and explicit LF line endings. The saved manifest contained no CR bytes, and Git for Windows GNU `sha256sum --check SHA256SUMS` reported `OK` for both wheel and sdist. PowerShell 与 GNU 校验互通已实测：显式 LF 清单无 CR 字节，两份真实产物均通过核验。
- All 99 local links in 22 delivery Markdown files resolved. Both workflow YAML files and all three issue-template frontmatter blocks parsed locally. This is syntax/link validation, not an Actions execution.

上述命令在本机执行；样例中的项目命令仍由 Repoize 标为 `not_run`。手动验证样例不等于 Repoize 自动执行命令，也不证明其他语言工具链、AI 客户端或模型行为。

## Final clean-commit acceptance / 最终干净提交验收

The following checks were completed on 2026-10-26 against source commit [`c7c8f35a54e63c04a8fe9e65ef9dcad6c258752f`](https://github.com/LQDC3417/repoize/commit/c7c8f35a54e63c04a8fe9e65ef9dcad6c258752f). They supplement the earlier working-tree probes above; they do not change the version or source of the stored demo.

以下是 2026-10-26 对最终提交的验收结果，补充前述工作区探针，不改变已保存演示的版本和来源。

| Check / 检查 | Observed result / 实际结果 |
| --- | --- |
| Windows tests / 完整测试 | Python 3.10.20 and 3.13.12: each **430 passed, 2 skipped**; the skipped cases require POSIX behavior. Main-directory Python 3.13.12 rerun matched. |
| Static checks / 静态检查 | Ruff check and format passed for 49 Python files; full-change whitespace check passed. 113 relative links across 28 delivery Markdown files, both workflow YAML files and three issue-template frontmatter blocks passed local checks. |
| Clean build / 干净构建 | Built the sdist from the final commit, then built the wheel from that sdist. Source version, planned tag string `v0.3.0`, and both artifact metadata agreed. No tag was created. |
| Exact wheel / 同批 wheel | Fresh external installs on Python 3.10.20 and 3.13.12 passed `tests/smoke_installed.py`. |
| Exact sdist / 同批源码包 | Fresh external Python 3.10.20 build/install passed the installed smoke check. |
| Chinese flow / 中文流程 | Installed-package generation of all six configuration types, doctor, and immediate drift check passed. |
| GitHub source install / 远程源码安装 | Fresh external pip install from default `main` recorded the exact commit in `direct_url.json`, reported 0.3.0 and passed the full installed smoke check. Package location was inside the new environment, without `PYTHONPATH` shadowing. |
| uvx source entry / uvx 源码入口 | GitHub source entry reported 0.3.0 and completed the doctor JSON command. |
| Checksums / 校验清单 | ASCII/LF manifest; GNU `sha256sum --check` accepted both final artifacts. |

The final local batch has these SHA-256 values, rechecked on 2026-10-29. Earlier probe batches with the same version are not this batch. These files remain unpublished, and their checks do not cover the later repository-configuration edits below.

最终本地批次的 SHA-256 于 2026-10-29 复核如下。同版本的早期探针不属于此批次；产物未发布，其验收不覆盖下述后续仓库配置改动。

```text
dacd452fd4d8bc8157984681bc97a4c678512e28c9471a40ecd964ac1250c359  repoize-0.3.0-py3-none-any.whl
a3438895fe978125030bbdb9b5693a56553941aec79ee834496b8e916275debf  repoize-0.3.0.tar.gz
```

## Repository configuration maintenance / 仓库自身配置维护

On 2026-10-29, the original configuration files were backed up outside the checkout before manual migration. `.claude/mcp.json` moved to root `.mcp.json`, preserving both server definitions; `.cursorrules` moved to `.cursor/rules/repoize.mdc`, preserving the rule body and adding MDC frontmatter. The Skill name now matches `project-dev`, and its lint instructions reflect the configured Ruff checks. Shared instructions use the project name `repoize` and link to the contribution guide instead of copying machine-specific tool versions, paths and environment values. Existing coding conventions remain intact.

2026-10-29 先在仓库外备份原文件，再迁移 MCP 和 Cursor 路径、修正 Skill 名称与代码检查说明；两个 MCP 服务定义及 Cursor 规则正文保留。共享指令统一项目名，移除本机版本和环境信息，保留编码约定并引用贡献指南。

Only the two hard-coded repository-path arguments in MCP changed to `${CLAUDE_PROJECT_DIR:-.}`, following the [Claude Code variable-expansion documentation](https://code.claude.com/docs/en/mcp#option-3-add-a-local-stdio-server). Launch Claude Code from the repository root when relying on the `.` fallback. An explicitly supplied `CLAUDE_PROJECT_DIR` must point to that root. This migration did not install or start either server; client expansion, loading and connections still need an actual client check.

MCP 仅把两个硬编码仓库路径参数改为上述变量引用。依赖 `.` 默认值时，从仓库根目录启动 Claude Code；显式设置变量时，值须指向该根目录。本次未安装或启动服务，变量展开、加载与连接仍待客户端实测。

The six repository configuration targets passed `doctor --strict --format json` with **0 errors, 0 warnings and 1 informational finding**. The informational `CMD001` concerns an unexecuted default build suggestion, not a configuration failure. Existing instruction bodies remain manually maintained without managed markers; this result is not an `update --check` drift pass.

仓库六类目标的严格自检结果为 **0 错误、0 警告、1 条提示**；提示仅表示默认构建建议未执行。现有指令正文仍由人工维护，未添加管理标记，自检通过不等于漂移检查通过。

After these configuration edits, Windows / Python 3.13.12 was rerun on 2026-10-29: **430 passed, 2 skipped**. Ruff check and format passed for all 49 Python files; changed relative documentation links and full-file preservation checks for the migrated configuration content passed. No product source code changed.

配置修改后于 2026-10-29 复跑 Windows / Python 3.13.12：**430 项通过、2 项 POSIX 用例跳过**；49 个 Python 文件的 Ruff 检查通过，修改文档的相对链接及迁移内容保留检查通过。本次未改产品源码。

## Scan and diagnostic fixes / 扫描与诊断修复

On 2026-10-30, the working tree was checked for four fixes: quality scans reject linked files and Windows junctions, dependency directories use the shared exclusion rules, strict diagnostics retain Cursor/Skill file links for `CFG003` without reading their targets, and shared `setup.cfg` files require a real `[flake8]` section before reporting Flake8. Packaging metadata alone no longer increases the quality score. Other supported quality sections in `setup.cfg` remain recognized as configuration evidence.

2026-10-30 核对工作区四项修复：质量分析跳过文件链接和 Windows junction，依赖目录使用共用排除规则；严格诊断对 Cursor/Skill 文件链接报 `CFG003`，不读取目标；仅在共享 `setup.cfg` 存在真实 `[flake8]` 配置节时识别 Flake8，打包元数据不再使评分虚高，其他受支持的质量配置节仍保留识别。

The regression probe loaded the two original analyzer modules from `HEAD` in an isolated Python process without replacing working-tree files: **27 failed, 3 passed, 68 deselected** for the targeted selection. With the current implementation, the full Windows / Python 3.13.12 suite completed with **464 passed, 2 skipped**. Ruff check and format passed for all 49 Python files. The two skipped POSIX cases remain unverified on Windows. Function-length extraction was not changed in this batch; these checks are not a new package build or a hosted CI result.

回归探针只在独立 Python 进程内加载 `HEAD` 的两个旧分析模块，不覆盖工作区文件；定向选择结果为 **27 项失败、3 项通过、68 项未选中**。当前实现的 Windows / Python 3.13.12 全量结果为 **464 项通过、2 项跳过**；49 个 Python 文件的 Ruff 检查通过。两个 POSIX 用例仍待对应平台验证；本批未改函数长度提取逻辑，也未构建新包或运行托管 CI。

## Remaining checks / 尚未验证

As rechecked on 2026-10-29, the final-commit CI run [40338421839](https://github.com/LQDC3417/repoize/actions/runs/40338421839) did not start because of an account billing lock. It provides no hosted test result; local YAML parsing and Windows tests do not replace the Ubuntu/Windows matrix. No release workflow was dispatched and no tag, GitHub Release or PyPI upload was created during this work.

2026-10-29 复核：最终提交的 CI 因账号计费锁定未启动，不能算作代码执行失败或测试通过。托管矩阵仍待实际运行，本轮没有触发发布工作流、标签或公开发布。

Actual client loading and MCP server connections remain unverified; see the [support matrix](../docs/support.md). PyPI and the latest GitHub Release were still 0.1.0 when checked on 2026-10-29, so the demonstrated features require source installation. The 5–8 developer pilot and one-week repeat-use follow-up in the [launch checklist](../docs/launch.md) have not been performed.

真实客户端加载与 MCP 连接、5–8 人试用及一周回访尚未执行。2026-10-29 核查时公开版本仍为 0.1.0，演示的新功能需通过源码安装体验。
