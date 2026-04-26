"""
Audio quality selection service
Spotify-level adaptive streaming quality
"""
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class QualityConfig:
    quality: str
    bitrate_kbps: int
    codec: str
    reason: str
    can_upgrade: bool = False


class AudioQualityService:
    """Determines optimal audio quality for playback"""
    
    # Quality definitions (kbps)
    QUALITY_LEVELS = {
        "low": 64,      # HE-AAC for mobile data
        "medium": 128,  # AAC for average WiFi
        "high": 320,    # MP3/AAC for good WiFi
        "lossless": 1411,  # FLAC
    }
    
    # Codec selection
    CODECS = {
        "low": "he-aac",
        "medium": "aac",
        "high": "aac",
        "lossless": "flac",
    }
    
    def determine_quality(
        self,
        user: Any,
        device: Any,
        network_type: str = "wifi",
        network_quality_score: float = 1.0
    ) -> QualityConfig:
        """
        Determine optimal audio quality
        Logic: final = MIN(device_max, user_pref, network_limit)
        """
        # Get user preference
        user_pref = getattr(user, "preferred_quality", "high")
        user_tier = getattr(user, "subscription_tier", "free")
        
        # Get device capability
        device_max = getattr(device, "max_audio_quality", "high")
        
        # Network-based limit
        network_limit = self._get_network_limit(network_type, network_quality_score)
        
        # Subscription limit
        sub_limit = self._get_subscription_limit(user_tier)
        
        # Apply constraints
        qualities = ["low", "medium", "high", "lossless"]
        
        user_idx = qualities.index(user_pref) if user_pref in qualities else 2
        device_idx = qualities.index(device_max) if device_max in qualities else 2
        network_idx = qualities.index(network_limit) if network_limit in qualities else 2
        sub_idx = qualities.index(sub_limit) if sub_limit in qualities else 1
        
        # Take minimum (most restrictive)
        final_idx = min(user_idx, device_idx, network_idx, sub_idx)
        
        # Auto-downgrade for poor network
        if network_quality_score < 0.3 and final_idx > 0:
            final_idx = max(0, final_idx - 1)
        
        final_quality = qualities[final_idx]
        
        # Build reason
        reason = self._build_reason(
            user_pref, device_max, network_limit, 
            network_type, final_quality
        )
        
        # Can upgrade if network improves
        can_upgrade = (
            network_quality_score > 0.8 and 
            final_idx < min(device_idx, sub_idx)
        )
        
        return QualityConfig(
            quality=final_quality,
            bitrate_kbps=self.QUALITY_LEVELS[final_quality],
            codec=self.CODECS[final_quality],
            reason=reason,
            can_upgrade=can_upgrade
        )
    
    def _get_network_limit(self, network_type: str, quality_score: float) -> str:
        """Determine quality limit based on network"""
        if network_type == "mobile_data":
            return "medium" if quality_score > 0.5 else "low"
        elif network_type == "wifi":
            if quality_score > 0.8:
                return "lossless"
            elif quality_score > 0.5:
                return "high"
            else:
                return "medium"
        return "medium"
    
    def _get_subscription_limit(self, tier: str) -> str:
        """Quality limits by subscription tier"""
        limits = {
            "free": "medium",
            "premium": "high",
            "premium_plus": "lossless",
            "family": "lossless",
        }
        return limits.get(tier, "medium")
    
    def _build_reason(
        self, user_pref: str, device_max: str, 
        network_limit: str, network_type: str, final: str
    ) -> str:
        """Human-readable explanation"""
        if final != user_pref:
            return f"Adjusted from {user_pref} to {final} for {network_type}"
        return f"Streaming at {final} quality"
