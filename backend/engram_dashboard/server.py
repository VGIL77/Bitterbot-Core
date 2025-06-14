#!/usr/bin/env python3
"""
ENGRAM Neural Observatory - WebSocket Server
Provides real-time metrics streaming for the visualization dashboard.

Authors: VMG & Claude (2025)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Dict, List, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from aiohttp import web
import aiohttp_cors
from aiohttp import web_ws
import socketio

from agentpress.engram_manager import get_engram_manager
from agentpress.engram_metrics import ExperienceMetrics
from services.supabase import DBConnection
from utils.logger import logger

# Import admin authentication
sys.path.append(str(Path(__file__).parent.parent))
try:
    from admin_console.auth import require_admin_auth, admin_login_handler
    AUTH_ENABLED = True
except ImportError:
    logger.warning("Admin auth not available, running without authentication")
    AUTH_ENABLED = False
    # Dummy decorator if auth not available
    def require_admin_auth(handler):
        return handler


class EngramObservatoryServer:
    """WebSocket server for real-time engram metrics."""
    
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode='aiohttp',
            cors_allowed_origins='*'
        )
        self.app = web.Application()
        self.sio.attach(self.app)
        
        # Metrics collectors
        self.engram_manager = get_engram_manager()
        self.experience_metrics = ExperienceMetrics()
        self.db = DBConnection()
        
        # Active connections
        self.active_threads = set()
        self.metrics_cache = {}
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio()
        
        # Configure CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Apply CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def setup_routes(self):
        """Setup HTTP routes."""
        # Serve dashboard files
        self.app.router.add_static(
            '/engram_dashboard', 
            Path(__file__).parent,
            name='dashboard'
        )
        
        # API endpoints (protected with auth)
        self.app.router.add_get('/api/engrams/metrics', require_admin_auth(self.get_metrics))
        self.app.router.add_get('/api/engrams/threads', require_admin_auth(self.get_threads))
        self.app.router.add_get('/api/engrams/{thread_id}/history', require_admin_auth(self.get_thread_history))
        self.app.router.add_post('/api/events', self.handle_event)  # No auth for internal events
        
        # Auth endpoints
        if AUTH_ENABLED:
            self.app.router.add_post('/api/admin/login', admin_login_handler)
        
        # Health check
        self.app.router.add_get('/health', self.health_check)
    
    def setup_socketio(self):
        """Setup Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            await self.sio.emit('connected', {'status': 'ok'}, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
        
        @self.sio.event
        async def thread_subscribe(sid, data):
            thread_id = data.get('threadId', 'system-wide')
            await self.sio.enter_room(sid, f"thread:{thread_id}")
            self.active_threads.add(thread_id)
            logger.info(f"Client {sid} subscribed to thread: {thread_id}")
            
            # Send initial data
            await self.send_thread_snapshot(sid, thread_id)
        
        @self.sio.event
        async def thread_unsubscribe(sid, data):
            thread_id = data.get('threadId', 'system-wide')
            await self.sio.leave_room(sid, f"thread:{thread_id}")
            logger.info(f"Client {sid} unsubscribed from thread: {thread_id}")
    
    async def get_metrics(self, request):
        """Get current metrics snapshot."""
        thread_id = request.query.get('thread_id', 'system-wide')
        
        try:
            if thread_id == 'system-wide':
                metrics = await self.experience_metrics.get_system_wide_metrics()
            else:
                metrics = await self.experience_metrics.log_metrics_snapshot(thread_id)
            
            return web.json_response(metrics)
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_threads(self, request):
        """Get list of threads with engrams."""
        try:
            client = await self.db.client
            result = await client.table('engrams').select('thread_id').execute()
            
            thread_ids = list(set(row['thread_id'] for row in result.data))
            
            return web.json_response({
                'threads': thread_ids,
                'count': len(thread_ids)
            })
        except Exception as e:
            logger.error(f"Error getting threads: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_thread_history(self, request):
        """Get engram history for a specific thread."""
        thread_id = request.match_info['thread_id']
        limit = int(request.query.get('limit', 100))
        
        try:
            client = await self.db.client
            result = await client.table('engrams')\
                .select('*')\
                .eq('thread_id', thread_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            # Process for visualization
            engrams = []
            for engram in result.data:
                engrams.append({
                    'id': engram['id'],
                    'relevance_score': engram['relevance_score'],
                    'surprise_score': engram['surprise_score'],
                    'created_at': engram['created_at'],
                    'token_count': engram['token_count'],
                    'access_count': engram['access_count'],
                    'content_preview': engram['content'][:200] + '...' if len(engram['content']) > 200 else engram['content']
                })
            
            return web.json_response({
                'thread_id': thread_id,
                'engrams': engrams,
                'count': len(engrams)
            })
        except Exception as e:
            logger.error(f"Error getting thread history: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def health_check(self, request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'active_threads': len(self.active_threads)
        })
    
    async def handle_event(self, request):
        """Handle incoming events from the main backend."""
        try:
            data = await request.json()
            event_type = data.get('type')
            event_data = data.get('data', {})
            
            # Emit to appropriate rooms
            if event_type == 'engram:created':
                thread_id = event_data.get('thread_id')
                await self.sio.emit('engram:created', event_data, room=f"thread:{thread_id}")
                await self.sio.emit('engram:created', event_data, room="thread:system-wide")
                
            elif event_type == 'engram:accessed':
                # Emit to all connected clients (for Hebbian visualization)
                await self.sio.emit('engram:accessed', event_data)
                
            elif event_type == 'metrics:update':
                thread_id = event_data.get('thread_id')
                await self.sio.emit('metrics:update', event_data, room=f"thread:{thread_id}")
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def send_thread_snapshot(self, sid, thread_id):
        """Send initial snapshot of thread data."""
        try:
            # Get recent engrams
            client = await self.db.client
            result = await client.table('engrams')\
                .select('*')\
                .eq('thread_id', thread_id)\
                .order('created_at', desc=True)\
                .limit(20)\
                .execute()
            
            # Get metrics
            metrics = await self.experience_metrics.log_metrics_snapshot(thread_id)
            
            # Send to client
            await self.sio.emit('thread:snapshot', {
                'thread_id': thread_id,
                'engrams': result.data,
                'metrics': metrics
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Error sending snapshot: {e}")
    
    async def start_metrics_broadcaster(self):
        """Broadcast metrics updates periodically."""
        while True:
            try:
                # Broadcast to each active thread room
                for thread_id in self.active_threads:
                    metrics = await self.experience_metrics.log_metrics_snapshot(thread_id)
                    
                    # Calculate additional real-time metrics
                    metrics['consolidation_rate'] = await self.calculate_consolidation_rate(thread_id)
                    metrics['retrieval_precision'] = await self.calculate_retrieval_precision(thread_id)
                    metrics['context_continuity'] = await self.calculate_context_continuity(thread_id)
                    
                    await self.sio.emit('metrics:update', metrics, room=f"thread:{thread_id}")
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics broadcaster: {e}")
                await asyncio.sleep(10)
    
    async def calculate_consolidation_rate(self, thread_id):
        """Calculate engrams created per minute."""
        try:
            client = await self.db.client
            # Count engrams created in last hour
            one_hour_ago = datetime.now(timezone.utc).isoformat()
            
            result = await client.rpc('count_recent_engrams', {
                'thread_id_param': thread_id,
                'since_time': one_hour_ago
            }).execute()
            
            count = result.data[0]['count'] if result.data else 0
            return count / 60.0  # Per minute
            
        except:
            return 0.0
    
    async def calculate_retrieval_precision(self, thread_id):
        """Calculate retrieval accuracy metric."""
        # In a real implementation, this would track actual retrieval success
        # For now, return a simulated value based on engram quality
        try:
            metrics = self.metrics_cache.get(thread_id, {})
            avg_relevance = metrics.get('basic_stats', {}).get('avg_relevance_score', 0.5)
            diversity = metrics.get('memory_health', {}).get('diversity_index', 0.5)
            
            # Precision is higher with better relevance and diversity
            return (avg_relevance * 0.6 + diversity * 0.4)
        except:
            return 0.5
    
    async def calculate_context_continuity(self, thread_id):
        """Calculate how well context is maintained."""
        try:
            metrics = self.metrics_cache.get(thread_id, {})
            temporal_coherence = metrics.get('memory_health', {}).get('temporal_distribution', 0.5)
            retrieval_balance = metrics.get('experience', {}).get('retrieval_balance', 0.5)
            
            # Continuity depends on temporal coherence and balanced retrieval
            return (temporal_coherence * 0.7 + retrieval_balance * 0.3)
        except:
            return 0.5
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the server."""
        logger.info(f"Starting ENGRAM Neural Observatory server on {host}:{port}")
        logger.info(f"Dashboard available at: http://localhost:{port}/engram_dashboard/")
        
        # Start background tasks
        async def start_background_tasks(app):
            app['metrics_broadcaster'] = asyncio.create_task(self.start_metrics_broadcaster())
        
        async def cleanup_background_tasks(app):
            app['metrics_broadcaster'].cancel()
            await app['metrics_broadcaster']
        
        self.app.on_startup.append(start_background_tasks)
        self.app.on_cleanup.append(cleanup_background_tasks)
        
        # Run server
        web.run_app(self.app, host=host, port=port)


def main():
    """Main entry point."""
    server = EngramObservatoryServer()
    
    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description='ENGRAM Neural Observatory Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    args = parser.parse_args()
    
    # Run server
    server.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()