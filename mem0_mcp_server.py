#!/usr/bin/env python3
"""
Mem0 MCP Server
Provides memory management capabilities via Model Context Protocol
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# MCP Server mode - uses stdio for communication
class MCPServer:
    def __init__(self):
        self.api_url = "http://localhost:8765"

    async def handle_request(self, request):
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "mem0_add",
                        "description": "Add a memory to Mem0",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "messages": {"type": "array"},
                                "user_id": {"type": "string"},
                                "metadata": {"type": "object"}
                            },
                            "required": ["messages"]
                        }
                    },
                    {
                        "name": "mem0_search",
                        "description": "Search memories in Mem0",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "user_id": {"type": "string"},
                                "limit": {"type": "integer"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "mem0_get_all",
                        "description": "Get all memories from Mem0",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "mem0_delete",
                        "description": "Delete a memory from Mem0",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "memory_id": {"type": "string"}
                            },
                            "required": ["memory_id"]
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            # Import requests here to make actual API calls
            import requests

            try:
                if tool_name == "mem0_add":
                    response = requests.post(
                        f"{self.api_url}/memories",
                        json=arguments
                    )
                    return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

                elif tool_name == "mem0_search":
                    response = requests.post(
                        f"{self.api_url}/memories/search",
                        json=arguments
                    )
                    return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

                elif tool_name == "mem0_get_all":
                    user_id = arguments.get("user_id")
                    params = {"user_id": user_id} if user_id else {}
                    response = requests.get(
                        f"{self.api_url}/memories",
                        params=params
                    )
                    return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

                elif tool_name == "mem0_delete":
                    memory_id = arguments.get("memory_id")
                    response = requests.delete(
                        f"{self.api_url}/memories/{memory_id}"
                    )
                    return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

                else:
                    return {"error": f"Unknown tool: {tool_name}"}

            except Exception as e:
                return {"error": str(e)}

        elif method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "mem0-mcp-server",
                    "version": "1.0.0"
                }
            }

        else:
            return {"error": f"Unknown method: {method}"}

    async def run(self):
        """Run the MCP server using stdio"""
        while True:
            try:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Handle the request
                response = await self.handle_request(request)

                # Create JSON-RPC response
                json_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": response
                }

                # Write to stdout
                print(json.dumps(json_response))
                sys.stdout.flush()

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())