"""
API Gateway Routing Module

This module defines all API routes and endpoints for the platform.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from .auth import get_current_user


# Request/Response Models
class TaskRequest(BaseModel):
    """Request model for task submission"""
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5
    metadata: Optional[Dict[str, Any]] = None


class TrainingRequest(BaseModel):
    """Request model for training operations"""
    model_type: str
    dataset_id: str
    config: Dict[str, Any]
    distributed: bool = True


class MemoryQuery(BaseModel):
    """Query model for memory operations"""
    query: str
    memory_type: str  # episodic, semantic, procedural
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


class DreamRequest(BaseModel):
    """Request model for dream engine operations"""
    themes: List[str]
    creativity_level: float = 0.7
    duration: int = 300  # seconds


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    repository_url: Optional[str] = None
    file_paths: Optional[List[str]] = None
    analysis_type: str = "comprehensive"


def setup_routes(app, gateway):
    """Setup all API routes"""
    
    # Protocol Layer Routes
    protocol_router = APIRouter(prefix="/api/v1/protocol", tags=["protocol"])
    
    @protocol_router.post("/tasks/submit")
    async def submit_task(request: TaskRequest, user=Depends(get_current_user)):
        """Submit a task to the protocol layer"""
        return await gateway.route_to_service("orchestrator", {
            "action": "submit_task",
            "data": request.dict()
        })
    
    @protocol_router.get("/tasks/{task_id}/status")
    async def get_task_status(task_id: str, user=Depends(get_current_user)):
        """Get task execution status"""
        return await gateway.route_to_service("orchestrator", {
            "action": "get_task_status",
            "task_id": task_id
        })
    
    @protocol_router.get("/workers/status")
    async def get_workers_status(user=Depends(get_current_user)):
        """Get status of all workers"""
        return await gateway.route_to_service("orchestrator", {
            "action": "get_workers_status"
        })
    
    # Intelligence Layer Routes
    intelligence_router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])
    
    @intelligence_router.post("/training/start")
    async def start_training(request: TrainingRequest, user=Depends(get_current_user)):
        """Start a training job"""
        return await gateway.route_to_service("ai_trainer", {
            "action": "start_training",
            "data": request.dict()
        })
    
    @intelligence_router.get("/training/{job_id}/status")
    async def get_training_status(job_id: str, user=Depends(get_current_user)):
        """Get training job status"""
        return await gateway.route_to_service("ai_trainer", {
            "action": "get_training_status",
            "job_id": job_id
        })
    
    @intelligence_router.post("/inference/predict")
    async def predict(data: Dict[str, Any], user=Depends(get_current_user)):
        """Run inference on data"""
        return await gateway.route_to_service("ai_inference", {
            "action": "predict",
            "data": data
        })
    
    # Conceptual Layer Routes
    conceptual_router = APIRouter(prefix="/api/v1/conceptual", tags=["conceptual"])
    
    @conceptual_router.post("/memory/store")
    async def store_memory(memory_data: Dict[str, Any], user=Depends(get_current_user)):
        """Store a memory in the appropriate system"""
        return await gateway.route_to_service("memory_system", {
            "action": "store_memory",
            "data": memory_data
        })
    
    @conceptual_router.post("/memory/query")
    async def query_memory(query: MemoryQuery, user=Depends(get_current_user)):
        """Query memories across systems"""
        return await gateway.route_to_service("memory_system", {
            "action": "query_memory",
            "data": query.dict()
        })
    
    @conceptual_router.post("/dream/start")
    async def start_dream(request: DreamRequest, user=Depends(get_current_user)):
        """Start a dream session"""
        return await gateway.route_to_service("dream_engine", {
            "action": "start_dream",
            "data": request.dict()
        })
    
    @conceptual_router.get("/dream/{session_id}/insights")
    async def get_dream_insights(session_id: str, user=Depends(get_current_user)):
        """Get insights from a dream session"""
        return await gateway.route_to_service("dream_engine", {
            "action": "get_insights",
            "session_id": session_id
        })
    
    # Development Layer Routes
    development_router = APIRouter(prefix="/api/v1/development", tags=["development"])
    
    @development_router.post("/analyze/code")
    async def analyze_code(request: CodeAnalysisRequest, user=Depends(get_current_user)):
        """Analyze code repository or files"""
        return await gateway.route_to_service("dev_tools", {
            "action": "analyze_code",
            "data": request.dict()
        })
    
    @development_router.post("/generate/plan")
    async def generate_plan(project_data: Dict[str, Any], user=Depends(get_current_user)):
        """Generate project plan from requirements"""
        return await gateway.route_to_service("dev_tools", {
            "action": "generate_plan",
            "data": project_data
        })
    
    @development_router.post("/generate/prd")
    async def generate_prd(requirements: Dict[str, Any], user=Depends(get_current_user)):
        """Generate PRD from requirements"""
        return await gateway.route_to_service("dev_tools", {
            "action": "generate_prd",
            "data": requirements
        })
    
    # Integration Layer Routes
    integration_router = APIRouter(prefix="/api/v1/integration", tags=["integration"])
    
    @integration_router.post("/events/publish")
    async def publish_event(event: Dict[str, Any], user=Depends(get_current_user)):
        """Publish an event to the event bus"""
        await gateway.broadcast_event(event)
        return {"status": "published", "timestamp": datetime.now()}
    
    @integration_router.get("/services/status")
    async def get_services_status(user=Depends(get_current_user)):
        """Get status of all registered services"""
        return gateway.service_registry.services
    
    # File Upload Routes
    upload_router = APIRouter(prefix="/api/v1/upload", tags=["upload"])
    
    @upload_router.post("/dataset")
    async def upload_dataset(file: UploadFile = File(...), user=Depends(get_current_user)):
        """Upload a dataset for training"""
        # TODO: Implement file upload handling
        return {"filename": file.filename, "status": "uploaded"}
    
    @upload_router.post("/model")
    async def upload_model(file: UploadFile = File(...), user=Depends(get_current_user)):
        """Upload a pre-trained model"""
        # TODO: Implement model upload handling
        return {"filename": file.filename, "status": "uploaded"}
    
    # Register all routers
    app.include_router(protocol_router)
    app.include_router(intelligence_router)
    app.include_router(conceptual_router)
    app.include_router(development_router)
    app.include_router(integration_router)
    app.include_router(upload_router)