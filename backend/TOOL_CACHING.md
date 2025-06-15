# Tool Result Caching System

## Overview
The tool caching system reduces API costs and improves response times by caching the results of expensive tool operations. This is especially beneficial for web searches, API calls, and data scraping operations.

## Features
- **Automatic caching** with configurable TTL (Time To Live)
- **Smart cache conditions** to only cache successful results
- **Cache invalidation** support for clearing stale data
- **Metrics tracking** for monitoring cache performance
- **Redis-backed** for distributed caching across instances

## Usage

### Basic Caching
Add the `@cache_tool_result` decorator to any tool method:

```python
from agentpress.tool_cache import cache_tool_result

@cache_tool_result(ttl=300)  # Cache for 5 minutes
async def web_search(self, query: str) -> ToolResult:
    # Expensive operation
    return result
```

### Advanced Configuration
```python
@cache_tool_result(
    ttl=lambda result: 3600 if result.success else 60,  # Dynamic TTL
    cache_condition=lambda result: result.success,      # Only cache successes
    key_params=['query', 'num_results']                 # Specific params for key
)
async def search_with_options(self, query: str, num_results: int = 10) -> ToolResult:
    # Implementation
```

## Currently Cached Tools

### 1. Web Search (`web_search`)
- **TTL**: 5 minutes
- **Reason**: Search results are relatively stable short-term
- **Savings**: ~$0.01 per cached hit

### 2. Web Scraping (`scrape_webpage`)
- **TTL**: 30 minutes
- **Reason**: Webpage content changes less frequently
- **Savings**: ~$0.02-0.05 per cached hit

### 3. Data Providers (`execute_data_provider_call`)
- **TTL**: 1 hour for success, 1 minute for failures
- **Reason**: API data (LinkedIn, Twitter, etc.) is stable
- **Savings**: ~$0.03-0.10 per cached hit

## Monitoring

### API Endpoint
```bash
GET /api/cache/metrics
```

### Response Example
```json
{
    "status": "ok",
    "metrics": {
        "enabled": true,
        "hits": 1250,
        "misses": 3200,
        "errors": 2,
        "hit_rate": 28.09,
        "total_requests": 4450
    },
    "timestamp": "2024-06-14T10:30:00Z"
}
```

## Cache Invalidation

### Manual Invalidation
```python
from agentpress.tool_cache import get_tool_cache

cache = get_tool_cache()

# Invalidate specific cached result
await cache.invalidate("SandboxWebSearchTool", {"query": "AI news"})

# Invalidate all results for a tool
await cache.invalidate("SandboxWebSearchTool")
```

## Implementation Details

### Cache Key Generation
Cache keys are generated using SHA256 hashes of:
- Tool class name
- Method parameters (sorted for consistency)
- Format: `tool_cache:ToolName:hash`

### Storage
- Uses Redis with automatic expiration
- JSON serialization for complex data types
- Graceful fallback if Redis unavailable

### Performance Impact
- Cache hits: ~1-5ms overhead
- Cache misses: ~5-10ms overhead
- Network savings: 50-99% reduction in external API calls

## Best Practices

1. **Cache Appropriate Tools**: Focus on tools that:
   - Make expensive external API calls
   - Return relatively stable data
   - Are called frequently with same parameters

2. **Set Reasonable TTLs**:
   - Real-time data: 1-5 minutes
   - Semi-stable data: 15-30 minutes
   - Static data: 1-24 hours

3. **Monitor Hit Rates**:
   - Good: >30% hit rate
   - Excellent: >50% hit rate
   - Consider adjusting TTL if rate is too low

4. **Handle Cache Failures Gracefully**:
   - Tool should work even if cache is unavailable
   - Log cache errors but don't fail the operation

## Future Improvements
- [ ] Cache warming for popular queries
- [ ] Intelligent TTL based on content changes
- [ ] Cache size limits and eviction policies
- [ ] Per-user cache isolation for personalized results