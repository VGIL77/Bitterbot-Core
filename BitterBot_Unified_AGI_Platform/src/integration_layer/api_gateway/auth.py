"""
Authentication module for BitterBot AGI Platform API Gateway

This module handles authentication and authorization for API requests.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from pydantic import BaseModel


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_DELTA", "1440")) // 60


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token
security = HTTPBearer()


class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False
    permissions: List[str] = []


class TokenData(BaseModel):
    """Token payload data"""
    sub: str  # Subject (user ID)
    exp: datetime
    iat: datetime
    permissions: List[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], 
                       expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Token data
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        token_data = TokenData(
            sub=payload.get("sub"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            permissions=payload.get("permissions", [])
        )
        
        if token_data.sub is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing subject"
            )
            
        return token_data
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    try:
        token_data = decode_token(token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}"
        )
        
    # TODO: Fetch actual user from database
    # For now, return a mock user
    user = User(
        id=token_data.sub,
        username=f"user_{token_data.sub}",
        email=f"user_{token_data.sub}@example.com",
        permissions=token_data.permissions
    )
    
    return user


def require_permission(permission: str):
    """
    Dependency to require a specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_checker(user: User = Depends(get_current_user)):
        if permission not in user.permissions and not user.is_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required"
            )
        return user
    
    return permission_checker


def require_admin():
    """
    Dependency to require admin privileges.
    
    Returns:
        Dependency function
    """
    async def admin_checker(user: User = Depends(get_current_user)):
        if not user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        return user
    
    return admin_checker