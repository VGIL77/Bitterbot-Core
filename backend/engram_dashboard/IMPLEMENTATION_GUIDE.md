# Engram System Implementation Guide

## Quick Start: Critical Fixes

### 1. Fix Database Schema (Immediate)
```bash
# Run the migration fix
psql -d your_database -f backend/supabase/migrations/20250613_engrams_table_fix.sql
```

### 2. Update Dependencies
```bash
pip install tiktoken==0.5.2 sentence-transformers==2.2.2 redis==5.0.1 tenacity==8.2.3
```

### 3. Switch to Improved Engram Manager
```python
# In backend/agentpress/context_manager.py
# Replace:
from .engram_manager import get_engram_manager

# With:
from .engram_manager_improved import get_improved_engram_manager as get_engram_manager
```

## Feature Implementation Guide

### Enable Dream Engine
```python
# In your main server startup (e.g., backend/server.py)
from bitterbot.memory.dream_engine.dream_cycle_enhanced import EnhancedDreamCycle

# Add to your application startup
async def start_dream_engine(app):
    memory_system = app['memory_system']  # Your memory instance
    dream_engine = EnhancedDreamCycle(memory_system)
    
    # Start dreaming after 5 minutes of idle
    asyncio.create_task(dream_engine.start_dreaming())
    app['dream_engine'] = dream_engine

# Add to shutdown
async def stop_dream_engine(app):
    if 'dream_engine' in app:
        app['dream_engine'].stop_dreaming()
```

### Add Redis Caching
```python
# config.py
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True
}

# In engram_manager_improved.py __init__
import redis.asyncio as redis
self.redis_client = redis.Redis(**REDIS_CONFIG)
```

### Enable Vector Search with pgvector
```sql
-- Add to your database
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE engrams 
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS idx_engrams_embedding 
ON engrams USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Testing Your Implementation

### 1. Test Engram Creation
```python
# test_engram_creation.py
import asyncio
from backend.agentpress.engram_manager_improved import get_improved_engram_manager

async def test_engram_creation():
    manager = get_improved_engram_manager()
    
    test_messages = [
        {'content': {'role': 'user', 'content': 'How do I implement a REST API?'}},
        {'content': {'role': 'assistant', 'content': 'Here\'s how to implement a REST API...'}},
        {'content': {'role': 'user', 'content': 'What about authentication?'}}
    ]
    
    engram = await manager.create_engram_with_embeddings(
        thread_id='test-thread-123',
        messages=test_messages,
        trigger='manual_test'
    )
    
    print(f"Created engram: {engram['id']}")
    print(f"Token count: {engram['token_count']}")
    print(f"Compression ratio: {engram['token_count'] / engram['metadata']['summary_tokens']:.1f}:1")

asyncio.run(test_engram_creation())
```

### 2. Test Retrieval with Embeddings
```python
async def test_retrieval():
    manager = get_improved_engram_manager()
    
    engrams = await manager.retrieve_with_embeddings(
        thread_id='test-thread-123',
        query_context='How do I handle API authentication?',
        limit=3
    )
    
    for i, engram in enumerate(engrams):
        print(f"\nEngram {i+1}:")
        print(f"  Score: {engram.get('semantic_similarity', 0):.3f}")
        print(f"  Content: {engram['content'][:100]}...")
```

### 3. Test Dream Cycle
```python
async def test_dream_cycle():
    from bitterbot.memory.dream_engine.dream_cycle_enhanced import EnhancedDreamCycle
    
    # Mock memory system
    class MockMemory:
        pass
    
    dream_engine = EnhancedDreamCycle(MockMemory())
    
    # Trigger a single dream cycle
    await dream_engine._dream_cycle()
    
    # Get insights
    insights = await dream_engine.get_dream_insights()
    print(f"Generated {len(insights)} insights")

asyncio.run(test_dream_cycle())
```

## Monitoring and Metrics

### Enable Prometheus Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
engram_created_total = Counter('engram_created_total', 'Total engrams created', ['trigger'])
engram_retrieval_duration = Histogram('engram_retrieval_duration_seconds', 'Engram retrieval duration')
active_engrams = Gauge('active_engrams_total', 'Total active engrams', ['thread_id'])

# Use in your code
engram_created_total.labels(trigger='token_threshold').inc()

with engram_retrieval_duration.time():
    engrams = await manager.retrieve_with_embeddings(...)
```

### Dashboard Enhancements
```javascript
// Add to neural-viz.js for better visualization
class EngramNetwork {
    constructor() {
        this.nodes = new Map();  // engram_id -> node data
        this.edges = new Map();  // connection_id -> edge data
    }
    
    addEngram(engram) {
        this.nodes.set(engram.id, {
            id: engram.id,
            relevance: engram.relevance_score,
            surprise: engram.surprise_score,
            position: this.calculatePosition(engram),
            color: this.getColorBySurprise(engram.surprise_score)
        });
    }
    
    addConnection(connection) {
        this.edges.set(connection.id, {
            source: connection.engram1_id,
            target: connection.engram2_id,
            strength: connection.similarity,
            type: connection.connection_type
        });
    }
}
```

## Performance Optimization Tips

1. **Batch Engram Updates**
```python
async def batch_update_access_patterns(engram_ids):
    # Use PostgreSQL's unnest for batch updates
    query = """
        UPDATE engrams 
        SET access_count = access_count + 1,
            last_accessed = NOW(),
            relevance_score = LEAST(relevance_score + 0.2, 5.0)
        WHERE id = ANY($1::uuid[])
    """
    await db.execute(query, engram_ids)
```

2. **Cache Embeddings**
```python
# Use Redis with TTL
async def get_cached_embedding(text_hash):
    cached = await redis_client.get(f"emb:{text_hash}")
    if cached:
        return np.frombuffer(cached, dtype=np.float32)
    return None

async def cache_embedding(text_hash, embedding, ttl=3600):
    await redis_client.setex(
        f"emb:{text_hash}", 
        ttl, 
        embedding.tobytes()
    )
```

3. **Optimize Similarity Search**
```sql
-- Use approximate nearest neighbor search
SELECT id, content, 
       1 - (embedding <=> $1::vector) as similarity
FROM engrams
WHERE thread_id = $2
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

## Troubleshooting

### Common Issues

1. **"column is_deleted does not exist"**
   - Run the schema fix migration
   - Check you're using the correct database

2. **Token counting mismatch**
   - Ensure tiktoken is installed
   - Use the correct encoding for your model

3. **Slow retrieval**
   - Check if indexes exist
   - Enable Redis caching
   - Reduce retrieval limit

4. **Memory leak in embeddings**
   - Implement cache cleanup
   - Use bounded cache size
   - Monitor memory usage

### Debug Logging
```python
# Enable detailed logging
import logging
logging.getLogger('engram_manager').setLevel(logging.DEBUG)

# Add timing logs
import time
start = time.time()
# ... operation ...
logger.debug(f"Operation took {time.time() - start:.2f}s")
```

## Next Steps

1. **Set up monitoring** - Deploy Grafana dashboards
2. **Run benchmarks** - Measure compression ratios and retrieval accuracy
3. **A/B testing** - Compare with traditional summarization
4. **Document findings** - Prepare for academic publication

---

*For questions or issues, check the logs first, then the assessment document for design rationale.*