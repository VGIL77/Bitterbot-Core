# API Endpoint Mismatch Analysis

## Frontend API Calls vs Backend Routes

### 1. **CRITICAL MISMATCH: API Prefix**
The frontend is making calls to endpoints without the `/api` prefix, but the backend expects all routes to have `/api` prefix.

**Frontend calls (api.ts and api-enhanced.ts):**
- `${API_URL}/thread/${threadId}/agent/start`
- `${API_URL}/agent-run/${agentRunId}/stop`
- `${API_URL}/agent-run/${agentRunId}`
- `${API_URL}/thread/${threadId}/agent-runs`
- `${API_URL}/agent-run/${agentRunId}/stream`
- `${API_URL}/agent/initiate`
- `${API_URL}/project/${projectId}/sandbox/ensure-active`
- `${API_URL}/sandboxes/${sandboxId}/files`
- `${API_URL}/sandboxes/${sandboxId}/files/content`
- `${API_URL}/sandboxes/${sandboxId}/files/json`
- `${API_URL}/api/health` ✓ (correctly includes /api)
- `${API_URL}/api/billing/create-checkout-session` ✓ (correctly includes /api)
- `${API_URL}/api/billing/create-portal-session` ✓ (correctly includes /api)
- `${API_URL}/api/billing/subscription` ✓ (correctly includes /api)
- `${API_URL}/api/billing/available-models` ✓ (correctly includes /api)
- `${API_URL}/api/billing/check-status` ✓ (correctly includes /api)
- `${API_URL}/transcription`
- `${API_URL}/agents/${agentId}/builder-chat-history`

**Backend routes (all routers are mounted with /api prefix in api.py):**
```python
app.include_router(agent_api.router, prefix="/api")
app.include_router(sandbox_api.router, prefix="/api")
app.include_router(billing_api.router, prefix="/api")
app.include_router(mcp_api.router, prefix="/api")
app.include_router(transcription_api.router, prefix="/api")
```

### 2. **Missing /api Prefix Summary**

These frontend calls are MISSING the `/api` prefix:
1. All agent-related endpoints
2. All sandbox-related endpoints
3. Transcription endpoint
4. Agents builder chat history

### 3. **Endpoint Mapping Issues**

#### Agent Endpoints
- Frontend: `/thread/{threadId}/agent/start` → Should be: `/api/thread/{threadId}/agent/start`
- Frontend: `/agent-run/{agentRunId}/stop` → Should be: `/api/agent-run/{agentRunId}/stop`
- Frontend: `/agent-run/{agentRunId}` → Should be: `/api/agent-run/{agentRunId}`
- Frontend: `/thread/{threadId}/agent-runs` → Should be: `/api/thread/{threadId}/agent-runs`
- Frontend: `/agent-run/{agentRunId}/stream` → Should be: `/api/agent-run/{agentRunId}/stream`
- Frontend: `/agent/initiate` → Should be: `/api/agent/initiate`
- Frontend: `/agents/${agentId}/builder-chat-history` → Should be: `/api/agents/${agentId}/builder-chat-history`

#### Sandbox Endpoints
- Frontend: `/project/{projectId}/sandbox/ensure-active` → Should be: `/api/project/{projectId}/sandbox/ensure-active`
- Frontend: `/sandboxes/{sandboxId}/files` → Should be: `/api/sandboxes/{sandboxId}/files`
- Frontend: `/sandboxes/{sandboxId}/files/content` → Should be: `/api/sandboxes/{sandboxId}/files/content`
- Frontend: `/sandboxes/{sandboxId}/files/json` → Should be: `/api/sandboxes/{sandboxId}/files/json`

#### Transcription Endpoint
- Frontend: `/transcription` → Should be: `/api/transcription`

### 4. **api-enhanced.ts Issues**

The `api-enhanced.ts` file uses a different pattern but still has issues:
- It correctly prefixes some paths like `/billing/subscription` which becomes `/api/billing/subscription`
- But paths like `/thread/${threadId}/agent/start` are missing the `/api` prefix
- The `backendApi` client in `api-client.ts` should be adding the `/api` prefix automatically, but it seems this is not happening consistently

### 5. **Specific Issues Found**

1. **Agent API calls**: The frontend is calling agent endpoints without `/api` prefix
2. **Sandbox API calls**: The frontend is calling sandbox endpoints without `/api` prefix
3. **Transcription API**: Missing `/api` prefix
4. **Inconsistent pattern**: Some endpoints (billing, health) correctly include `/api`, while others don't

### 6. **Additional Observations**

- The billing endpoints are correctly using `/api/billing/...` in the frontend
- The health check endpoint correctly uses `/api/health`
- The MCP discover custom tools uses `/api/mcp/discover-custom-tools` correctly
- But agent, sandbox, and transcription endpoints are missing the `/api` prefix

### Recommendation

The frontend needs to be updated to consistently include the `/api` prefix for ALL backend API calls. This can be done either by:
1. Updating all the endpoint URLs in `api.ts` to include `/api/`
2. Or ensuring the `API_URL` environment variable or the base URL configuration properly includes the `/api` prefix
3. Or updating the `backendApi` client configuration to automatically prepend `/api` to all routes