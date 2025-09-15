#!/usr/bin/env python3
"""
Mem0 MCP Server - STDIO Transport for Claude Code
Based on official MCP examples
"""

import asyncio
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Load environment variables
load_dotenv()

# Initialize the MCP server
server = Server("mem0-mcp")

# For now, we'll use simple in-memory storage instead of the full Mem0 client
# This can be upgraded to use the Mem0 API later
memories = {}
memory_counter = 0

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="mem0_add",
            description="Add a memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The content to store in memory"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="mem0_search",
            description="Search memories",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="mem0_list",
            description="List all memories",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="mem0_delete",
            description="Delete a memory",
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
    global memory_counter, memories

    if name == "mem0_add":
        content = arguments.get("content")
        tags = arguments.get("tags", [])
        memory_id = f"mem_{memory_counter}"
        memory_counter += 1

        memories[memory_id] = {
            "id": memory_id,
            "content": content,
            "tags": tags
        }

        return [types.TextContent(
            type="text",
            text=f"Added memory {memory_id}: {content}"
        )]

    elif name == "mem0_search":
        query = arguments.get("query", "").lower()
        results = []

        for mem_id, memory in memories.items():
            if query in memory["content"].lower():
                results.append(memory)

        if results:
            result_text = "\n".join([f"- [{m['id']}] {m['content']}" for m in results])
            return [types.TextContent(type="text", text=f"Found {len(results)} memories:\n{result_text}")]
        else:
            return [types.TextContent(type="text", text="No memories found matching your query")]

    elif name == "mem0_list":
        if memories:
            result_text = "\n".join([f"- [{m['id']}] {m['content']}" for m in memories.values()])
            return [types.TextContent(type="text", text=f"All memories:\n{result_text}")]
        else:
            return [types.TextContent(type="text", text="No memories stored yet")]

    elif name == "mem0_delete":
        memory_id = arguments.get("memory_id")
        if memory_id in memories:
            deleted = memories.pop(memory_id)
            return [types.TextContent(type="text", text=f"Deleted memory {memory_id}: {deleted['content']}")]
        else:
            return [types.TextContent(type="text", text=f"Memory {memory_id} not found")]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server with stdio transport"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())