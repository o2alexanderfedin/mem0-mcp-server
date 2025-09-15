# Mem0 MCP Server with Anthropic Claude

A local Mem0 memory system configured to work with Anthropic's Claude API and MCP (Model Context Protocol).

## Features

- ✅ Vector storage with Qdrant
- ✅ Graph database with Neo4j (to be configured)
- ✅ Metadata storage with PostgreSQL
- ✅ Anthropic Claude 3.5 Sonnet integration
- ✅ MCP server for Claude Code integration

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Anthropic API key (Claude subscription)

## Quick Start

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd mem0-setup
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your MEM0_ANTHROPIC_KEY
```

3. **Start the databases**
```bash
docker compose up -d
```

4. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

5. **Run the Mem0 server**
```bash
source .env
python3 mem0_server.py
```

The server will be available at http://localhost:8765

## Architecture

- **Qdrant**: Vector database for semantic search
- **Neo4j**: Graph database for relationship storage (optional)
- **PostgreSQL**: Metadata and configuration storage
- **FastAPI**: REST API server
- **MCP**: Model Context Protocol integration

## Configuration

The system uses `MEM0_ANTHROPIC_KEY` instead of `ANTHROPIC_API_KEY` to avoid conflicts with Claude's own authentication.

## API Endpoints

- `GET /health` - Health check
- `POST /memories` - Add a memory
- `POST /memories/search` - Search memories
- `GET /memories` - Get all memories
- `PUT /memories/{memory_id}` - Update a memory
- `DELETE /memories/{memory_id}` - Delete a memory

## MCP Integration

For Claude Code integration, add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "mem0": {
      "command": "python3",
      "args": ["/path/to/mem0_stdio_mcp.py"]
    }
  }
}
```

## License

MIT