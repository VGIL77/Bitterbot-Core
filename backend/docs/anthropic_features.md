# Anthropic API Features Integration

This document describes the new Anthropic features integrated into BitterBot Core.

## New Features

### 1. Thinking Budget Tokens (New API)

The `thinking_budget_tokens` parameter allows you to control how many tokens Claude can use for its internal reasoning process.

**Usage:**
```python
response = await make_llm_api_call(
    messages,
    model_name="anthropic/claude-3-opus-latest",
    enable_thinking=True,
    thinking_budget_tokens=1000,  # Allocate 1000 tokens for thinking
)
```

**When to use:**
- For complex reasoning tasks
- When you want to limit computational overhead
- To balance between response quality and cost

### 2. Native Web Search (Beta)

The `enable_native_web_search` parameter enables Claude to search the web directly through Anthropic's native implementation.

**Usage:**
```python
response = await make_llm_api_call(
    messages,
    model_name="anthropic/claude-3-opus-latest",
    enable_native_web_search=True,
)
```

**When to use:**
- For real-time information queries
- When you need current events or recent data
- As an alternative to the Tavily web search tool

## API Changes

### Updated Function Signatures

1. **make_llm_api_call**
   - Added `thinking_budget_tokens: Optional[int] = None`
   - Added `enable_native_web_search: Optional[bool] = False`

2. **ThreadManager.run_thread**
   - Added `thinking_budget_tokens: Optional[int] = None`
   - Added `enable_native_web_search: Optional[bool] = False`

3. **run_agent**
   - Added `thinking_budget_tokens: Optional[int] = None`
   - Added `enable_native_web_search: Optional[bool] = False`

### API Request Body

The `AgentStartRequest` model now includes:
```python
thinking_budget_tokens: Optional[int] = None
enable_native_web_search: Optional[bool] = False
```

## Implementation Details

### Thinking API

The implementation supports both the legacy `reasoning_effort` API and the new `thinking_budget_tokens` API:

- If `thinking_budget_tokens` is provided, it uses the new thinking API with budget
- Otherwise, it falls back to the legacy `reasoning_effort` parameter
- Temperature is automatically set to 1.0 when thinking is enabled (Anthropic requirement)

### Web Search Beta

- Adds the "web-search-2025-03-05" beta feature to Anthropic headers
- Only enabled when `enable_native_web_search=True`
- Works alongside the existing Tavily web search tool

## Testing

Run the test script to verify the implementation:
```bash
python test_anthropic_features.py
```

This will test:
1. Thinking budget tokens alone
2. Native web search alone
3. Both features combined

## Notes

- These features are currently in beta and may change
- The native web search is only available for Anthropic models
- Thinking budget provides more granular control than reasoning_effort
- Both features can be used together for complex research tasks