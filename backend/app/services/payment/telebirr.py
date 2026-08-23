from typing import Dict, Any, Optional
import httpx
import hmac
import hashlib
import json
import os
import logging
from datetime import datetime

from app.services.payment.base import PaymentProvider, PaymentError

logger = logging.getLogger(__name__)

class TelebirrProvider(PaymentProvider):
    def __init__(self):
        self.api_key = os.getenv("TELEBIRR_API_KEY")
        self.api_secret = os.getenv("TELEBIRR_API_SECRET")
        self.base_url = os.getenv("TELEBIRR_API_URL", "https://api.telebirr.et/v1")
        self.callback_url = os.getenv("TELEBIRR_CALLBACK_URL")
        self.timeout = 30

    async def initiate_payment(
        self,
        amount: float,
        currency: str,
        reference: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Initiate Telebirr payment"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/payment/initiate",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "amount": amount,
                        "currency": currency,
                        "reference": reference,
                        "callback_url": self.callback_url,
                        "metadata": metadata or {}
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "reference": data.get("reference"),
                    "payment_url": data.get("payment_url"),
                    "status": data.get("status", "pending"),
                    "provider": "telebirr"
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Telebirr initiate error: {e}")
            raise PaymentError(str(e), provider="telebirr")

    async def verify_payment(
        self,
        reference: str,
        provider_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify Telebirr payment"""
        try:
            # Verify webhook signature
            signature = provider_data.get("signature")
            if not await self._verify_signature(provider_data.get("body", b""), signature):
                return {"status": "failed", "message": "Invalid signature"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/payment/status/{reference}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "completed":
                    return {
                        "status": "success",
                        "reference": reference,
                        "amount": data.get("amount"),
                        "currency": data.get("currency"),
                        "completed_at": data.get("completed_at")
                    }
                else:
                    return {
                        "status": "failed",
                        "message": data.get("message", "Payment not completed"),
                        "reference": reference
                    }
                    
        except httpx.HTTPError as e:
            logger.error(f"Telebirr verify error: {e}")
            return {"status": "failed", "message": str(e)}

    async def handle_webhook(
        self,
        raw_body: bytes,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Handle Telebirr webhook"""
        try:
            # Verify signature
            signature = headers.get("X-Telebirr-Signature")
            if not signature or not await self._verify_signature(raw_body, signature):
                return {"status": "failed", "message": "Invalid signature"}
            
            # Parse webhook data
            data = json.loads(raw_body)
            
            return {
                "status": "success",
                "reference": data.get("reference"),
                "event": data.get("event"),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Telebirr webhook error: {e}")
            return {"status": "failed", "message": str(e)}

    async def refund_payment(
        self,
        reference: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Refund a Telebirr payment"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/payment/refund",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "reference": reference,
                        "amount": amount
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "status": "success",
                    "reference": data.get("reference"),
                    "refund_id": data.get("refund_id")
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Telebirr refund error: {e}")
            raise PaymentError(str(e), provider="telebirr")

    async def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not signature:
            return False
        
        expected = hmac.new(
            self.api_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)