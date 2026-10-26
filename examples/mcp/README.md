# MCP configuration examples

[中文](README.zh-CN.md)

Repoize generates a project-level `.mcp.json` scaffold only:

```json
{
  "mcpServers": {}
}
```

No service is selected, installed, downloaded, or started. Doctor warns that an empty scaffold has no configured servers.

## Add a server you have reviewed

The following documents configuration shape. **It is not a runnable server or a recommendation to grant access.** Replace the placeholder with a server you have installed and reviewed, then decide its allowed directories, credentials, and network access yourself.

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

For a reviewed remote HTTP service, the supported client shape can include:

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

The URL is an example, not a working service. Set the named environment variable outside version control if your chosen service requires it. Do not commit a real token. Client-specific expansion and approval behavior must be checked in the [Claude MCP documentation](https://code.claude.com/docs/en/mcp).

Run `repoize doctor /path/to/project --type mcp` to check supported structure. This does not connect to a server, resolve credentials, verify a process, or prove the service is safe. Use the client's own controls for those steps.

Normal updates keep existing server definitions. `generate --type mcp --force` replaces the whole current file with the scaffold; inspect `--force --dry-run` before doing that.
