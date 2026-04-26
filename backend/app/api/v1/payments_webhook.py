"""
Payment webhook handlers for song purchases
"""
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/payment-confirmed")
async def handle_payment_webhook(
    request: Request,
    signature: str = Header(None, alias="X-Webhook-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle payment confirmation from payment provider
    Grants song access after successful purchase
    """
    import hashlib
    import json
    
    payload = await request.json()
    
    # Verify webhook signature (implement based on your provider)
    # expected_sig = hashlib.sha256(f"{payload}{webhook_secret}".encode()).hexdigest()
    # if signature != expected_sig:
    #     raise HTTPException(401, "Invalid signature")
    
    # Extract payment details
    payment_intent_id = payload.get("payment_intent_id") or payload.get("id")
    metadata = payload.get("metadata", {})
    
    payment_type = metadata.get("type")
    user_id = metadata.get("user_id")
    song_id = metadata.get("song_id")
    
    if payment_type == "song_purchase":
        from app.services.song_purchase_service import SongPurchaseService
        
        purchase_service = SongPurchaseService(db)
        
        try:
            result = await purchase_service.confirm_purchase(
                payment_id=payment_intent_id,
                user_id=user_id,
                song_id=song_id,
                price=metadata.get("price")
            )
            
            return {
                "received": True,
                "processed": True,
                "access_granted": result["success"],
                "song_id": song_id,
                "user_id": user_id
            }
            
        except Exception as e:
            # Log error but return 200 to prevent retries
            return {
                "received": True,
                "processed": False,
                "error": str(e)
            }
    
    # Handle subscription payments
    elif payment_type == "subscription":
        # Update user subscription status
        # Implementation depends on your user model
        return {
            "received": True,
            "processed": True,
            "type": "subscription"
        }
    
    return {"received": True, "processed": False, "reason": "Unknown payment type"}


@router.post("/payment-failed")
async def handle_payment_failure(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle failed payments"""
    payload = await request.json()
    
    # Log for analytics/retry logic
    payment_id = payload.get("payment_intent_id")
    
    return {"received": True, "status": "logged"}
