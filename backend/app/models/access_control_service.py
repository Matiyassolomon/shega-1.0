"""
Access control service for song playback permissions
"""
from typing import Optional, Dict, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.song_access import SongAccess, SongPricing
from app.models.user import User
from app.core.cache import cache_manager


class AccessControlService:
    """Manages song access permissions with caching"""
    
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    def __init__(self, db: Session):
        self.db = db
    
    async def check_playback_access(
        self,
        user_id: str,
        song_id: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check if user can play song
        Returns: (can_play, error_code, details)
        """
        cache_key = f"access:{user_id}:{song_id}"
        
        # 1. Check cache
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached["can_play"], cached.get("error"), cached.get("details")
        
        # 2. Get song pricing
        pricing = self.db.query(SongPricing).filter(
            SongPricing.song_id == song_id
        ).first()
        
        if not pricing:
            # Default: treat as free if no pricing set
            result = (True, None, {"access_type": "free"})
            await self._cache_result(cache_key, result)
            return result
        
        # 3. Check if free
        if pricing.is_free:
            result = (True, None, {"access_type": "free", "pricing": pricing})
            await self._cache_result(cache_key, result)
            return result
        
        # 4. Check user subscription for premium content
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "USER_NOT_FOUND", None
        
        if pricing.requires_premium:
            # Check if user has active premium
            if await self._has_active_premium(user):
                result = (True, None, {
                    "access_type": "subscription",
                    "tier": user.subscription_tier if hasattr(user, "subscription_tier") else "premium"
                })
                await self._cache_result(cache_key, result)
                return result
        
        # 5. Check individual purchase
        access = self.db.query(SongAccess).filter(
            SongAccess.user_id == user_id,
            SongAccess.song_id == song_id,
            SongAccess.is_active == True
        ).filter(
            (SongAccess.valid_until == None) | 
            (SongAccess.valid_until > datetime.utcnow())
        ).first()
        
        if access:
            # Update play stats
            access.play_count += 1
            access.last_played_at = datetime.utcnow()
            self.db.commit()
            
            result = (True, None, {
                "access_type": access.access_type,
                "purchase_id": access.purchase_id,
                "access_id": access.id
            })
            await self._cache_result(cache_key, result)
            return result
        
        # 6. No access - PAYMENT_REQUIRED
        price = pricing.promo_price if pricing.promo_price and pricing.promo_ends_at > datetime.utcnow() else pricing.individual_price
        price = price or 0.99
        
        result = (False, "PAYMENT_REQUIRED", {
            "song_id": song_id,
            "price": price,
            "currency": "USD",
            "requires_premium": pricing.requires_premium,
            "preview_available": True
        })
        await cache_manager.set(cache_key, {
            "can_play": False,
            "error": "PAYMENT_REQUIRED",
            "details": result[2]
        }, ttl=30)
        
        return result
    
    async def grant_access_after_payment(
        self,
        user_id: str,
        song_id: str,
        payment_id: str,
        access_type: str = "purchase",
        price: float = None
    ) -> SongAccess:
        """Grant access after successful payment"""
        access = SongAccess(
            user_id=user_id,
            song_id=song_id,
            access_type=access_type,
            purchase_id=payment_id,
            purchase_price=price,
            is_active=True,
            valid_until=None
        )
        
        self.db.add(access)
        self.db.commit()
        self.db.refresh(access)
        
        # Invalidate cache
        cache_key = f"access:{user_id}:{song_id}"
        await cache_manager.delete(cache_key)
        
        return access
    
    async def _has_active_premium(self, user: User) -> bool:
        """Check if user has active premium subscription"""
        # Implement based on your subscription model
        if hasattr(user, "subscription_tier"):
            return user.subscription_tier in ["premium", "premium_plus", "family"]
        return False
    
    async def _cache_result(self, cache_key: str, result: Tuple) -> None:
        """Cache access check result"""
        await cache_manager.set(cache_key, {
            "can_play": result[0],
            "error": result[1],
            "details": result[2]
        }, ttl=self.CACHE_TTL_SECONDS)
    
    async def revoke_access(self, user_id: str, song_id: str) -> bool:
        """Revoke access (refund, subscription expired, etc.)"""
        access = self.db.query(SongAccess).filter(
            SongAccess.user_id == user_id,
            SongAccess.song_id == song_id
        ).first()
        
        if access:
            access.is_active = False
            self.db.commit()
            
            cache_key = f"access:{user_id}:{song_id}"
            await cache_manager.delete(cache_key)
            return True
        
        return False
