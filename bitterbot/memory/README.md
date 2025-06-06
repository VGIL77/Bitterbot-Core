# BitterBot Memory System

A multi-layered memory architecture for persistent, context-aware AI interactions.

## Architecture Overview

```
BitterBot Memory System
├── Working Memory (Redis)     - Short-term session memory
├── Episodic Memory (SQLite)   - Long-term interaction storage
├── Semantic Memory (JSON)     - Knowledge graph & concepts
└── Dream Memory (JSON)        - Dream-generated insights
```

## Components

### 1. Working Memory
- **Purpose**: Short-term memory for current session
- **Storage**: Redis (with in-memory fallback)
- **TTL**: 1 hour default
- **Use Case**: Recent context, temporary state

### 2. Episodic Memory
- **Purpose**: Long-term storage of user interactions
- **Storage**: SQLite + Vector embeddings
- **Features**: 
  - Full conversation history
  - Vector similarity search
  - Curiosity scoring

### 3. Semantic Memory
- **Purpose**: Persistent knowledge base
- **Storage**: JSON (upgradeable to graph DB)
- **Features**:
  - Concept storage
  - Relationship mapping
  - Fact accumulation

### 4. Dream Memory
- **Purpose**: Store insights from dream cycles
- **Storage**: JSON logs
- **Features**:
  - Dream session logs
  - Generated insights
  - Curiosity seeds

## Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Required packages:
# - qdrant-client>=1.7.0
# - sentence-transformers>=2.2.2
# - redis>=5.0.0
# - numpy>=1.24.0
```

## Usage Example

```python
from bitterbot.memory import BitterBotMemory

# Initialize memory system
memory = BitterBotMemory(user_id="user123")

# Store an interaction
await memory.store_interaction(
    prompt="What is quantum computing?",
    response="Quantum computing is...",
    metadata={"topic": "science"}
)

# Retrieve context for new query
context = await memory.retrieve_context(
    "Tell me more about qubits",
    k=5
)
```

## Development Status

### ✅ Completed
- Directory structure
- Core module stubs
- SQLite schema
- Import structure

### 🚧 TODO
- Implement Redis connection
- Add vector search functionality
- Implement RAG pipeline
- Create dream cycle logic
- Add embedding generation
- Implement curiosity scoring

## Testing

Run the import test to verify structure:

```bash
cd bitterbot
python3 test_memory_imports.py
```

## Future Enhancements

1. **Graph Database**: Migrate semantic memory to Neo4j
2. **Distributed Storage**: Add support for distributed vector stores
3. **Memory Consolidation**: Automated memory pruning and consolidation
4. **Multi-Modal Memory**: Support for image/audio memories
5. **Federated Learning**: Share insights across BitterBot instances