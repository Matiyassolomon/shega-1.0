"""
Navidrome integration service
Generates Subsonic-compatible stream URLs
"""
import hashlib
import random
import string
from typing import Optional
from urllib.parse import urlencode
from app.core.config import settings


class NavidromeService:
    """
    Navidrome Subsonic API integration
    Generates secure stream URLs with token auth
    """
    
    def __init__(self):
        self.base_url = getattr(settings, "NAVIDROME_URL", "http://navidrome:4533")
        self.api_version = "1.16.1"
        self.client_name = "music-platform"
    
    def generate_stream_url(
        self,
        song_id: str,
        username: str,
        password: str = None,
        max_bitrate: int = 320,
        time_offset: int = None,
        time_limit: int = None
    ) -> str:
        """
        Generate secure Navidrome stream URL
        Uses MD5(password + salt) token auth
        """
        # Get Navidrome credentials
        navidrome_pass = password or self._get_user_navidrome_password(username)
        
        # Generate random salt
        salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        # Create token: md5(password + salt)
        token = hashlib.md5(f"{navidrome_pass}{salt}".encode()).hexdigest()
        
        # Build params
        params = {
            "id": song_id,
            "u": username,
            "t": token,
            "s": salt,
            "v": self.api_version,
            "c": self.client_name,
            "maxBitRate": max_bitrate,
        }
        
        # Optional time-based preview
        if time_offset is not None:
            params["offset"] = time_offset
        if time_limit is not None:
            params["time"] = time_limit
        
        query_string = urlencode(params)
        return f"{self.base_url}/rest/stream.view?{query_string}"
    
    def generate_preview_url(
        self,
        song_id: str,
        duration_seconds: int = 30
    ) -> str:
        """
        Generate preview URL for unpaid songs.
        
        Uses a dedicated preview account configured in settings.
        Never hardcode credentials.
        """
        # SECURITY: Get preview credentials from secure config
        preview_user = getattr(settings, "NAVIDROME_PREVIEW_USER", None)
        preview_pass = getattr(settings, "NAVIDROME_PREVIEW_PASS", None)
        
        if not preview_user or not preview_pass:
            raise ValueError(
                "Preview credentials not configured. "
                "Please set NAVIDROME_PREVIEW_USER and NAVIDROME_PREVIEW_PASS in settings."
            )
        
        return self.generate_stream_url(
            song_id=song_id,
            username=preview_user,
            password=preview_pass,
            max_bitrate=128,
            time_offset=0,
            time_limit=duration_seconds
        )
    
    def generate_download_url(
        self,
        song_id: str,
        username: str,
        password: str = None
    ) -> str:
        """Generate download URL (for purchased songs)"""
        navidrome_pass = password or self._get_user_navidrome_password(username)
        
        salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        token = hashlib.md5(f"{navidrome_pass}{salt}".encode()).hexdigest()
        
        params = {
            "id": song_id,
            "u": username,
            "t": token,
            "s": salt,
            "v": self.api_version,
            "c": self.client_name,
        }
        
        query_string = urlencode(params)
        return f"{self.base_url}/rest/download.view?{query_string}"
    
    def _get_user_navidrome_password(self, username: str) -> str:
        """
        Get Navidrome password for user.
        
        SECURITY: Never return default passwords. Each user must have
        their own Navidrome credentials or use SSO.
        
        Raises:
            ValueError: If user credentials are not configured
        """
        # TODO: Implement proper user credential lookup
        # Option 1: Fetch from secure credential store (e.g., HashiCorp Vault, AWS Secrets Manager)
        # Option 2: Use Navidrome's token-based auth with user-specific tokens
        # Option 3: Implement SSO/SAML integration where Navidrome trusts our auth
        
        # For now, raise an error to force proper implementation
        # In a real system, this would look up per-user credentials
        navidrome_user_creds = getattr(settings, "NAVIDROME_USER_CREDENTIALS", {})
        
        if username in navidrome_user_creds:
            return navidrome_user_creds[username]
        
        # SECURITY: Do NOT fall back to default password
        raise ValueError(
            f"Navidrome credentials not configured for user: {username}. "
            f"Please configure NAVIDROME_USER_CREDENTIALS in settings or implement SSO."
        )
    
    def ping(self) -> bool:
        """Check if Navidrome is reachable"""
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/rest/ping.view",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
