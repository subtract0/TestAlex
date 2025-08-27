# Sentry MCP Server - Installation Complete! 🎉

## What's Installed

The official **@sentry/mcp-server** (version 0.17.1) from Sentry has been successfully installed globally.

## Usage

```bash
sentry-mcp --access-token=<token> [--host=<host>|--url=<url>] [--mcp-url=<url>] [--sentry-dsn=<dsn>]
```

## Required Configuration

### 1. Get Your Sentry Access Token

1. Go to Sentry → Settings → Account → API → Auth Tokens
2. Create a new token with the necessary scopes:
   - `org:read` - Read organization data
   - `project:read` - Read project data
   - `project:write` - Update projects and issues
   - `event:read` - Read event data

### 2. Basic Usage

```bash
# Run the MCP server with your token
sentry-mcp --access-token=YOUR_SENTRY_TOKEN

# Specify a different Sentry host (if using on-premises)
sentry-mcp --access-token=YOUR_SENTRY_TOKEN --host=your-sentry-instance.com

# Use full URL for custom Sentry instance
sentry-mcp --access-token=YOUR_SENTRY_TOKEN --url=https://your-sentry-instance.com

# Optionally set a Sentry DSN for error reporting
sentry-mcp --access-token=YOUR_SENTRY_TOKEN --sentry-dsn=YOUR_DSN
```

## Integration with TestAlex

Based on the Sentry documentation, this MCP server provides:

- **Issue Access**: Access Sentry issues and errors
- **File Search**: Search for errors in specific files  
- **Project Management**: Query projects and organizations
- **DSN Management**: List and create Sentry DSN's for projects
- **AI-Powered Fixes**: Invoke Seer to automatically fix issues
- **OAuth Support**: Authenticate using your existing Sentry organization

## For MCP Clients

Configure your MCP client (like Claude Desktop) to use:

```json
{
  "mcpServers": {
    "sentry": {
      "command": "sentry-mcp",
      "args": ["--access-token=YOUR_SENTRY_TOKEN"],
      "env": {}
    }
  }
}
```

## Features Available

According to Sentry's documentation, you can now:

✅ Access Sentry issues and errors  
✅ Search for errors in specific files  
✅ Query projects and organizations  
✅ List and create Sentry DSN's for projects  
✅ Invoke Seer to automatically fix issues  
✅ Remote hosted mode (preferred) or local STDIO mode  
✅ OAuth support for seamless authentication  

## Next Steps

1. Get your Sentry access token from your Sentry account
2. Test the connection: `sentry-mcp --access-token=YOUR_TOKEN`
3. Configure your MCP client to use this server
4. Start monitoring and managing your TestAlex project errors through AI!

## Perfect for TestAlex Ecosystem

This integrates seamlessly with your:
- ACIMguide Firebase Functions error monitoring
- React Native mobile app crash tracking
- Autonomous CI/CD system for error-driven fixes
- Business intelligence for user experience optimization

The official Sentry MCP server is production-ready and maintained by Sentry themselves! 🚀
