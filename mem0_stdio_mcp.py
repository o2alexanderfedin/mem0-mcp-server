#!/usr/bin/env python3
"""
Mem0 MCP Server - STDIO Transport for Claude Code
Properly integrated with Mem0 to support both vector and graph storage
"""

import asyncio
import os
import logging
import json
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from mem0 import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the MCP server
server = Server("mem0-mcp")

# Configuration for Mem0 with Anthropic and Neo4j - same as REST server
config = {
    "llm": {
        "provider": "litellm",
        "config": {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": os.getenv("MEM0_ANTHROPIC_KEY")
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": int(os.getenv("QDRANT_PORT", 6333)),
            "embedding_model_dims": 384
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": f"bolt://{os.getenv('NEO4J_HOST', 'localhost')}:{os.getenv('NEO4J_PORT', 7687)}",
            "username": os.getenv("NEO4J_USER", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", "mem0password")
        }
    },
    "db": {
        "provider": "postgres",
        "config": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5433)),
            "user": os.getenv("POSTGRES_USER", "mem0"),
            "password": os.getenv("POSTGRES_PASSWORD", "mem0password"),
            "database": os.getenv("POSTGRES_DB", "mem0db")
        }
    }
}

# Initialize Mem0 with full configuration
try:
    memory = Memory.from_config(config_dict=config)
    logger.info("Mem0 initialized successfully with Anthropic API and Neo4j graph store")
except Exception as e:
    logger.error(f"Failed to initialize Mem0: {e}")
    memory = None
    # Fallback to simple storage if initialization fails
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

    # Use default user_id for MCP operations
    default_user_id = "alexander_fedin"

    if not memory:
        return [types.TextContent(
            type="text",
            text="Memory service not initialized. Please check database connections."
        )]

    try:
        if name == "mem0_add":
            content = arguments.get("content")
            tags = arguments.get("tags", [])

            # Create messages format that Mem0 expects for proper graph extraction
            messages = [
                {"role": "user", "content": content},
                {"role": "assistant", "content": f"I'll remember that: {content}"}
            ]

            # Use memory.add with messages format to trigger graph extraction
            result = memory.add(
                messages=messages,
                user_id=default_user_id,
                metadata={"tags": tags} if tags else None
            )

            # Format the response to include graph relationships if present
            response_text = f"Added memory: {content}"

            if isinstance(result, dict):
                # Extract memory IDs if available
                if "results" in result and result["results"]:
                    for mem in result["results"]:
                        if "id" in mem:
                            response_text = f"Added memory [{mem['id']}]: {content}"
                            break

                # Show graph relationships - handle nested list structure
                if "relations" in result and result["relations"]:
                    relations = result["relations"]
                    if relations.get("added_entities") and relations["added_entities"]:
                        response_text += "\n\nGraph relationships created:"
                        for rel_item in relations["added_entities"]:
                            # Each rel_item is a list containing a dict
                            if isinstance(rel_item, list) and rel_item:
                                rel = rel_item[0] if isinstance(rel_item[0], dict) else {}
                            elif isinstance(rel_item, dict):
                                rel = rel_item
                            else:
                                continue
                            if rel:
                                response_text += f"\n  - {rel.get('source', 'N/A')} → {rel.get('relationship', 'N/A')} → {rel.get('target', 'N/A')}"

            return [types.TextContent(type="text", text=response_text)]

        elif name == "mem0_search":
            query = arguments.get("query", "")

            results = memory.search(
                query=query,
                user_id=default_user_id,
                limit=10
            )

            if results and isinstance(results, dict):
                memories_list = results.get("results", [])
                if memories_list:
                    result_text = f"Found {len(memories_list)} memories:\n"
                    for mem in memories_list:
                        score = mem.get('score', 0)
                        result_text += f"- [{mem.get('id', 'N/A')}] {mem.get('memory', mem.get('text', 'N/A'))} (score: {score:.2f})\n"
                    return [types.TextContent(type="text", text=result_text)]
                else:
                    return [types.TextContent(type="text", text="No memories found matching your query")]
            else:
                return [types.TextContent(type="text", text="No memories found matching your query")]

        elif name == "mem0_list":
            results = memory.get_all(user_id=default_user_id)

            if results:
                # Check if results contain both memories and relations
                if isinstance(results, dict) and "results" in results:
                    memories_list = results["results"]
                    relations = results.get("relations", [])
                else:
                    memories_list = results
                    relations = []

                if memories_list:
                    result_text = f"All memories ({len(memories_list)}):\n"
                    for mem in memories_list:
                        result_text += f"- [{mem.get('id', 'N/A')}] {mem.get('memory', mem.get('text', 'N/A'))}\n"

                    # Add graph relationships if present
                    if relations:
                        result_text += "\nGraph relationships:\n"
                        for rel in relations:
                            result_text += f"  - {rel.get('source', 'N/A')} → {rel.get('relationship', 'N/A')} → {rel.get('target', 'N/A')}\n"

                    return [types.TextContent(type="text", text=result_text)]
                else:
                    return [types.TextContent(type="text", text="No memories stored yet")]
            else:
                return [types.TextContent(type="text", text="No memories stored yet")]

        elif name == "mem0_delete":
            memory_id = arguments.get("memory_id")

            result = memory.delete(memory_id=memory_id)

            return [types.TextContent(
                type="text",
                text=f"Deleted memory {memory_id}"
            )]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

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