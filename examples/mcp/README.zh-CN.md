# MCP 配置示例

[English](README.md)

Repoize 仅生成项目根目录 `.mcp.json` 空模板：

```json
{
  "mcpServers": {}
}
```

不自动选择、安装、下载或启动服务。Doctor 对空模板提示尚无服务器。

## 添加你已检查的服务

以下只说明配置结构，**不是可直接运行的服务，也不代表建议授予访问权限**。请换成自己已安装并检查的服务器，明确目录范围、凭据和联网权限。

```json
{
  "mcpServers": {
    "reviewed-local-server": {
      "command": "node",
      "args": ["/absolute/path/to/reviewed-server.mjs"]
    }
  }
}
```

对已检查的远程 HTTP 服务，可参考客户端结构：

```json
{
  "mcpServers": {
    "reviewed-remote-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${EXAMPLE_MCP_TOKEN}"
      }
    }
  }
}
```

URL 是示例，不是可用服务。若实际服务要求凭据，在版本控制之外设置相应环境变量，不提交真实令牌。变量展开和批准行为以 [Claude MCP 文档](https://code.claude.com/docs/en/mcp)为准。

`repoize doctor /path/to/project --type mcp` 只检查已支持的结构，不连接服务、不解析凭据、不验证进程，也不证明服务安全；后续操作由客户端自身控制。

普通更新保留已有服务器定义。`generate --type mcp --force` 会用空模板替换整份当前文件；执行前先通过 `--force --dry-run` 查看。
