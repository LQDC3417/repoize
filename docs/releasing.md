# Release checklist / 发布清单

This roadmap does not publish tags, GitHub Releases, or PyPI packages during ordinary development. Those are explicit maintainer actions after validation.

普通开发不推送标签、不创建 GitHub Release、不发布 PyPI。以下由维护者在验收后明确执行。

## 1. Validate one commit / 验证同一提交

- Match `pyproject.toml`, `repoize.__version__`, the planned tag, wheel metadata, and source distribution metadata.
- Run pytest and Ruff, the supported CI matrix, and installed-package smoke checks outside the checkout.
- Review English/Chinese documentation, migration instructions, and actual generated paths.
- Distinguish automated format tests from client-loading results; keep unverified clients marked as such.
- A CI job that did not start, was cancelled, or failed is not a pass. Resolve account or runner problems before public release.

版本声明、计划标签、wheel 与源码包元数据必须一致。运行测试、代码检查、CI 矩阵及源码目录外的安装冒烟；核对双语文档和迁移路径。格式检查与客户端加载分开记录。CI 未启动、取消或失败不能计为通过。

## 2. Build the release artifacts / 构建发布物

Build the wheel and source distribution from the verified commit. Keep their SHA-256 checksums and the build/check logs. Verify a fresh wheel install without editable source paths or `PYTHONPATH` masking missing package resources.

从已验证提交构建 wheel 和源码包，保留 SHA-256 与验证记录。使用干净环境安装 wheel，避免 editable 源码或 `PYTHONPATH` 掩盖模板、Schema 或模块缺失。

In a clean checkout of the intended commit, with Python 3.10+ and [uv](https://docs.astral.sh/uv/) available, run:

在计划发布的干净提交中执行（Python 3.10+，已安装 uv）：

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/
python scripts/check_release.py --tag v0.3.0
uv build --out-dir ../repoize-release-dist
python scripts/check_release.py --dist ../repoize-release-dist --tag v0.3.0
uv venv ../repoize-release-smoke
python -c "from pathlib import Path; import subprocess; wheel, = Path('../repoize-release-dist').glob('*.whl'); subprocess.run(['uv', 'pip', 'install', '--python', '../repoize-release-smoke', str(wheel)], check=True)"
```

Use a new empty artifact directory for each batch. The checker requires exactly `repoize-0.3.0-py3-none-any.whl` and `repoize-0.3.0.tar.gz` (plus optional `SHA256SUMS` and uv's `.gitignore` directory marker); it checks metadata inside both archives without extracting or importing them. Wrong versions/tags, missing/extra files, or unreadable archives fail with status 1. Argument errors use status 2. Without `--dist`, success prints the source version; with it, stdout contains only checksum lines. Update the example tag when preparing a later release.

每批产物使用新的空目录。检查器要求恰好一个对应版本的 wheel 和源码包，可另含 `SHA256SUMS` 与 uv 自动生成的 `.gitignore` 目录标记；直接读取归档元数据，不解压、不导入。版本、标签、缺失/多余产物或归档损坏退出 1，参数错误退出 2。未传 `--dist` 时成功输出版本；传入后仅输出校验行。后续发布请同步示例标签。

Run the installed smoke check with the new environment's Python. It launches the installed CLI in an external temporary fixture and removes `PYTHONPATH` from that CLI's environment:

使用新环境执行冒烟脚本；脚本在外部临时样例中启动已安装 CLI，移除其 `PYTHONPATH`：

```bash
# Linux/macOS
../repoize-release-smoke/bin/python tests/smoke_installed.py
```

```powershell
# Windows PowerShell
..\repoize-release-smoke\Scripts\python.exe tests\smoke_installed.py
```

Save the successful checksum output. In Bash use `python scripts/check_release.py --dist ../repoize-release-dist > ../repoize-release-dist/SHA256SUMS`. In PowerShell, check the exit status before writing, resolve the absolute filesystem path, and explicitly use ASCII with LF line endings so GNU `sha256sum --check` reads the same filenames:

```powershell
$releaseChecksums = python scripts/check_release.py --dist ../repoize-release-dist
if ($LASTEXITCODE -ne 0) { throw "Release check failed; checksum manifest not written." }
$releaseArtifactDirectory = (Resolve-Path -LiteralPath ../repoize-release-dist).ProviderPath
[IO.File]::WriteAllText(
    (Join-Path $releaseArtifactDirectory "SHA256SUMS"),
    (($releaseChecksums -join "`n") + "`n"),
    [Text.Encoding]::ASCII
)
```

PowerShell 先确认检查器退出 0，再解析文件系统绝对路径，以 ASCII 和显式 LF 换行保存，避免 GNU `sha256sum --check` 将 CR 当作文件名的一部分。失败时产生的空文件或不完整文件不算验收通过。

Use the exact verified artifacts for both GitHub and PyPI. Do not rebuild a different package after the checks and upload it under the same version.

GitHub 与 PyPI 使用同一批已经验收的产物；不要验收一份、重建上传另一份。

## Workflow gates / 工作流阻断

The [release workflow](../.github/workflows/release.yml) calls the same [CI workflow](../.github/workflows/ci.yml): Ruff, Python 3.10–3.13 on Ubuntu, and Python 3.13 on Windows, each test job including an installed-wheel smoke check. A build job then checks source/tag agreement, builds one wheel/sdist batch from that run's commit, checks artifact metadata, installs that exact wheel, and uploads those files with SHA-256. A manually requested `workflow_dispatch` performs validation/build only, even if a tag is selected.

发布复用相同 CI 矩阵；通过后从该次运行的提交构建、校验并安装同批 wheel，再保留 wheel、源码包和 SHA-256。手动 `workflow_dispatch` 只验收和构建，即使选择标签也不发布。

Only a pushed `v*` tag can enter the GitHub publication job after every gate passes. The build jobs have `contents: read`; only the publication job has `contents: write`. Publication downloads the already checked batch, verifies its checksum lines, and attaches those exact bytes. No PyPI authentication or publishing step is configured. Ordinary branch pushes do not publish anything. No release workflow, tag, or publication was triggered while preparing this roadmap.

只有显式推送 `v*` 标签且全部阻断通过后才能进入 GitHub 发布任务。构建只有仓库读取权限，发布任务才有写权限；下载同批产物并核验 SHA 后附加原始文件。没有配置 PyPI 认证或发布步骤，本轮也没有触发发布工作流、标签或公开发布。

Action contracts reviewed on 2026-10-26 through their official versioned sources:

- [upload-artifact v7.0.2 action definition](https://github.com/actions/upload-artifact/blob/v7.0.2/action.yml): `path: release-dist/`, named upload, default `archive: true`, and error on missing files. The archive contains that directory's contents.
- [download-artifact v8.0.2 README](https://github.com/actions/download-artifact/blob/v8.0.2/README.md): selecting one artifact by name extracts directly into `path: release-dist`, without a named subdirectory, with decompression enabled by default. The wheel, sdist, and `SHA256SUMS` therefore match the publish paths.
- [action-gh-release v3.0.3 README](https://github.com/softprops/action-gh-release/blob/v3.0.3/README.md): newline-separated `files` globs, `fail_on_unmatched_files`, and required `contents: write` permission. All three newly selected majors run Node 24. Use current GitHub-hosted `ubuntu-latest`; this workflow does not promise old self-hosted runner or GitHub Enterprise Server compatibility.

上述记录只核对官方输入、归档布局和运行时要求，不代表本仓库的 GitHub 工作流已运行通过。当前验收与未验证范围见[样例验证记录](../examples/verification.md)。

## 3. Publish explicitly / 明确发布

- Finish CHANGELOG entries with the actual release date and migration notes.
- Create and push only the intended version tag; do not bulk-push unrelated tags.
- Attach the verified wheel, source distribution, and checksums to the GitHub Release.
- Publish the same artifacts to PyPI using an authorized maintainer account or separately configured trusted publisher.
- Never place a publishing credential in the repository, generated configuration, issue, or workflow output.

维护者完成 CHANGELOG 日期与升级说明，只推送本次目标标签；GitHub Release 附验收产物和校验值。PyPI 使用已授权账号或另行配置的可信发布。凭据不进入仓库、生成配置、Issue 或工作流输出。

PyPI authentication and public publication are separate from preparing a passing build. A workflow that only creates a GitHub Release does not prove a package was published to PyPI.

PyPI 认证和公开发布与本地构建准备分开；创建 GitHub Release 不能证明 PyPI 已发布。

## 4. Verify the public install / 验证公开安装

Install the exact released version from the public index in a fresh environment. Check `--version`, help, JSON/schema validation, default generation, explicit targets, doctor, preview, and drift behavior for the features available in that version.

在新环境从公开源安装指定版本，验证版本、帮助、JSON/Schema、默认与显式生成，以及该版本具备的 doctor、预览和漂移行为。

Only then update README's stable installation examples, badges, support records, and demonstration version. Until publication, label new functionality as development/source-install behavior. Do not show an unavailable PyPI command as a working quick start.

完成后再更新稳定版安装示例、徽章、支持记录与演示版本。尚未发布的功能明确标注开发版及源码安装方式，不把旧 PyPI 包没有的命令写成可用入口。

## Recovery / 问题处理

If a published artifact is wrong, preserve the evidence and follow the package index's supported removal/yank process. Fix the source and release a new version; do not silently replace an existing version. Restore a user's configuration from their reviewed backup rather than overwriting it with an unrelated template.

已发布产物有误时保留证据，按平台支持方式撤下或标记，再修复并发布新版本；不静默替换同一版本。配置问题从用户确认的备份恢复，不使用无关模板覆盖。
