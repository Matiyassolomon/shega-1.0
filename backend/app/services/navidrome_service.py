"""
Navidrome Service - Internal Proxy
Keeps Navidrome credentials fully internal, no exposure to client
"""
import hashlib
import random
import string
from typing import Optional
from urllib.parse import urlencode
import httpx
from app.core.config import settings


class NavidromeService:
    """
    Internal Navidrome integration service.
    All Navidrome interactions happen server-side only.
    Client never sees Navidrome URLs or credentials.
    """
    
    def __init__(self):
        self.base_url = getattr(settings, "NAVIDROME_URL", "http://localhost:4533")
        self.api_version = "1.16.1"
        self.client_name = "shega-backend"
    
    def _get_user_credentials(self, user_id: str) -> tuple[str, str]:
        """
        Get Navidrome credentials for a user.
        In production: fetch from secure storage or use SSO.
        NEVER expose these to client.
        
        SECURITY: No default credentials. Must be explicitly configured.
        """
        # Get credentials from secure config - NO DEFAULTS
        username = getattr(settings, "NAVIDROME_USER", None)
        password = getattr(settings, "NAVIDROME_PASS", None)
        
        if not username or not password:
            raise ValueError(
                "Navidrome credentials not configured. "
                "Please set NAVIDROME_USER and NAVIDROME_PASS in settings."
            )
        
        # TODO: Implement proper per-user credential mapping
        # For production, map user_id to specific Navidrome account or use SSO
        # Option 1: User-specific credentials from secure vault
        # Option 2: Shared service account with user tracking in headers
        # Option 3: JWT tokens with Navidrome OAuth2
        
        return username, password
    
    def _generate_token(self, password: str, salt: str) -> str:
        """Generate Subsonic token from password + salt"""
        return hashlib.md5(f"{password}{salt}".encode()).hexdigest()
    
    def _build_subsonic_params(
        self,
        username: str,
        password: str,
        endpoint: str,
        params: dict
    ) -> dict:
        """Build Subsonic API parameters"""
        salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        token = self._generate_token(password, salt)
        
        base_params = {
            "u": username,
            "t": token,
            "s": salt,
            "v": self.api_version,
            "c": self.client_name,
        }
        base_params.update(params)
        
        return base_params
    
    async def get_stream_url(
        self,
        user_id: str,
        song_id: str,
        max_bitrate: int = 320,
        time_offset: Optional[int] = None,
        time_limit: Optional[int] = None
    ) -> str:
        """
        INTERNAL: Get Navidrome stream URL for server-side use.
        This URL is NEVER returned to client.
        """
        username, password = self._get_user_credentials(user_id)
        
        params = {
            "id": song_id,
            "maxBitRate": max_bitrate,
        }
        
        if time_offset is not None:
            params["offset"] = time_offset
        if time_limit is not None:
            params["time"] = time_limit
        
        subsonic_params = self._build_subsonic_params(
            username, password, "stream.view", params
        )
        
        query_string = urlencode(subsonic_params)
        return f"{self.base_url}/rest/stream.view?{query_string}"
    
    async def get_song_info(self, user_id: str, song_id: str) -> dict:
        """Get song metadata from Navidrome"""
        username, password = self._get_user_credentials(user_id)
        
        params = self._build_subsonic_params(
            username, password, "getSong.view", {"id": song_id}
        )
        
        query_string = urlencode(params)
        url = f"{self.base_url}/rest/getSong.view?{query_string}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse Subsonic response
                data = response.json()
                subsonic = data.get("subsonic-response", {})
                
                if subsonic.get("status") == "ok":
                    song_data = subsonic.get("song", {})
                    return {
                        "id": song_id,
                        "title": song_data.get("title", "Unknown"),
                        "artist": song_data.get("artist", "Unknown"),
                        "album": song_data.get("album"),
                        "duration": song_data.get("duration", 0),
                        "bitrate": song_data.get("bitRate"),
                        "path": song_data.get("path"),
                    }
                else:
                    # Return fallback on API error
                    return {
                        "id": song_id,
                        "title": "Unknown",
                        "artist": "Unknown",
                        "duration": 0,
                        "error": subsonic.get("error", {}).get("message", "Unknown error"),
                    }
                    
        except httpx.RequestError as e:
            # Network error - return fallback
            return {
                "id": song_id,
                "title": "Unknown",
                "artist": "Unknown",
                "duration": 0,
                "error": f"Failed to connect to Navidrome: {str(e)}",
            }
        except Exception as e:
            # Unexpected error
            return {
                "id": song_id,
                "title": "Unknown",
                "artist": "Unknown",
                "duration": 0,
                "error": str(e),
            }
