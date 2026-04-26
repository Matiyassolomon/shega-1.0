"""
Access Control Service
Manages song playback permissions based on pricing, purchases, and subscriptions
"""
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User, Subscription
from app.models.commerce import SongPurchase, SongMarketplace
from app.models.song import PremiumContent


class AccessControlService:
    """Check if user can play a song"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def check_playback_access(
        self,
        user_id: str,
        song_id: str
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Check if user can play a song.
        
        Access hierarchy:
        1. Free songs (no price set)
        2. User purchased the song
        3. User has active subscription (premium/premium_plus)
        4. PAYMENT_REQUIRED (preview only)
        
        Returns:
            (can_play, error_code, access_details)
        """
        user_id_int = int(user_id)
        
        # 1. Check if user purchased this specific song
        purchase = self.db.query(SongPurchase).filter(
            SongPurchase.buyer_id == user_id_int,
            SongPurchase.song_id == song_id
        ).first()
        
        if purchase:
            return True, None, {
                "access_type": "purchase",
                "is_owned": True,
                "purchase_id": purchase.id,
                "purchased_at": purchase.purchased_at.isoformat() if hasattr(purchase, 'purchased_at') else None
            }
        
        # 2. Check if user has active premium subscription
        user = self.db.query(User).filter_by(id=user_id_int).first()
        if user:
            active_sub = self.db.query(Subscription).filter(
                Subscription.user_id == user_id_int,
                Subscription.status == "active",
                Subscription.expires_at > datetime.utcnow()
            ).first()
            
            if active_sub:
                return True, None, {
                    "access_type": "subscription",
                    "subscription_tier": user.subscription_tier,
                    "expires_at": active_sub.expires_at.isoformat() if active_sub.expires_at else None
                }
        
        # 3. Check if song is free (no pricing set or explicitly free)
        marketplace_song = self.db.query(SongMarketplace).filter_by(song_id=song_id).first()
        if marketplace_song:
            # Check if explicitly free
            if getattr(marketplace_song, 'is_free', False) or marketplace_song.price == 0:
                return True, None, {
                    "access_type": "free",
                    "is_owned": False
                }
            
            # Song has a price - return PAYMENT_REQUIRED with pricing details
            return False, "PAYMENT_REQUIRED", {
                "access_type": "none",
                "price": marketplace_song.price,
                "currency": getattr(marketplace_song, 'currency', 'USD'),
                "requires_premium": getattr(marketplace_song, 'is_premium', False),
                "song_id": song_id
            }
        
        # 4. Check premium content table
        premium_content = self.db.query(PremiumContent).filter_by(song_id=song_id).first()
        if premium_content:
            if getattr(premium_content, 'is_free_preview', False):
                return True, None, {
                    "access_type": "free_preview",
                    "is_owned": False,
                    "preview_duration": 30
                }
            
            return False, "PAYMENT_REQUIRED", {
                "access_type": "none",
                "price": getattr(premium_content, 'price', 0.99),
                "currency": getattr(premium_content, 'currency', 'USD'),
                "requires_premium": True,
                "song_id": song_id
            }
        
        # 5. Default: song not in marketplace - treat as free (legacy songs)
        return True, None, {
            "access_type": "free",
            "is_owned": False,
            "note": "Song not in marketplace - treated as free"
        }
