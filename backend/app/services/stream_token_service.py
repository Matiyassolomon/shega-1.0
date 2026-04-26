"""
Stream Token Service
Generates and validates time-limited signed tokens for direct media access.
Eliminates the need for the API server to proxy all audio bytes.

Architecture:
- /playback/start issues a signed JWT stream token
- /playback/media validates the token and returns HTTP 307 redirect to Navidrome
- Audio bytes flow directly from Navidrome to client
- API server only handles authorization (control plane), not media transport
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.core.settings import get_settings


settings = get_settings()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _json_dumps(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


class StreamTokenService:
    """
    Service for generating and validating signed stream access tokens.
    
    Tokens are short-lived JWTs signed with the app secret key.
    They encode: session_id, user_id, song_id, quality, expiry.
    
    Usage:
        token = StreamTokenService.generate_token(session_id, user_id, song_id, quality)
        # ... client uses token in URL ...
        payload = StreamTokenService.validate_token(token)
        # payload contains session_id, user_id, song_id, quality, exp
    """
    
    TOKEN_TTL_SECONDS = 300  # 5 minutes - tokens are short-lived
    
    @classmethod
    def generate_token(
        cls,
        session_id: str,
        user_id: int,
        song_id: str,
        quality: str,
        bitrate: int,
    ) -> str:
        """
        Generate a signed stream access token.
        
        The token is a JWT-like structure:
        base64url(header).base64url(payload).base64url(signature)
        
        Payload contains:
        - session_id: The playback session ID
        - user_id: The authorized user
        - song_id: The song being accessed
        - quality: Audio quality level
        - bitrate: Target bitrate
        - exp: Expiration timestamp (Unix epoch)
        - iat: Issued-at timestamp
        - jti: Unique token ID (prevents replay)
        """
        now = int(time.time())
        ttl = cls.TOKEN_TTL_SECONDS
        
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sid": session_id,
            "sub": str(user_id),
            "song": song_id,
            "qual": quality,
            "br": bitrate,
            "exp": now + ttl,
            "iat": now,
            "jti": secrets.token_hex(8),
        }
        
        encoded_header = _b64url_encode(_json_dumps(header))
        encoded_payload = _b64url_encode(_json_dumps(payload))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        
        signature = hmac.new(
            settings.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        encoded_signature = _b64url_encode(signature)
        
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"
    
    @classmethod
    def validate_token(cls, token: str) -> Optional[dict]:
        """
        Validate a stream access token.
        
        Returns the decoded payload if valid, None if invalid or expired.
        Performs:
        1. Format validation
        2. Signature verification (constant-time)
        3. Expiration check
        4. Required claims check
        """
        if not token or token.count(".") != 2:
            return None
        
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError:
            return None
        
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(
            settings.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        
        try:
            provided_signature = _b64url_decode(encoded_signature)
            payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None
        
        # Constant-time signature comparison
        if not hmac.compare_digest(provided_signature, expected_signature):
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if not isinstance(exp, int) or exp <= int(time.time()):
            return None
        
        # Check required claims
        required = {"sid", "sub", "song", "qual", "br", "exp", "iat", "jti"}
        if not required.issubset(payload.keys()):
            return None
        
        return payload
    
    @classmethod
    def build_media_url(cls, token: str, base_url: str = "/api/v1/playback/media") -> str:
        """Build the media access URL from a token."""
        return f"{base_url}?token={token}"


def generate_stream_token(
    session_id: str,
    user_id: int,
    song_id: str,
    quality: str,
    bitrate: int,
) -> str:
    """Convenience function to generate a stream token."""
    return StreamTokenService.generate_token(session_id, user_id, song_id, quality, bitrate)


def validate_stream_token(token: str) -> Optional[dict]:
    """Convenience function to validate a stream token."""
    return StreamTokenService.validate_token(token)
