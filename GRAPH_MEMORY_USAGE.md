# Mem0 Graph Memory Usage Guide

## Overview
Our Mem0 MCP server includes full Neo4j graph memory support, automatically extracting entities and relationships from conversations to build a knowledge graph alongside vector embeddings.

## Current Setup
- **Neo4j**: Running on localhost:7687 with APOC plugins installed
- **Automatic Extraction**: Entities and relationships are extracted automatically
- **Dual Storage**: Memories are stored in both Qdrant (vector) and Neo4j (graph)
- **API Endpoint**: http://localhost:8765

## How Graph Memory Works

### 1. Automatic Entity & Relationship Extraction
When you add a memory, Mem0 automatically:
- Identifies entities (people, projects, technologies, companies)
- Extracts relationships between entities
- Creates a knowledge graph in Neo4j

### 2. Response Structure
Every memory operation returns both:
- **results**: Traditional memories (vector-stored)
- **relations**: Graph relationships (Neo4j-stored)

```json
{
  "results": [
    {"id": "...", "memory": "Manager is John Smith", "event": "ADD"}
  ],
  "relations": {
    "added_entities": [
      {"source": "john_smith", "relationship": "manages", "target": "user"}
    ]
  }
}
```

## API Usage Examples

### Adding Memories with Relationship Extraction
```bash
curl -X POST http://localhost:8765/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I work with Sarah on the AI project using Python and Neo4j"},
      {"role": "assistant", "content": "Noted that you work with Sarah on an AI project using Python and Neo4j"}
    ],
    "user_id": "alex",
    "metadata": {"context": "team_info"}
  }'
```

This automatically creates:
- Entities: `alex`, `sarah`, `ai_project`, `python`, `neo4j`
- Relationships:
  - `alex` → `works_with` → `sarah`
  - `alex` → `works_on` → `ai_project`
  - `ai_project` → `uses` → `python`
  - `ai_project` → `uses` → `neo4j`

### Retrieving Graph Relationships
```bash
curl "http://localhost:8765/memories?user_id=alex" | jq '.memories.relations'
```

Returns all graph relationships for the user.

### Searching with Graph Context
```bash
curl -X POST http://localhost:8765/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who works on AI projects?",
    "user_id": "alex",
    "limit": 5
  }'
```

The search leverages both:
- Vector similarity (semantic search)
- Graph relationships (connected entities)

## Advanced Graph Patterns

### 1. Team Relationships
```json
{
  "messages": [
    {"role": "user", "content": "John is my manager and Sarah is my colleague. We all work on Project X"}
  ]
}
```

Creates:
- `john` → `manages` → `user`
- `sarah` → `colleague_of` → `user`
- `john`, `sarah`, `user` → `works_on` → `project_x`

### 2. Technology Stack
```json
{
  "messages": [
    {"role": "user", "content": "Our stack includes React frontend, Python backend, and PostgreSQL database"}
  ]
}
```

Creates:
- `project` → `uses` → `react` (type: frontend)
- `project` → `uses` → `python` (type: backend)
- `project` → `uses` → `postgresql` (type: database)

### 3. Skills and Expertise
```json
{
  "messages": [
    {"role": "user", "content": "I'm an expert in machine learning and have 10 years of Python experience"}
  ]
}
```

Creates:
- `user` → `expert_in` → `machine_learning`
- `user` → `skilled_in` → `python` (experience: 10_years)

## Customizing Entity Extraction

You can customize how entities are extracted by modifying the graph_store config:

```python
config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "mem0password"
        },
        "custom_prompt": "Extract entities focusing on professional relationships, technologies, and projects"
    }
}
```

## Use Cases for Graph Memory

### 1. Professional Network Mapping
- Track colleagues, managers, team members
- Understand organizational structure
- Find expertise within network

### 2. Project Dependencies
- Map technologies used in projects
- Track project team members
- Understand technology relationships

### 3. Skill Inventory
- Catalog technical skills
- Track experience levels
- Find skill gaps and overlaps

### 4. Knowledge Management
- Connect related concepts
- Build domain knowledge graphs
- Track learning paths

## Querying Neo4j Directly

For advanced queries, you can connect directly to Neo4j:

```bash
# Access Neo4j Browser
open http://localhost:7474

# Login with:
# Username: neo4j
# Password: mem0password

# Example Cypher queries:

# Find all relationships for a user
MATCH (n)-[r]-(m)
WHERE n.name = 'alex'
RETURN n, r, m

# Find who works on what projects
MATCH (person)-[:works_on]->(project)
RETURN person.name, project.name

# Find technology stack
MATCH (project)-[:uses]->(tech)
RETURN project.name, COLLECT(tech.name) as technologies
```

## Best Practices

### 1. Structured Input for Better Extraction
Instead of: "I know Python"
Use: "I have 5 years of experience with Python for data science"

### 2. Explicit Relationships
Instead of: "Sarah and I are on a team"
Use: "Sarah is my teammate on the AI platform project"

### 3. Include Context
Instead of: "Working on the new feature"
Use: "I'm working with John on the authentication feature for Project X"

### 4. Consistent Entity Names
- Use full names consistently: "John Smith" not just "John"
- Use official project names: "AI Platform" not "the AI thing"
- Standardize technology names: "PostgreSQL" not "postgres" or "pg"

## Integration with Agents

Your agents can leverage graph memory by:

1. **Checking relationships**:
   ```python
   memories = mcp__mem0__mem0_search("who works on PROJECT_NAME")
   ```

2. **Finding expertise**:
   ```python
   memories = mcp__mem0__mem0_search("expert in TECHNOLOGY")
   ```

3. **Understanding context**:
   ```python
   memories = mcp__mem0__mem0_list()
   # Check relations array for entity connections
   ```

## Monitoring Graph Growth

Check graph statistics:
```bash
# Count nodes
curl -s "http://localhost:8765/memories?user_id=all" | \
  jq '.memories.relations | length'

# Unique entities
curl -s "http://localhost:8765/memories?user_id=all" | \
  jq '.memories.relations | map(.source, .target) | unique | length'
```

## Troubleshooting

### Relations Array Empty
- Ensure Neo4j is running: `docker ps | grep neo4j`
- Check APOC plugins: `docker exec mem0-neo4j ls /var/lib/neo4j/plugins/`
- Verify memory has conversational content (not just keywords)

### Slow Graph Operations
- Check Neo4j memory: `docker stats mem0-neo4j`
- Consider adding indexes for frequently queried properties
- Limit result sets with pagination

### Entity Extraction Issues
- Provide more context in messages
- Use full sentences rather than fragments
- Include role/relationship descriptors

## Summary

The graph memory feature transforms conversational data into a structured knowledge graph, enabling:
- Automatic relationship discovery
- Complex entity connections
- Semantic + graph-based search
- Persistent organizational knowledge

Use it to build intelligent systems that understand not just what is said, but how everything connects together.