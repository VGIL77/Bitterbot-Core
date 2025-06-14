"""
Authentication for BitterBot Admin Console.

Only creators/admins can access the admin console features.
"""

import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from aiohttp import web

from services.supabase import DBConnection
from utils.logger import logger

# JWT configuration
JWT_SECRET = "your-secret-key-change-this"  # Should be in env vars
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AdminAuth:
    """Handles authentication for admin console access."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def verify_admin_user(self, user_id: str) -> bool:
        """
        Check if a user has admin/creator privileges.
        
        We use the existing privileged tier system from billing.py
        """
        try:
            client = await self.db.client
            
            # Check user tier using the existing profiles table
            PRIVILEGED_TIERS = ['creator', 'tester', 'vip', 'investor']
            
            result = await client.from_('profiles').select('tier').eq(
                'account_id', user_id
            ).single().execute()
            
            if result.data and result.data.get('tier') in PRIVILEGED_TIERS:
                logger.info(f"User {user_id} has privileged tier: {result.data.get('tier')}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error verifying admin user: {e}")
            return False
            
    def generate_admin_token(self, user_id: str, email: str) -> str:
        """Generate a JWT token for admin access."""
        payload = {
            'user_id': user_id,
            'email': email,
            'role': 'admin',
            'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.now(timezone.utc)
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
    def verify_admin_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode an admin JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Admin token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid admin token: {e}")
            return None


# Middleware for protecting admin routes
def require_admin_auth(handler):
    """Decorator for routes that require admin authentication."""
    @wraps(handler)
    async def wrapper(request):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Missing or invalid authorization header'},
                status=401
            )
            
        token = auth_header.replace('Bearer ', '')
        
        # Verify token
        auth = AdminAuth()
        payload = auth.verify_admin_token(token)
        
        if not payload:
            return web.json_response(
                {'error': 'Invalid or expired token'},
                status=401
            )
            
        # Verify user still has admin privileges
        is_admin = await auth.verify_admin_user(payload['user_id'])
        if not is_admin:
            return web.json_response(
                {'error': 'Admin privileges required'},
                status=403
            )
            
        # Add user info to request
        request['admin_user'] = payload
        
        # Call the handler
        return await handler(request)
        
    return wrapper


async def admin_login_handler(request):
    """Handle admin login requests."""
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')  # In production, verify with Supabase Auth
        
        if not email:
            return web.json_response(
                {'error': 'Email required'},
                status=400
            )
            
        # In production, verify credentials with Supabase Auth
        # For now, we'll do a simple check
        client = await DBConnection().client
        
        # Get user by email
        result = await client.table('accounts').select(
            'account_id', 'email', 'metadata'
        ).eq('email', email).single().execute()
        
        if not result.data:
            return web.json_response(
                {'error': 'Invalid credentials'},
                status=401
            )
            
        account = result.data
        
        # Verify admin status
        auth = AdminAuth()
        is_admin = await auth.verify_admin_user(account['account_id'])
        
        if not is_admin:
            return web.json_response(
                {'error': 'Admin access required'},
                status=403
            )
            
        # Generate token
        token = auth.generate_admin_token(
            account['account_id'],
            account['email']
        )
        
        return web.json_response({
            'token': token,
            'user': {
                'id': account['account_id'],
                'email': account['email'],
                'role': 'admin'
            }
        })
        
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return web.json_response(
            {'error': 'Login failed'},
            status=500
        )