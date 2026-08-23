from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import os

from app.models.models import User
from app.core.database import get_db
from app.core.redis import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)

class TokenBlacklist:
    @staticmethod
    async def blacklist_token(token: str, expires_in: int):
        await redis_client.set(f"blacklist:{token}", "revoked", ttl=expires_in)
    
    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        return await redis_client.exists(f"blacklist:{token}") > 0

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_tokens(user_id: str, username: str) -> Dict[str, str]:
        access_token_data = {
            "sub": str(user_id),
            "username": username,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        refresh_token_data = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = credentials.credentials
    
    if await TokenBlacklist.is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import os

from app.models.models import User
from app.core.database import get_db
from app.core.redis import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)

class TokenBlacklist:
    @staticmethod
    async def blacklist_token(token: str, expires_in: int):
        await redis_client.set(f"blacklist:{token}", "revoked", ttl=expires_in)
    
    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        return await redis_client.exists(f"blacklist:{token}") > 0

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_tokens(user_id: str, username: str) -> Dict[str, str]:
        access_token_data = {
            "sub": str(user_id),
            "username": username,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        refresh_token_data = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = credentials.credentials
    
    if await TokenBlacklist.is_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")