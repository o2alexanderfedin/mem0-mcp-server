#!/usr/bin/env python3
"""
Mem0 MCP Server - STDIO Transport
Compatible with Claude Code
"""

import sys
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.server.models import InitializationOptions
import mcp.types as types
from mem0 import MemoryClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the MCP server
server = Server("mem0-mcp")

# Initialize mem0 client with local API
mem0_client = MemoryClient(api_key=os.getenv("MEM0_API_KEY", "local"))
DEFAULT_USER_ID = "claude_code_user"

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="mem0_add",
            description="Add a memory to Mem0",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The content to store in memory"},
                    "user_id": {"type": "string", "description": "User ID (optional)"},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="mem0_search",
            description="Search memories in Mem0",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "user_id": {"type": "string", "description": "User ID (optional)"},
                    "limit": {"type": "integer", "description": "Number of results"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="mem0_get_all",
            description="Get all memories from Mem0",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID (optional)"}
                }
            }
        ),
        types.Tool(
            name="mem0_delete",
            description="Delete a memory from Mem0",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "Memory ID to delete"}
                },
                "required": ["memory_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""

    try:
        if name == "mem0_add":
            content = arguments.get("content")
            user_id = arguments.get("user_id", DEFAULT_USER_ID)
            metadata = arguments.get("metadata", {})

            messages = [{"role": "user", "content": content}]
            result = mem0_client.add(messages, user_id=user_id, metadata=metadata)
            return [types.TextContent(type="text", text=json.dumps({"success": True, "result": result}))]

        elif name == "mem0_search":
            query = arguments.get("query")
            user_id = arguments.get("user_id", DEFAULT_USER_ID)
            limit = arguments.get("limit", 10)

            results = mem0_client.search(query, user_id=user_id, limit=limit)
            return [types.TextContent(type="text", text=json.dumps({"success": True, "results": results}))]

        elif name == "mem0_get_all":
            user_id = arguments.get("user_id", DEFAULT_USER_ID)

            memories = mem0_client.get_all(user_id=user_id)
            return [types.TextContent(type="text", text=json.dumps({"success": True, "memories": memories}))]

        elif name == "mem0_delete":
            memory_id = arguments.get("memory_id")

            result = mem0_client.delete(memory_id=memory_id)
            return [types.TextContent(type="text", text=json.dumps({"success": True, "result": result}))]

        else:
            return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    """Run the MCP server with stdio transport"""
    transport = StdioServerTransport()

    # Run the server
    await server.run(
        transport,
        InitializationOptions(
            server_name="mem0-mcp",
            server_version="1.0.0"
        )
    )

if __name__ == "__main__":
    asyncio.run(main())