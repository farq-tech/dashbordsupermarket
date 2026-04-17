# Blackbox MCP Server Setup

The Blackbox MCP (Model Context Protocol) server has been configured for this project.

## Configuration Details

- **Server Name**: blackbox
- **URL**: https://cloud.blackbox.ai/api/mcp
- **Transport**: HTTP
- **Authentication**: Bearer token

## MCP Server Location

The MCP server configuration is located at:
```
C:\Users\abdul\.cursor\projects\f-fustog\mcps\blackbox\
```

## Files Created

1. **SERVER_METADATA.json** - Contains server configuration including:
   - Server identifier
   - Server name
   - Transport type
   - API endpoint URL
   - Authorization headers

## API Key

The API key has been updated in:
- `.env` file (local configuration)
- `.env.example` file (template)
- `services/blackboxApi.ts` (fallback default)

**API Key**: `bb_7fcb12101101418cd043175d35e0e57054bb8d8f2db6391efc60a0877635e6a2`

## Usage

The MCP server should be automatically available in Cursor. You can:

1. Use MCP tools through the Cursor interface
2. Access Blackbox AI features via the MCP protocol
3. Use the `blackboxApi` service in your code

## Manual Configuration (if needed)

If the MCP server doesn't appear automatically, you may need to:

1. Restart Cursor
2. Check Cursor settings for MCP server configuration
3. Verify the server metadata file is correctly formatted

## Testing the Connection

You can test the MCP connection by:
- Checking if Blackbox tools appear in Cursor's MCP tools list
- Using the `call_mcp_tool` function with server "blackbox"
- Checking MCP resources with `list_mcp_resources`

## Troubleshooting

If the MCP server doesn't work:

1. Verify the API key is correct
2. Check that the URL is accessible
3. Ensure the SERVER_METADATA.json file is valid JSON
4. Restart Cursor to reload MCP servers
5. Check Cursor's MCP server logs for errors
