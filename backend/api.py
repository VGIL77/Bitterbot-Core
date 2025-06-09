from fastapi import FastAPI, Request, HTTPException, Response, Depends, Header
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

# Define allowed origins based on environment
allowed_origins = [
    "https://www.suna.so",
    "https://suna.so",
    "https://bitterbot.net",
    "https://www.bitterbot.net",
    "http://localhost:3000"
]
allow_origin_regex = None

# Add staging-specific origins
if config.ENV_MODE == EnvMode.STAGING:
    allowed_origins.append("https://staging.suna.so")
    # Updated regex to include both suna and bitterbot Vercel preview URLs
    allow_origin_regex = r"https://(suna|bitterbot)-.*-.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

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

# Override the JWT authentication dependency to always return a test user
from agent.api import get_current_user_id_from_jwt

async def fake_get_current_user_id_from_jwt():
    """Bypass JWT auth - always return test user"""
    return "test-user-123"

# Override the dependency
app.dependency_overrides[get_current_user_id_from_jwt] = fake_get_current_user_id_from_jwt

# Add auth endpoints that the real agent/initiate might check
@app.get("/user")
async def get_user_bypass(authorization: str = Header(None)):
    """Bypass user endpoint - returns mock user"""
    return {
        "id": "test-user-123",
        "email": "test@bitterbot.net",
        "user_metadata": {"full_name": "Test User"}
    }

@app.get("/billing/subscription")
async def get_subscription_bypass():
    """Bypass subscription check - always active"""
    return {
        "status": "active",
        "type": "premium",
        "limits": None,
        "model_access": ["all"]
    }

@app.get("/billing/check-status") 
async def check_billing_bypass():
    """Bypass billing check - always active"""
    return {
        "status": "active",
        "can_use_features": True,
        "message": "Billing bypassed"
    }

# Simple bypass - catch ONLY truly missing endpoints (must be LAST)
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def catch_all(path: str, request: Request):
    """Catch-all route for missing endpoints only"""
    logger.warning(f"Catch-all route hit (unhandled endpoint): {request.method} /{path}")
    
    # Log the full request details to help debug
    try:
        body = await request.body()
        logger.info(f"Request body: {body[:200]}...")  # First 200 chars
    except:
        pass
    
    # Return minimal response for unhandled endpoints
    if request.method == "GET":
        return {"status": "ok", "message": f"Unhandled GET /{path}"}
    else:
        return {"success": True, "message": f"Unhandled {request.method} /{path}"}

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