# Local verification / 本机验证

Recorded on 2026-10-26 for the 0.3.0 development source. The demo used product source at `a8d5fc3` plus the Task 5 delivery working tree; it is a development record, not a tagged release or a CI result.

记录对应 0.3.0 开发源码；演示基于 `a8d5fc3` 产品实现和 Task 5 工作区交付文件，不代表已打标签发布或 CI 通过。

The stored terminal record has trailing whitespace stripped; its output text is otherwise preserved as described in the [example guide](README.md).

终端记录存储时已去除行尾空白，其余整理方式见[示例说明](README.zh-CN.md)。

## Verified locally / 本机已验证

- Initial delivery snapshot on Windows, Python 3.13.12: `python -m pytest -q` — **427 passed, 2 skipped**. The skipped cases require POSIX filesystem behavior unavailable on this platform.
- After the final ordering correction, the main thread reran the full suite on Windows with Python 3.10.20 and 3.13.12: **430 passed, 2 skipped** on each. Three new regressions cover language-count ties, count precedence, and filename case ties; the implementation changes only the two sort keys. 最终固定排序补正后，主线程在 Python 3.10/3.13 各复验 430 项通过、2 项 POSIX 用例跳过。
- `ruff check src tests scripts`, `ruff format --check src tests scripts`, and `git diff --check` passed. The formatter checked 49 Python files.
- The release checker has 15 tests: consistent batch/hash output, static version reading, tag/source mismatch, missing/extra artifacts, metadata mismatch, corrupt archives, checksum output, and uv's `.gitignore` build marker. Initial checker tests and the later uv-marker regression were observed failing before implementation.
- Python, TypeScript, and Go disposable copies completed analysis, default generation, `doctor --type agents`, and `update --check --type agents`. Python English and Chinese generation both passed immediate drift checks. The English demonstration then changed the declared entry point, observed drift status 1, previewed and applied the update, preserved a handwritten prefix, and finished with status 0. Dry-run bytes and change-report schema were checked.
- The Python sample printed `Hello, world!`; its focused test passed (1 test). This is an explicit fixture check outside Repoize's extraction logic. TypeScript/Go project scripts were not executed.
- A working-tree `uv build` produced a real wheel and sdist in an external directory. `python scripts/check_release.py --dist <that directory> --tag v0.3.0` accepted their names/metadata and printed SHA-256 lines. This batch is a checker probe; the maintainer must build final artifacts from the final reviewed commit.
- That exact wheel was installed into a fresh external Python 3.13.5 environment. `tests/smoke_installed.py` passed, including installed CLI/version, packaged templates and JSON schemas, default/explicit generation, preservation, preview, and drift behavior. This probe is separate from the final clean-commit cross-version acceptance.
- The documented PowerShell checksum-saving method was run against that real artifact batch, using ASCII and explicit LF line endings. The saved manifest contained no CR bytes, and Git for Windows GNU `sha256sum --check SHA256SUMS` reported `OK` for both wheel and sdist. PowerShell 与 GNU 校验互通已实测：显式 LF 清单无 CR 字节，两份真实产物均通过核验。
- All 99 local links in 22 delivery Markdown files resolved. Both workflow YAML files and all three issue-template frontmatter blocks parsed locally. This is syntax/link validation, not an Actions execution.

上述命令在本机执行；样例中的项目命令仍由 Repoize 标为 `not_run`。手动验证样例不等于 Repoize 自动执行命令，也不证明其他语言工具链、AI 客户端或模型行为。

## Remaining checks / 尚未验证

The GitHub matrix has not been demonstrated passing. The previous main CI run [40189193800](https://github.com/LQDC3417/repoize/actions/runs/40189193800) did not start because of an account billing lock; it provides no Ubuntu/Windows test result. Local YAML parsing and local Windows tests do not replace the hosted matrix. The release workflow was not dispatched and no tag, GitHub Release, or PyPI upload was created.

GitHub 矩阵尚无本轮通过记录；既有运行因账号计费锁定未启动，不能算作代码执行失败或测试通过。尚未触发发布工作流、标签、GitHub Release 或 PyPI 上传。

Actual client loading remains unverified; see the [support matrix](../docs/support.md). The repository's own historical `.claude/mcp.json`, `.cursorrules`, Skill wrapper, and unmarked instructions were intentionally retained for manual migration. A doctor run on this repository may correctly report legacy or format findings; the disposable demo is not a claim that the repository's own configurations are all clean.

真实客户端加载未验收；仓库自身历史配置保留，需手动迁移。演示通过不能当作仓库自身全部 doctor 项目通过。

The remote source-install quick start needs verification after the reviewed source is pushed. Public PyPI 0.1.0 does not include the demonstrated commands. A final clean-commit wheel/sdist build and supported-version installs belong to release acceptance. The 5–8 developer pilot and one-week repeat-use follow-up in the [launch checklist](../docs/launch.md) are future human work, not performed observations.

源码推送后仍需验证远程安装；最终提交产物及支持版本安装由发布验收完成。5–8 人试用与一周回访尚未开展。
