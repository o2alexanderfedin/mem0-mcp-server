# MCP Server Logging and Encoding Fixes

## Issues Identified

### 1. Logging Corruption
- **Problem**: Logging output was being written to stdout, which corrupts the JSON-RPC protocol used by MCP
- **Impact**: Mixed log messages with protocol messages cause parsing errors and connection failures

### 2. Encoding Issues
- **Problem**: Improper handling of UTF-8 and special characters in messages
- **Impact**: Non-ASCII characters or control characters could break the communication protocol

## Fixes Implemented

### 1. Logging Isolation (`mem0_stdio_mcp_fixed.py`)

#### Redirect All Logging to stderr
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        # Use stderr handler to keep stdout clean for MCP protocol
        logging.StreamHandler(sys.stderr)
    ]
)
```

**Why this works:**
- stdout is reserved exclusively for JSON-RPC protocol messages
- stderr can be used for logging without interfering with the protocol
- MCP clients expect clean JSON on stdout and will parse stderr separately

### 2. Proper Encoding Configuration

#### Configure Stream Encoding
```python
# Ensure stdout is in binary mode with proper UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
```

#### Safe JSON Encoding Function
```python
def safe_json_encode(obj):
    """Safely encode objects to JSON with proper UTF-8 handling"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON encoding error: {e}")
        return json.dumps({"error": "Encoding error", "message": str(e)})
```

#### Text Response Sanitization
```python
def safe_text_response(text):
    """Ensure text responses are properly encoded"""
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    elif not isinstance(text, str):
        text = str(text)
    # Remove any control characters that might corrupt the protocol
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text
```

### 3. Enhanced Error Handling

- All tool calls wrapped in try-except blocks
- Proper error messages returned as valid JSON-RPC responses
- Graceful fallback when services are unavailable

### 4. Additional Improvements

#### Stream Management
```python
async def main():
    """Run the MCP server with stdio transport and proper stream handling"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Starting MCP server with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
```

#### Graceful Shutdown
```python
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
```

## Usage

### Running the Fixed Server

1. **Direct Python execution:**
```bash
python mem0_stdio_mcp_fixed.py
```

2. **As an MCP server in Claude Code:**
Update your MCP configuration to use the fixed script:
```json
{
  "mem0": {
    "command": "python",
    "args": ["/path/to/mem0_stdio_mcp_fixed.py"]
  }
}
```

### Debugging

To monitor the server logs without corrupting the protocol:
```bash
# Logs will appear in stderr, which can be redirected
python mem0_stdio_mcp_fixed.py 2> mcp_server.log
```

Or in real-time:
```bash
python mem0_stdio_mcp_fixed.py 2>&1 | tee mcp_server.log
```

## Key Principles for MCP Server Development

1. **Never write to stdout except for protocol messages**
   - stdout is sacred for JSON-RPC communication
   - Use stderr for all logging and debugging output

2. **Always sanitize text data**
   - Remove control characters
   - Handle encoding errors gracefully
   - Validate UTF-8 compliance

3. **Use structured error handling**
   - Return proper JSON-RPC error responses
   - Log errors to stderr for debugging
   - Never let exceptions bubble up to corrupt the protocol

4. **Test with various character sets**
   - ASCII text
   - UTF-8 with emojis and special characters
   - Binary data (should be base64 encoded)
   - Very long strings

## Testing the Fixes

### Test Script
```python
#!/usr/bin/env python3
import json
import subprocess
import sys

def test_mcp_server():
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "mem0_stdio_mcp_fixed.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }

    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()

    # Read response
    response = proc.stdout.readline()
    print(f"Response: {response}")

    # Check stderr for logs
    import select
    if select.select([proc.stderr], [], [], 0)[0]:
        logs = proc.stderr.read()
        print(f"Logs:\n{logs}")

    proc.terminate()

if __name__ == "__main__":
    test_mcp_server()
```

## Monitoring in Production

### Log Rotation
Configure log rotation to prevent disk space issues:

```bash
# /etc/logrotate.d/mcp-server
/var/log/mcp-server/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}
```

### Health Checks
Implement a health check endpoint or monitoring script:

```python
def health_check():
    """Check if MCP server is responding correctly"""
    # Send a simple request and verify response
    pass
```

## Conclusion

These fixes ensure:
1. Clean separation between protocol communication and logging
2. Proper handling of all text encodings
3. Robust error handling that doesn't break the protocol
4. Better debugging capabilities without interference

The fixed server (`mem0_stdio_mcp_fixed.py`) can be used as a drop-in replacement for the original server with improved reliability and debugging capabilities.