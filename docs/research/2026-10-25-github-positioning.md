# Repoize：GitHub 项目对照与产品路线

调研日期：2026-10-25。范围：官方仓库 README、文档、源码与 GitHub API；未使用第三方榜单。
本轮仅调查和路线建议，不修改产品代码，不提交或发布。

## 结论与证据边界

**建议先把 Repoize 做成“从仓库事实生成、检查并安全更新 Agent 上下文”的可靠工具。**
先修兼容性基线，再交付有依据的检查和可审阅的更新；暂缓扩展成规则同步平台、源码打包器或需求管理平台。

- **事实**：Repoize 已有扫描、命令提取、多目标生成、JSON 输出和保留手写区间的更新实现；不是从零起步。[本地 README](../../README.md)、[更新实现](../../src/repoize/generator/base.py)。
- **事实**：直接竞品已覆盖较多同步目标和安全写入功能；单纯多生成几种配置不足以形成明显区分。[Rulesync](https://github.com/dyoshikawa/rulesync#readme)、[Ruler](https://github.com/intellectronica/ruler#readme)。
- **推断**：Repoize 更值得验证的价值是“提取事实 → 说明依据 → 检查有效性 → 安全更新”，尤其适合已有项目首次接入 Agent，以及维护配置的人。
- **未知**：没有用户访谈、留存、下载转化或功能实验数据，不能确定哪项功能会带来 star；高 star 只用于选择参考项目。
- **边界**：下述兼容性问题由源码和规范对照得到，未在真实客户端完整加载验证；不把规范风险写成已证实运行失败。

## 样本：直接竞品与邻近项目分开看

数字为 2026-10-25 主线程读取 GitHub 官方 API 的快照，后续会变化；不是增长因果证据。

| 类别 | 项目 | Stars | 主要用户任务 | 对 Repoize 的意义 |
|---|---|---:|---|---|
| 直接 | [dyoshikawa/rulesync](https://api.github.com/repos/dyoshikawa/rulesync) | 1,552 | 统一规则、导入、转换并分发到多种 Agent | 多工具同步已有成熟覆盖 |
| 直接 | [intellectronica/ruler](https://api.github.com/repos/intellectronica/ruler) | 2,951 | 集中编写规则，应用到不同 Agent | 安全应用与恢复已有参照 |
| 邻近 | [yamadashy/repomix](https://api.github.com/repos/yamadashy/repomix) | 29,014 | 把仓库打包成可交给 LLM 的上下文 | 学习低门槛试用与明确输出 |
| 邻近 | [coderamp-labs/gitingest](https://api.github.com/repos/coderamp-labs/gitingest) | 16,004 | 从 URL 或本地目录提取代码摘要 | 学习一眼能理解的核心动作 |
| 邻近 | [github/spec-kit](https://api.github.com/repos/github/spec-kit) | 142,795 | 给 Agent 提供结构化过程、模板与产物 | 学习按任务展示价值 |
| 邻近 | [Fission-AI/OpenSpec](https://api.github.com/repos/Fission-AI/OpenSpec) | 72,936 | 把需求、方案、任务和变更落成可审阅文件 | 学习展示完整使用结果 |

Gitingest 当前 canonical 仓库是 `coderamp-labs/gitingest`；旧的 `cyclotruc/gitingest` 地址会重定向。[官方仓库](https://github.com/coderamp-labs/gitingest)。

### 直接竞品：哪些能力已经存在

**Rulesync，事实**：围绕统一规则文件生成多种目标；既能导入已有配置，也支持直接 `convert`，不要求每次都采用统一源目录。[官方快速开始](https://github.com/dyoshikawa/rulesync#readme)。
它的工具矩阵还区分规则、MCP、skills 等能力及作用模式；目标覆盖数量已经不是空白市场。[官方支持矩阵](https://rulesync.dyoshikawa.com/reference/supported-tools.html)。

**Ruler，事实**：集中规则后执行 `apply`；提供 `--dry-run`、默认备份与 `revert`，还支持 MCP 合并和嵌套规则；嵌套模式在文档中标为实验性。[官方 README](https://github.com/intellectronica/ruler#readme)。

**推断**：Repoize 不宜把“多 Agent”“预览”“doctor”分别宣传为独有发明。更可检验的定位是：比手写规则分发更擅长提取项目事实，并把生成内容与依据联系起来。
这不是断言竞品完全没有分析或检查能力；本轮未逐模块审计竞品全部源码。

### 邻近项目：学入口，避免复制整个产品

- **Repomix，事实**：把仓库打包为一个 AI 友好的文件，支持 token 统计、过滤与敏感信息检测；`npx repomix@latest` 和网页是直接试用入口。[官方 README](https://github.com/yamadashy/repomix#readme)、[入门文档](https://repomix.com/guide/)。
- **Gitingest，事实**：核心是从仓库 URL 或目录得到文本摘要；同时提供 CLI 与 Python 接口，主页用替换 URL 中的 `hub` 为 `ingest` 解释入口。[官方 README](https://github.com/coderamp-labs/gitingest#readme)。
- **Spec Kit，事实**：当前 README 按功能开发、修复问题、评估想法等任务组织入口，提供结构化过程、模板和记录下来的产物。[官方 README](https://github.com/github/spec-kit#readme)。
- **OpenSpec，事实**：README 用一次变更演示提案、规格、设计、任务、实施和归档；初始化会按所选工具提供对应调用形式。[官方 README](https://github.com/Fission-AI/OpenSpec#readme)。

**推断**：这些项目共同值得借鉴的是清晰的“输入 → 动作 → 可见结果”，不能据此断言其某个功能造成高 star。Repoize 可以成为这些工作流之前的仓库事实准备工具，不必包办后续开发过程。

## 对照本地实现：五个实际用户任务

| 用户想完成的任务 | 当前事实 | 差异与建议 | 可验收结果 |
|---|---|---|---|
| 我接手一个已有仓库，先知道 Agent 能读到什么 | scanner 主要判断已知路径是否存在；`check` 使用现有评分 | 从“存在率”走向有效性检查，展示路径、格式、规则依据 | 空文件、坏 JSON、旧路径与正常配置给出不同结果 |
| 我想知道生成的测试命令从哪里来 | 命令从项目配置和语言默认值提取，输出尚未逐项带来源 | 保留来源文件与提取方式，明确区分发现、默认建议、未验证 | 显示 `package.json:scripts.test` 等依据；不声称命令已执行 |
| 我怕初始化覆盖原有团队规范 | 标记区间更新保留区间外内容；已有文件可跳过 | 在现有机制上加只读预览，先呈现新增、修改、跳过与冲突 | 预览前后文件字节不变；实际结果与预览一致 |
| 我用当前 Cursor/Claude/Skills，生成后希望直接被发现 | 当前仍输出 `.cursorrules`、`.claude/mcp.json`；Skill 包装存在规范风险 | 优先完成当前格式与路径兼容，逐项记录支持范围 | 规范校验和固定样本通过；客户端验证另列状态 |
| 仓库结构或脚本变了，我想知道说明是否过期 | 已有 `update`，未见只读漂移判定入口 | 后续把重新分析结果与受管区间比较，复用生成器 | 仅受管内容变化时报告漂移；手写区变化不误报 |

依据：[配置扫描](../../src/repoize/analyzer/config_scanner.py)、[命令提取](../../src/repoize/analyzer/cmd_extractor.py)、[更新逻辑](../../src/repoize/generator/base.py)、[CLI check](../../src/repoize/cli.py)、[分析评分](../../src/repoize/analyzer/project_analyzer.py)。

## 先修的兼容性基线

1. **Claude MCP 路径**：本地生成器写 `.claude/mcp.json`；官方文档的项目级配置是根目录 `.mcp.json`。先核定支持范围和迁移方式，再更新生成与扫描，保护旧文件。[本地生成器](../../src/repoize/generator/mcp_config.py)、[官方项目作用域](https://code.claude.com/docs/en/mcp#project-scope)。
2. **Cursor 当前格式**：本地以 `.cursorrules` 为目标；官方当前规则文档介绍 `.cursor/rules`。新增当前格式支持，并把旧格式兼容与迁移说清楚。[本地生成器](../../src/repoize/generator/cursorrules.py)、[Cursor 规则](https://cursor.com/docs/rules)。
3. **Skill 文件结构**：模板原本以 YAML frontmatter 开头，但通用 `generate_marked()` 会在其前插 HTML；输出目录固定 `project-dev`，name 却由项目名生成。应让首部和目录名满足规范，同时保留安全更新能力。[本地 Skill 生成器](../../src/repoize/generator/skill_md.py)、[模板](../../src/repoize/templates/skill_md.j2)、[通用包装](../../src/repoize/generator/base.py)、[Agent Skills 规范](https://agentskills.io/specification)。

这三项是发布承诺的基础，不应被包装成“AI 一定正确加载”。格式正确与客户端实际采用是不同层次；后者需用明确版本做人工验证。

## 最小版本：只做三项能力

### P0：当前目标兼容与诚实报告

- 完成上面的路径、格式和 Skill 修复；联动扫描器、生成器、模板、样例、文档及针对性回归。
- 把“发现文件”和“配置有效”分开；不要因空配置存在就宣传“完备、100% 就绪”。
- 建立简短支持表：客户端、路径、格式依据、最近规范核对日期、是否做过实际加载。
- 正式推广前对齐发布物：主线程现场核对为 PyPI/Release 仍是 0.1.0、本地源码为 0.1.1；先检查安装后的真实行为和 README 承诺，再由用户决定发布。[PyPI 元数据](https://pypi.org/pypi/repoize/json)、[GitHub Releases](https://api.github.com/repos/LQDC3417/repoize/releases)。
- **验收**：已有文件不被静默迁移或覆盖；无效样本被识别；正常样本生成正确；针对性回归通过。

### P1：有依据的只读检查

- 从少量高价值问题开始：当前支持路径、可解析性、Skill 必填项/目录匹配、已知旧格式。
- 按用户实际使用的目标检查；仅使用一个 Agent 的仓库不应因缺少其他工具配置而被判不完备。
- 每条发现包含规则 ID、严重程度、文件路径、依据和修复建议；避免再加一个缺乏依据的综合分。
- 在已有命令提取结果中先保留“来源文件/默认建议”的区别；未知信息明确显示未知。
- 保留现有 `check` 使用体验；新增机器输出和失败状态前，写清兼容策略，不突然改变脚本行为。
- **验收**：同一固定样本重复检查结果稳定；不执行仓库脚本、不修改文件；JSON 可消费。

### P1：受管内容的更新预览

- 复用现有生成和合并逻辑，显示哪些文件新增、哪些受管区间变化、哪些被跳过及哪些冲突。
- 预览不写文件；实际写入仍遵循现有手写内容保护原则，JSON 冲突不自动覆盖用户值。
- **验收**：预览前后字节一致；实际更改与预览一致；再次运行无新增差异；CRLF 与手写区保留。

顺序：先 P0，再检查与预览。每项单独可发布和试用，不等完整平台做完。

## 明确后延

- 更多语言、几十个 Agent 目标、完整双向规则同步：直接竞品已有广覆盖，先证明核心输出可靠。
- Monorepo 分层配置：先收集真实多包仓库样本；作用域和继承容易产生错误承诺。
- 漂移 CI / GitHub Action：待只读比较与退出状态稳定后再封装；第一步可先给工作流示例。
- 全仓 token 打包、压缩、远程仓库托管网页：与 Repomix/Gitingest 重叠，成本明显超过当前主线。
- Prompt/Skill 商店、MCP 推荐安装、自动执行测试、LLM 自动写业务规则：边界更大，当前没有需求证据。
- Spec Kit/OpenSpec 式完整需求工作流：以文档说明如何互补即可，不重做其平台。

## GitHub 展示与试用：可以立刻落地的改进

以下是建议，本轮未修改 README、仓库设置或发布材料。

1. **首屏说清产出**：用一句具体描述，加扫描结果与生成片段对照；避免只说“立即理解项目”。保留中文，英文入口放到首屏；可拆出独立英文 README。[当前 README](../../README.md)。
2. **先读后写**：先展示现有 `repoize analyze --no-env`，再展示选择性生成和安全更新；新预览完成后再把它加入演示。不要在文档提前写不存在的命令。[当前 CLI](../../src/repoize/cli.py)。
3. **可复制体验**：准备一个无密钥的极小公开样例，展示真实终端录制；用户能核对输入、输出和差异。README 放短演示，详细报告另链，控制首屏长度。
4. **一次性运行入口**：核验发布包后提供 `uvx repoize --help` 等短路径，并说明前置条件；保留 pip 安装。不要假定用户已有 uv，也不要把安装过程做成主产品。
5. **为什么选 Repoize**：用三行说明“从项目事实生成”“检查依据可见”“保留团队手写内容”，再诚实链接 Rulesync/Ruler；需要同步现成规则的人可以直接选它们。
6. **完善发现入口**：当前 API 快照中 Repoize 为 1 star、0 fork、topics 为空、homepage 为空。可先补准确 description、少量真实 topic 和 README 文档链接；这是元数据整理，不是增长保证。[官方 API](https://api.github.com/repos/LQDC3417/repoize)、[GitHub Topics 说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)。
7. **开放具体贡献入口**：给出“提交一种误识别配置的最小样例”“补一个客户端验证记录”等小任务；issue 模板要求版本、输入、预期、实际结果并提示脱敏。

展示参考：Repomix 的一条运行命令、Gitingest 的 URL 动作、OpenSpec 的变更产物演示、Spec Kit 的任务入口；这些都是可观察设计，不是其增长原因的证明。[Repomix](https://repomix.com/guide/)、[Gitingest](https://github.com/coderamp-labs/gitingest#readme)、[OpenSpec](https://github.com/Fission-AI/OpenSpec#readme)、[Spec Kit](https://github.com/github/spec-kit#readme)。

## 怎么判断路线值得继续

- 先请真实维护者用已有仓库完成“分析 → 看懂依据 → 预览 → 生成/更新”，记录卡点；不默认上传代码或加入遥测。
- 首要记录成功生成、误报/漏报、覆盖事故、用户能否解释输出；star 和下载作为辅助信号。
- 分版本只改变一个明确入口或能力，记录展示日期、反馈和回访；小样本只做方向判断，不虚构转化率或因果结论。
- 获得可靠复现样例后再扩语言和目标；若用户主要需要规则同步，则优先考虑互操作，不继续堆同类功能。
- 推广以有实质内容的示例、修复记录和适合场景的分享为主；不做互 star、虚假 star 或批量骚扰。

## 本轮验证与未覆盖

已读本地 README、核心扫描/命令提取/评分/生成/更新实现；通过 GitHub 官方 README、文档与 API 对照六个项目。
未修改产品、未跑全量测试、未执行竞品安装、未做真实客户端加载或用户增长实验；上述路线仍需用户场景验证。
