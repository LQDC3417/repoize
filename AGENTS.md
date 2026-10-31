# repoize

> 本文件由 [repoize](https://github.com/LQDC3417/repoize) 初始生成，现由项目维护者维护。

## 项目概述

- **主语言**: Python

## 技术栈

- click
- rich
- jinja2


## 开发依赖

- pytest
- pytest-cov


## 常用命令

### 测试
```bash
pytest
```


## 开发环境

- 使用 Python 3.10 及以上虚拟环境；依赖和工具配置以 `pyproject.toml` 为准。
- 安装、测试和代码检查步骤见 [贡献指南](CONTRIBUTING.zh-CN.md)。
- 本机路径和环境变量由开发者自行配置，不写入共享项目指令。

## 目录结构

```
repoize/
├── src/          # 源代码
├── tests/        # 测试
└── ...
```

## 编码规范

- 代码注释使用中文，变量名和函数名使用英文
- 遵循项目已有代码风格
- 修改代码前先理解现有逻辑，保持最小化改动
- 提交前运行 lint 和测试确保通过

## 代码质量分析

本项目使用 Repoize 进行代码质量分析，包括：

### 代码统计
- 文件数、总行数、代码行、注释行、空行
- 按语言分类的文件和行数统计

### 代码质量评分
基于以下因素计算代码质量评分（0-100）：
1. 代码质量工具使用情况（20分）
2. 质量配置文件存在情况（15分）
3. 测试覆盖情况（10分）
4. CI/CD 配置情况（5分）
5. 文件大小合理性（10分）

### 支持的代码质量工具
- Python: Ruff、Mypy、Pylint、Flake8、Bandit
- JavaScript/TypeScript: ESLint、Prettier、Jest、Vitest
- Go: golangci-lint、gofmt、goimports
- Rust: cargo-clippy、cargo-fmt、cargo-audit
- Java: Checkstyle、SpotBugs、PMD、Spotless
- Ruby: RuboCop、Brakeman、bundler-audit
- PHP: PHP-CS-Fixer、PHPStan、Psalm、PHPUnit

### 使用示例
```bash
# 查看包含代码质量分析的完整报告
repoize analyze

# 输出 JSON 格式的分析结果
repoize analyze --format json --output analysis.json
```
