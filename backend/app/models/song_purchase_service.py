"""
Song purchase service integration
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.access_control_service import AccessControlService


class SongPurchaseService:
    """Handles song purchase flow"""
    
    def __init__(self, db: Session):
        self.db = db
        self.access_service = AccessControlService(db)
    
    async def initiate_purchase(
        self,
        user_id: str,
        song_id: str,
        payment_method: str = "stripe"
    ) -> Dict[str, Any]:
        """Initiate song purchase"""
        from app.models.song_access import SongPricing
        
        pricing = self.db.query(SongPricing).filter(
            SongPricing.song_id == song_id
        ).first()
        
        if not pricing:
            raise HTTPException(404, "Song pricing not found")
        
        if pricing.is_free:
            raise HTTPException(400, "Song is already free")
        
        # Check if already owned
        can_play, error, _ = await self.access_service.check_playback_access(
            user_id, song_id
        )
        if can_play:
            raise HTTPException(400, "You already have access to this song")
        
        # Calculate price
        price = pricing.individual_price or 0.99
        if pricing.promo_price and pricing.promo_ends_at and pricing.promo_ends_at > datetime.utcnow():
            price = pricing.promo_price
        
        # Create payment intent
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(self.db)
        
        payment_intent = await payment_service.create_payment_intent(
            user_id=user_id,
            amount=int(price * 100),  # cents
            currency="USD",
            metadata={
                "type": "song_purchase",
                "song_id": song_id,
                "price": price
            }
        )
        
        return {
            "payment_intent_id": payment_intent["id"],
            "client_secret": payment_intent.get("client_secret"),
            "amount": price,
            "currency": "USD",
            "song_id": song_id,
            "status": "requires_payment",
            "redirect_url": payment_intent.get("redirect_url")
        }
    
    async def confirm_purchase(
        self,
        payment_id: str,
        user_id: str,
        song_id: str,
        price: float = None
    ) -> Dict[str, Any]:
        """Confirm purchase after payment"""
        from app.services.payment_service import PaymentService
        
        payment_service = PaymentService(self.db)
        payment = await payment_service.confirm_payment(payment_id)
        
        if payment["status"] != "completed":
            raise HTTPException(400, "Payment not completed")
        
        # Grant access
        access = await self.access_service.grant_access_after_payment(
            user_id=user_id,
            song_id=song_id,
            payment_id=payment_id,
            access_type="purchase",
            price=price
        )
        
        return {
            "success": True,
            "access_granted": True,
            "access_id": access.id,
            "song_id": song_id,
            "can_play_now": True
        }
