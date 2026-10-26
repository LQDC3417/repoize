# 项目命令从哪里来

[English](command-evidence.md)

Repoize 读取支持的清单和配置文件，不执行发现的命令。即使有声明，命令仍可能依赖未安装的程序、损坏的脚本或不可用的服务。

| 来源类型 | 含义 | 是否进入生成指令 |
| --- | --- | --- |
| `declared` | 项目声明提供命令或具名入口 | 是 |
| `inferred` | 支持的本地配置为约定命令提供依据 | 是，附来源 |
| `suggested` | 画像或适配器提供通用建议，缺少充分项目依据 | 不进入生成指令；doctor 解释来源，旧分析报告仍可能保留命令字符串 |

所有命令均为 `verification: "not_run"`。不提供置信百分比，不声称测试通过。重复证据去重；同一命令可以保留多个来源位置。

## 证据示例

- `package.json` 的测试脚本形成包管理器命令，来源 selector 为 `scripts.test`。这不能证明脚本使用的工具已安装。
- 显式 `packageManager` 在证据无冲突时决定 JavaScript 命令使用的包管理器；否则以唯一的受支持锁文件为依据。锁文件之间冲突、或声明与锁文件不符时告警，不选择包管理器。两者均缺失时，适配器使用 npm 默认入口。
- Python 项目声明为安装命令提供依据；只有确实声明 `dev` extra 时才使用 `.[dev]`。测试或工具配置、实际依赖声明可为其他命令提供依据。
- 支持的 Go、Cargo、Maven、Gradle、Composer 等清单可提供约定的构建或测试命令。覆盖范围取决于适配器，Repoize 不理解所有构建系统。
- 仅发现源文件扩展名，不能证明项目配置了 pytest、Ruff 或开发 extra。语言画像的通用建议不进入生成指令。

查看当前仓库的实际结果：

```bash
repoize doctor /path/to/project
repoize doctor /path/to/project --format json
```

命令来源包含类型、可用时的相对路径以及 selector。selector 指向配置位置，不复制原始值。声明存在语法或结构错误时，doctor 单独报告，不回显损坏的源码行。

## 诊断规则

| 规则 | 检查对象 |
| --- | --- |
| `CFG001` | 未发现配置，或显式要求的类型缺失 |
| `CFG002` | 已知旧配置入口 |
| `CFG003` | 文件读取、UTF-8、空文件或不安全链接 |
| `CFG004` | 支持的 JSON/YAML 语法及对象结构 |
| `CFG005` | Skill 元数据和目录名匹配 |
| `CFG006` | Cursor frontmatter 及支持的字段类型 |
| `CFG007` | 空 MCP 配置或空服务条目 |
| `UPD001` | 生成标记完整性或标记与 frontmatter 重叠 |
| `SRC001` | 命令来源无法按支持的声明解析 |
| `CMD001` | 命令只有通用建议 |
| `CMD002` | 包管理器来源冲突 |

结合每条诊断的严重程度、证据和修复建议处理。规则编号表示问题类别，不是代码质量分数。参见 [CI 退出码](ci.zh-CN.md)和[支持边界](support.zh-CN.md)。

## JSON 兼容性

`analyze --format json` 保留分析 schema v1，包括五组命令字符串数组。这个兼容报告不包含新的命令证据模型。`validate` 仅校验分析报告。

Doctor 使用独立的版本化 [schema](../src/repoize/schemas/doctor.schema.json)，变更预览使用另一份 [changes schema](../src/repoize/schemas/changes.schema.json)。不要把这两种报告交给旧分析校验器，也不要将报告格式有效理解为命令已成功执行。
