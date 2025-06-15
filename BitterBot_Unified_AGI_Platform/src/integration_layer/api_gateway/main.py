"""
Unified API Gateway for BitterBot AGI Platform

This module provides the main API gateway that routes requests to
all platform services and manages cross-layer communication.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .routing import setup_routes
from .middleware import setup_middleware
from .auth import get_current_user
from ..event_system.event_bus import EventBus
from ..monitoring.metrics_collector import MetricsCollector


logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for platform services"""
    
    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        
    def register_service(self, name: str, config: Dict[str, Any]) -> None:
        """Register a service with the gateway"""
        self.services[name] = {
            "config": config,
            "status": "registered",
            "last_heartbeat": datetime.now()
        }
        
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service configuration"""
        return self.services.get(name)
        
    def update_service_status(self, name: str, status: str) -> None:
        """Update service status"""
        if name in self.services:
            self.services[name]["status"] = status
            self.services[name]["last_heartbeat"] = datetime.now()


class UnifiedAPIGateway:
    """
    Unified API Gateway providing access to all platform layers
    with intelligent routing and event broadcasting.
    """
    
    def __init__(self):
        self.app = self._create_app()
        self.service_registry = ServiceRegistry()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.websocket_connections: Dict[str, WebSocket] = {}
        
    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self._startup()
            yield
            # Shutdown
            await self._shutdown()
            
        app = FastAPI(
            title="BitterBot Unified AGI Platform",
            description="Unified API Gateway for AGI Platform Services",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Setup middleware
        setup_middleware(app)
        
        # Setup routes
        setup_routes(app, self)
        
        return app
        
    async def _startup(self) -> None:
        """Startup tasks"""
        logger.info("Starting Unified API Gateway...")
        
        # Initialize service connections
        await self._initialize_services()
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._metrics_collection_loop())
        
        logger.info("API Gateway started successfully")
        
    async def _shutdown(self) -> None:
        """Shutdown tasks"""
        logger.info("Shutting down API Gateway...")
        
        # Close websocket connections
        for ws in self.websocket_connections.values():
            await ws.close()
            
        # Cleanup
        await self.event_bus.close()
        
        logger.info("API Gateway shutdown complete")
        
    async def _initialize_services(self) -> None:
        """Initialize connections to platform services"""
        # Register core services
        self.service_registry.register_service("orchestrator", {
            "url": "http://orchestrator:9001",
            "type": "protocol_layer"
        })
        
        self.service_registry.register_service("ai_inference", {
            "url": "http://ai-inference:8001",
            "type": "intelligence_layer"
        })
        
        self.service_registry.register_service("dev_tools", {
            "url": "http://dev-tools:8002",
            "type": "development_layer"
        })
        
    async def _health_check_loop(self) -> None:
        """Periodic health check of services"""
        while True:
            try:
                for service_name in self.service_registry.services:
                    # TODO: Implement actual health checks
                    pass
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def _metrics_collection_loop(self) -> None:
        """Collect metrics periodically"""
        while True:
            try:
                await self.metrics_collector.collect_system_metrics()
                await asyncio.sleep(10)  # Collect every 10 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                
    async def route_to_service(self, 
                             service_name: str, 
                             request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route requests to appropriate services.
        
        Args:
            service_name: Target service name
            request_data: Request data
            
        Returns:
            Service response
        """
        service = self.service_registry.get_service(service_name)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
            
        # TODO: Implement actual service routing
        raise NotImplementedError("Service routing not yet implemented")
        
    async def broadcast_event(self, event: Dict[str, Any]) -> None:
        """
        Broadcast events across all platform layers.
        
        Args:
            event: Event to broadcast
        """
        await self.event_bus.publish("platform.events", event)
        
        # Send to WebSocket clients
        for client_id, ws in self.websocket_connections.items():
            try:
                await ws.send_json(event)
            except Exception as e:
                logger.error(f"Failed to send event to {client_id}: {e}")
                
    async def handle_websocket(self, websocket: WebSocket, client_id: str) -> None:
        """
        Handle WebSocket connections for real-time updates.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await websocket.accept()
        self.websocket_connections[client_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_json()
                # Process WebSocket messages
                await self._process_websocket_message(client_id, data)
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {client_id} disconnected")
        finally:
            del self.websocket_connections[client_id]
            
    async def _process_websocket_message(self, 
                                       client_id: str, 
                                       data: Dict[str, Any]) -> None:
        """Process incoming WebSocket messages"""
        # TODO: Implement message processing
        pass


# Create gateway instance
gateway = UnifiedAPIGateway()
app = gateway.app


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": gateway.service_registry.services
    }


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get platform metrics"""
    return await gateway.metrics_collector.get_metrics()


# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await gateway.handle_websocket(websocket, client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)