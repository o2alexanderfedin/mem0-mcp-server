#!/usr/bin/env python3
"""
Mem0 MCP Server with Anthropic API
Provides memory management capabilities via Model Context Protocol
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from mem0 import Memory
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for Mem0 with Anthropic and Neo4j
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
            "port": int(os.getenv("QDRANT_PORT", 6333))
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
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "user": os.getenv("POSTGRES_USER", "mem0"),
            "password": os.getenv("POSTGRES_PASSWORD", "mem0password"),
            "database": os.getenv("POSTGRES_DB", "mem0db")
        }
    }
}

# Initialize FastAPI app
app = FastAPI(title="Mem0 MCP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mem0
try:
    memory = Memory.from_config(config_dict=config)
    logger.info("Mem0 initialized successfully with Anthropic API and Neo4j graph store")
except Exception as e:
    logger.error(f"Failed to initialize Mem0: {e}")
    memory = None

# Request/Response Models
class AddMemoryRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    limit: Optional[int] = 10

class UpdateMemoryRequest(BaseModel):
    memory_id: str
    data: str

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if memory else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "backend": "Anthropic Claude 3.5 Sonnet",
        "graph_store": "Neo4j",
        "vector_store": "Qdrant"
    }

@app.post("/memories")
async def add_memory(request: AddMemoryRequest):
    """Add a new memory"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        result = memory.add(
            messages=request.messages,
            user_id=request.user_id,
            agent_id=request.agent_id,
            metadata=request.metadata
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/search")
async def search_memories(request: SearchMemoryRequest):
    """Search memories"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        results = memory.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.agent_id,
            limit=request.limit
        )
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories")
async def get_all_memories(user_id: Optional[str] = None, agent_id: Optional[str] = None):
    """Get all memories for a user or agent"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        results = memory.get_all(user_id=user_id, agent_id=agent_id)
        return {"success": True, "memories": results}
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memories/{memory_id}")
async def update_memory(memory_id: str, request: UpdateMemoryRequest):
    """Update a memory"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        result = memory.update(memory_id=memory_id, data=request.data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        result = memory.delete(memory_id=memory_id)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories")
async def delete_all_memories(user_id: Optional[str] = None, agent_id: Optional[str] = None):
    """Delete all memories for a user or agent"""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory service not initialized")

    try:
        result = memory.delete_all(user_id=user_id, agent_id=agent_id)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error deleting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8765))
    uvicorn.run(app, host="0.0.0.0", port=port)