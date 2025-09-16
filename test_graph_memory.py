#!/usr/bin/env python3
"""Test script for Mem0 Graph Memory features"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8765"

def add_memory_with_relationships():
    """Add memories that should create graph relationships"""

    # Test data with relationships
    test_memories = [
        {
            "messages": [
                {"role": "user", "content": "I'm Alexander Fedin, a software engineer working at TechCorp"},
                {"role": "assistant", "content": "Nice to meet you Alexander! Being a software engineer at TechCorp sounds interesting."}
            ],
            "user_id": "alexander",
            "metadata": {"source": "introduction"}
        },
        {
            "messages": [
                {"role": "user", "content": "I specialize in Python, JavaScript, and cloud architecture using AWS"},
                {"role": "assistant", "content": "Great skill set! Python, JavaScript and AWS cloud architecture are in high demand."}
            ],
            "user_id": "alexander",
            "metadata": {"source": "skills"}
        },
        {
            "messages": [
                {"role": "user", "content": "I'm working on an AI project that uses LangChain and Neo4j for knowledge graphs"},
                {"role": "assistant", "content": "That's an interesting combination - LangChain for AI orchestration with Neo4j for knowledge graphs."}
            ],
            "user_id": "alexander",
            "metadata": {"source": "current_project"}
        },
        {
            "messages": [
                {"role": "user", "content": "My colleague Sarah also works on the AI project. She handles the frontend using React"},
                {"role": "assistant", "content": "It's good to have Sarah handling the React frontend while you work on the AI backend."}
            ],
            "user_id": "alexander",
            "metadata": {"source": "team"}
        }
    ]

    print("Adding memories with relationships...")
    for memory_data in test_memories:
        response = requests.post(f"{BASE_URL}/memories", json=memory_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added memory: {memory_data['metadata']['source']}")
            if 'result' in result and 'relations' in result['result']:
                print(f"   Relations: {json.dumps(result['result']['relations'], indent=2)}")
        else:
            print(f"❌ Failed to add memory: {response.text}")

def get_graph_relationships(user_id="alexander"):
    """Retrieve all memories and their graph relationships"""

    print(f"\nRetrieving graph relationships for user: {user_id}")
    response = requests.get(f"{BASE_URL}/memories", params={"user_id": user_id})

    if response.status_code == 200:
        data = response.json()

        # Display memories
        print("\n📝 Memories:")
        for memory in data['memories']['results']:
            print(f"  - {memory['memory']}")

        # Display relationships
        print("\n🔗 Graph Relationships:")
        relations = data['memories'].get('relations', [])

        # Group relationships by source
        grouped = {}
        for rel in relations:
            source = rel['source']
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(f"{rel['relationship']} → {rel['target']}")

        for source, rels in grouped.items():
            print(f"\n  {source}:")
            for rel in rels:
                print(f"    • {rel}")
    else:
        print(f"❌ Failed to retrieve memories: {response.text}")

def search_graph_memory(query, user_id="alexander"):
    """Search memories using semantic search"""

    print(f"\n🔍 Searching for: '{query}'")

    search_data = {
        "query": query,
        "user_id": user_id,
        "limit": 5
    }

    response = requests.post(f"{BASE_URL}/memories/search", json=search_data)

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        print(f"Found {len(results)} relevant memories:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['memory']} (relevance: {result.get('score', 'N/A')})")
    else:
        print(f"❌ Search failed: {response.text}")

def test_relationship_queries():
    """Test various relationship-based queries"""

    queries = [
        "Who works on AI projects?",
        "What technologies does Alexander know?",
        "Who are the team members?",
        "What is the tech stack?",
        "Who works with React?",
        "What cloud platforms are used?"
    ]

    print("\n📊 Testing relationship queries:")
    for query in queries:
        search_graph_memory(query)
        print()

if __name__ == "__main__":
    print("🧪 Testing Mem0 Graph Memory Features")
    print("=" * 50)

    # Add memories with relationships
    add_memory_with_relationships()

    # Retrieve and display graph
    get_graph_relationships()

    # Test search queries
    test_relationship_queries()

    print("\n✅ Graph memory test complete!")