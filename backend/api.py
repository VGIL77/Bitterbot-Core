from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import sentry
from contextlib import asynccontextmanager
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.config import config, EnvMode
import asyncio
from utils.logger import logger
import time
from collections import OrderedDict
from typing import Dict, Any
from litellm import completion
import os

from pydantic import BaseModel
# Import the agent API module
from agent import api as agent_api
from sandbox import api as sandbox_api
from services import billing as billing_api
from services import transcription as transcription_api
from services.mcp_custom import discover_custom_tools
import sys

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize managers
db = DBConnection()
instance_id = "single"

# Claude is initialized via LiteLLM - no need for direct Anthropic client

# Rate limiter state
ip_tracker = OrderedDict()
MAX_CONCURRENT_IPS = 25

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up FastAPI application with instance ID: {instance_id} in {config.ENV_MODE.value} mode")
    try:
        await db.initialize()
        
        agent_api.initialize(
            db,
            instance_id
        )
        
        sandbox_api.initialize(db)
        
        # Initialize Redis connection
        from services import redis
        try:
            await redis.initialize_async()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            # Continue without Redis - the application will handle Redis failures gracefully
        
        # Start background tasks
        # asyncio.create_task(agent_api.restore_running_agent_runs())
        
        yield
        
        # Clean up agent resources
        logger.info("Cleaning up agent resources")
        await agent_api.cleanup()
        
        # Clean up Redis connection
        try:
            logger.info("Closing Redis connection")
            await redis.close()
            logger.info("Redis connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        
        # Clean up database connection
        logger.info("Disconnecting from database")
        await db.disconnect()
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise

app = FastAPI(lifespan=lifespan)

# Define allowed origins based on environment
allowed_origins = [
    "https://www.suna.so",
    "https://suna.so",
    "https://bitterbot.net",
    "https://www.bitterbot.net",
    "http://localhost:3000",
    "http://localhost:3001"  # Added for good measure
]
allow_origin_regex = None

# Add staging-specific origins
if config.ENV_MODE == EnvMode.STAGING:
    allowed_origins.append("https://staging.suna.so")
    # Updated regex to include both suna and bitterbot Vercel preview URLs
    allow_origin_regex = r"https://(suna|bitterbot)-.*-.*\.vercel\.app"

# CORS MUST BE FIRST!
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],  # Allow ALL methods
    allow_headers=["*"],  # Allow ALL headers
)

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    path = request.url.path
    query_params = str(request.query_params)
    
    # Log the incoming request
    logger.info(f"Request started: {method} {path} from {client_ip} | Query: {query_params}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Request completed: {method} {path} | Status: {response.status_code} | Time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {path} | Error: {str(e)} | Time: {process_time:.2f}s")
        raise

# CORS configuration already added above (right after app initialization)

# Add OPTIONS handler for preflight requests
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    })

# Define our custom endpoints BEFORE including routers
@app.post("/agent/initiate")
async def initiate_agent(request: Request):
    data = await request.json()
    prompt = data.get('prompt', 'Hello')
    
    try:
        # 🔥 CLAUDE OPUS 4 VIA LITELLM 🔥
        response = completion(
            model="claude-opus-4-20250514",  # THE NEWEST MODEL!
            messages=[{
                "role": "user", 
                "content": prompt
            }],
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096,  # DOUBLE THE TOKENS!
            temperature=0.8,   # More creative
            # LiteLLM passes these through to Anthropic:
            top_p=0.95,
            metadata={
                "user": "trust_fund_victor",
                "mode": "MAXIMUM_PURPLE"
            }
        )
        
        return {
            "agent_id": "bitter-bot-opus-4",
            "thread_id": f"thread-{int(time.time())}",
            "response": response.choices[0].message.content,
            "model": "claude-opus-4-20250514",
            "tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else "UNLIMITED",
            "cost": f"${(response.usage.total_tokens * 0.00015):.2f}" if hasattr(response.usage, 'total_tokens') else "$$",
            "powered_by": "LiteLLM + Trust Fund Particles™"
        }
    except Exception as e:
        return {
            "agent_id": "error",
            "thread_id": "error", 
            "response": f"Error calling Claude Opus 4: {str(e)}",
            "suggestion": "Check if ANTHROPIC_API_KEY is set and has Opus 4 access"
        }

app.include_router(agent_api.router, prefix="/api")

app.include_router(sandbox_api.router, prefix="/api")

app.include_router(billing_api.router, prefix="/api")

from mcp_local import api as mcp_api

app.include_router(mcp_api.router, prefix="/api")

app.include_router(transcription_api.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify API is working."""
    logger.info("Health check endpoint called")
    return {
        "status": "ok", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": instance_id
    }

class CustomMCPDiscoverRequest(BaseModel):
    type: str
    config: Dict[str, Any]


@app.post("/api/mcp/discover-custom-tools")
async def discover_custom_mcp_tools(request: CustomMCPDiscoverRequest):
    try:
        return await discover_custom_tools(request.type, request.config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering custom MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

<<<<<<< HEAD
# Simple bypass - catch common endpoints that might be called
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def catch_all(path: str, request: Request):
    """Catch-all route for bypassing authentication/billing checks"""
    logger.info(f"Catch-all route hit: {request.method} /{path}")
    
    # Return sensible defaults for common endpoints
    if path == "user":
        return {"id": "bypass-user", "email": "user@bitterbot.net"}
    elif path.startswith("billing") or path.startswith("subscription"):
        return {"status": "active", "unlimited": True}
    elif path == "agents":
        return {"agents": []}
    elif path == "projects":
        return []
    elif path == "threads":
        return []
    elif request.method == "POST":
        # For any POST request, just return success
        return {"success": True, "id": f"bypass-{path}"}
    else:
        # For anything else, return empty success
        return {"status": "ok"}
=======
@app.get("/billing/subscription")
async def get_subscription():
    return {
        "status": "active",
        "type": "TRUST_FUND_UNLIMITED",
        "limits": None,
        "model_access": ["claude-opus-4", "claude-sonnet-4", "all-the-models"],
        "features": {
            "unlimited_messages": True,
            "priority_access": True,
            "purple_mode": "MAXIMUM"
        }
    }

@app.get("/billing/available-models")
async def get_models():
    return {"models": ["claude-3-opus", "gpt-4"]}

@app.get("/agents/{agent_id}/builder-chat-history")
async def get_builder_history(agent_id: str):
    return {"history": []}

@app.get("/agents")
async def get_agents():
    return {"agents": []}

@app.get("/thread/{thread_id}/agent-runs")
async def get_agent_runs(thread_id: str):
    return {"runs": []}

@app.get("/billing/check-status")
async def check_billing():
    return {"status": "active", "can_use_features": True}

@app.post("/project/{project_id}/sandbox/ensure-active")
async def ensure_sandbox(project_id: str):
    return {"active": True}

@app.get("/api/agents")
async def get_agents_api():
    return {"agents": []}

@app.post("/api/initiate-agent")
async def initiate_agent_api():
    return {"agent_id": "bitter-bot-1", "status": "ready"}

@app.get("/user")
async def get_user():
    return {"id": "mock-user", "email": "bitter@bot.com"}

@app.get("/projects")
async def get_projects():
    return []  # Empty projects for now

@app.get("/threads")
async def get_threads():
    return []  # Empty threads
>>>>>>> ccedfdd4f1079fda2f1a372ee552120d25ee4a54

if __name__ == "__main__":
    import uvicorn
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    workers = 1
    
    logger.info(f"Starting server on 0.0.0.0:8000 with {workers} workers")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000,
        workers=workers,
        loop="asyncio"
    )