"""
BitterBot MVP Backend - Main FastAPI Application
"""
import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Claude service
from app.services.claude import ClaudeService

# Models
class ChatMessage(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class Task(BaseModel):
    id: str
    title: str
    description: str
    status: str  # "pending", "in_progress", "completed"
    progress: float  # 0.0 to 1.0
    subtasks: list["Task"] = []
    metadata: Dict[str, Any] = {}

class TaskUpdate(BaseModel):
    task_id: str
    status: str = None
    progress: float = None
    metadata: Dict[str, Any] = None

# Initialize FastAPI app
app = FastAPI(title="BitterBot MVP API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize Claude service
claude_service = ClaudeService()

# In-memory storage for MVP
conversations: Dict[str, list[ChatMessage]] = {}
tasks: Dict[str, Task] = {}
active_connections: list[WebSocket] = []

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BitterBot MVP"}

# Chat endpoints
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Process a chat message and return response"""
    # Create conversation if new
    if not request.conversation_id:
        request.conversation_id = str(uuid.uuid4())
    
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = []
    
    # Store user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    conversations[request.conversation_id].append(user_msg)
    
    # Create initial task breakdown (mock for MVP)
    main_task = Task(
        id=str(uuid.uuid4()),
        title="Process User Request",
        description=f"Handling: {request.message[:50]}...",
        status="in_progress",
        progress=0.0,
        subtasks=[
            Task(
                id=str(uuid.uuid4()),
                title="Analyze Request",
                description="Understanding user intent",
                status="pending",
                progress=0.0
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Gather Information",
                description="Accessing relevant tools and data",
                status="pending",
                progress=0.0
            ),
            Task(
                id=str(uuid.uuid4()),
                title="Generate Response",
                description="Crafting comprehensive answer",
                status="pending",
                progress=0.0
            )
        ]
    )
    
    # Store task
    tasks[main_task.id] = main_task
    
    # Broadcast task update
    await manager.broadcast({
        "type": "task_update",
        "task": main_task.dict()
    })
    
    # Get conversation history to provide context
    conversation_history = [
        {"role": msg.role, "content": msg.content} 
        for msg in conversations[request.conversation_id][-10:]
    ]
    
    # Process the message using Claude API
    try:
        response = await claude_service.process_message(request.message, conversation_history)
        
        # Create assistant message from Claude response
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=response.get("content", ""),
            timestamp=datetime.utcnow(),
            metadata={
                "task_id": main_task.id,
                "tools_used": response.get("tools_used", [])
            }
        )
        conversations[request.conversation_id].append(assistant_msg)
    except Exception as e:
        # Log the error and return a fallback response
        print(f"Error processing message with Claude API: {str(e)}")
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            timestamp=datetime.utcnow(),
            metadata={"task_id": main_task.id, "error": True}
        )
        conversations[request.conversation_id].append(assistant_msg)
    
    # Update task progress
    asyncio.create_task(simulate_task_progress(main_task.id))
    
    return {
        "conversation_id": request.conversation_id,
        "message": assistant_msg.dict(),
        "task_id": main_task.id
    }

# Get conversation history
@app.get("/api/chat/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": [msg.dict() for msg in conversations[conversation_id]]
    }

# Task endpoints
@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id].dict()

@app.post("/api/tasks/update")
async def update_task(update: TaskUpdate):
    if update.task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[update.task_id]
    
    if update.status:
        task.status = update.status
    if update.progress is not None:
        task.progress = update.progress
    if update.metadata:
        task.metadata.update(update.metadata)
    
    # Broadcast update
    await manager.broadcast({
        "type": "task_update",
        "task": task.dict()
    })
    
    return task.dict()

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper functions
async def simulate_task_progress(task_id: str):
    """Simulate task progress for MVP"""
    if task_id not in tasks:
        return
    
    task = tasks[task_id]
    
    # Update subtasks
    for i, subtask in enumerate(task.subtasks):
        await asyncio.sleep(2)  # Simulate processing time
        
        subtask.status = "in_progress"
        await manager.broadcast({
            "type": "task_update",
            "task": task.dict()
        })
        
        await asyncio.sleep(1)
        
        subtask.status = "completed"
        subtask.progress = 1.0
        task.progress = (i + 1) / len(task.subtasks)
        
        await manager.broadcast({
            "type": "task_update",
            "task": task.dict()
        })
    
    task.status = "completed"
    task.progress = 1.0
    
    await manager.broadcast({
        "type": "task_update",
        "task": task.dict()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
