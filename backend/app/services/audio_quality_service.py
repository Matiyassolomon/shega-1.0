"""
Audio Quality Service
Determines optimal audio quality based on user, device, and network conditions
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class QualityLevel(str, Enum):
    LOW = "low"          # 64 kbps
    MEDIUM = "medium"    # 128 kbps
    HIGH = "high"        # 320 kbps
    LOSSLESS = "lossless"  # 1411 kbps


@dataclass
class QualityDecision:
    quality: QualityLevel
    bitrate_kbps: int
    codec: str
    reason: str
    can_upgrade: bool


class AudioQualityService:
    """Determine optimal audio quality for streaming"""
    
    QUALITY_CONFIG = {
        QualityLevel.LOW: {"bitrate": 64, "codec": "mp3"},
        QualityLevel.MEDIUM: {"bitrate": 128, "codec": "mp3"},
        QualityLevel.HIGH: {"bitrate": 320, "codec": "mp3"},
        QualityLevel.LOSSLESS: {"bitrate": 1411, "codec": "flac"},
    }
    
    def determine_quality(
        self,
        user: Optional[dict],
        device: Optional[dict],
        network_type: str,
        network_quality_score: float
    ) -> QualityDecision:
        """
        Determine optimal quality based on:
        - User subscription tier
        - Device capabilities
        - Network type (wifi/mobile)
        - Network quality score (0-1)
        """
        # Start with user's preference if available
        if user and user.get("preferred_quality"):
            preferred = QualityLevel(user["preferred_quality"])
            if self._can_use_quality(preferred, user, device, network_type, network_quality_score):
                return self._build_decision(preferred, "User preference")
        
        # Determine based on network
        if network_type == "mobile_data" and network_quality_score < 0.5:
            return self._build_decision(QualityLevel.LOW, "Mobile data with poor connection")
        
        if network_type == "mobile_data":
            return self._build_decision(QualityLevel.MEDIUM, "Mobile data connection")
        
        # WiFi or good connection
        if network_quality_score < 0.7:
            return self._build_decision(QualityLevel.MEDIUM, "WiFi with variable quality")
        
        # Check subscription tier
        if user and user.get("subscription_tier") == "premium_plus":
            return self._build_decision(QualityLevel.LOSSLESS, "Premium Plus subscription")
        
        if user and user.get("subscription_tier") == "premium":
            return self._build_decision(QualityLevel.HIGH, "Premium subscription")
        
        # Free tier - high quality on good WiFi
        return self._build_decision(QualityLevel.HIGH, "Free tier on good WiFi")
    
    def _can_use_quality(
        self,
        quality: QualityLevel,
        user: Optional[dict],
        device: Optional[dict],
        network_type: str,
        network_quality_score: float
    ) -> bool:
        """Check if quality can be used given constraints"""
        # Lossless requires premium tier
        if quality == QualityLevel.LOSSLESS:
            if not user or user.get("subscription_tier") != "premium_plus":
                return False
        
        # High quality on mobile requires good connection
        if quality == QualityLevel.HIGH and network_type == "mobile_data":
            return network_quality_score >= 0.8
        
        return True
    
    def _build_decision(self, quality: QualityLevel, reason: str) -> QualityDecision:
        config = self.QUALITY_CONFIG[quality]
        return QualityDecision(
            quality=quality,
            bitrate_kbps=config["bitrate"],
            codec=config["codec"],
            reason=reason,
            can_upgrade=quality != QualityLevel.LOSSLESS
        )
