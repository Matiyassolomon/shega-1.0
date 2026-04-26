"""
YouTube Data API integration for external trending signals.
Provides weak external signal (20% weight) to boost internal recommendations.
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
import requests
from urllib.parse import quote

from app.core.cache import cache

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class YouTubeTrendingVideo:
    """Represents a trending music video from YouTube."""
    video_id: str
    title: str
    artist: Optional[str]
    channel_title: str
    view_count: int
    like_count: int
    published_at: datetime
    region: str
    youtube_score: float  # Normalized 0-100


@dataclass
class YouTubeBoostResult:
    """Result of matching internal song to YouTube trending."""
    song_id: int
    matched_title: str
    match_confidence: float  # 0.0 - 1.0
    youtube_video_id: str
    youtube_views: int
    boost_score: float  # The score to add to internal ranking (0-20 points max)


class YouTubeIntegrationService:
    """
    YouTube Data API integration for music trending.
    
    Design Principles:
    - YouTube signal is WEAK (20% max weight)
    - Internal system is STRONG (80% weight)
    - YouTube is used only as a verification/trending boost
    - No user data is synced with YouTube
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.enabled = bool(self.api_key)
        self.boost_weight = 0.20  # 20% maximum boost
        self.max_boost_points = 20.0  # Maximum points to add to score
        
        if not self.enabled:
            logger.warning("YouTube API key not configured. YouTube trending disabled.")
    
    def get_trending_music(
        self,
        region_code: str = "ET",  # Ethiopia default
        max_results: int = 25
    ) -> List[YouTubeTrendingVideo]:
        """
        Fetch trending music videos from YouTube.
        Uses YouTube's "mostPopular" chart filtered for music category.
        """
        if not self.enabled:
            logger.debug("YouTube integration disabled")
            return []
        
        # Check cache first (cache for 2 hours)
        cache_key = f"youtube:trending:{region_code}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"YouTube trending cache hit for {region_code}")
            return [YouTubeTrendingVideo(**v) for v in cached]
        
        try:
            # Search for trending music videos
            url = f"{YOUTUBE_API_BASE}/search"
            params = {
                "part": "snippet",
                "chart": "mostPopular",  # This requires a different endpoint
                "regionCode": region_code,
                "videoCategoryId": "10",  # Music category
                "maxResults": max_results,
                "key": self.api_key,
            }
            
            # Actually use the videos endpoint for trending
            trending_url = f"{YOUTUBE_API_BASE}/videos"
            trending_params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region_code,
                "videoCategoryId": "10",  # Music
                "maxResults": max_results,
                "key": self.api_key,
            }
            
            response = requests.get(
                trending_url,
                params=trending_params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            trending = []
            for item in data.get("items", []):
                try:
                    video = self._parse_video_item(item, region_code)
                    if video:
                        trending.append(video)
                except Exception as e:
                    logger.warning(f"Failed to parse YouTube video: {e}")
                    continue
            
            # Cache for 2 hours
            cache.set(
                cache_key,
                [self._video_to_dict(v) for v in trending],
                ttl=7200
            )
            
            logger.info(f"Fetched {len(trending)} trending videos from YouTube for {region_code}")
            return trending
            
        except requests.exceptions.RequestException as e:
            logger.error(f"YouTube API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"YouTube trending fetch error: {e}")
            return []
    
    def search_music_video(
        self,
        query: str,
        artist: Optional[str] = None,
        max_results: int = 5
    ) -> List[YouTubeTrendingVideo]:
        """
        Search for a specific music video on YouTube.
        Used to find trending info for specific songs.
        """
        if not self.enabled:
            return []
        
        # Build search query
        search_query = query
        if artist:
            search_query = f"{artist} {query}"
        
        cache_key = f"youtube:search:{quote(search_query.lower())}"
        cached = cache.get(cache_key)
        if cached:
            return [YouTubeTrendingVideo(**v) for v in cached]
        
        try:
            url = f"{YOUTUBE_API_BASE}/search"
            params = {
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "videoCategoryId": "10",  # Music
                "maxResults": max_results,
                "key": self.api_key,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            
            if not video_ids:
                return []
            
            # Get detailed stats
            videos_url = f"{YOUTUBE_API_BASE}/videos"
            videos_params = {
                "part": "snippet,statistics",
                "id": ",".join(video_ids),
                "key": self.api_key,
            }
            
            videos_response = requests.get(videos_url, params=videos_params, timeout=10)
            videos_response.raise_for_status()
            videos_data = videos_response.json()
            
            results = []
            for item in videos_data.get("items", []):
                video = self._parse_video_item(item, "search")
                if video:
                    results.append(video)
            
            # Cache for 6 hours (search results change less)
            cache.set(
                cache_key,
                [self._video_to_dict(v) for v in results],
                ttl=21600
            )
            
            return results
            
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return []
    
    def match_and_boost_internal_songs(
        self,
        internal_songs: List[Dict],
        region_code: str = "ET"
    ) -> Dict[int, YouTubeBoostResult]:
        """
        Match internal songs to YouTube trending and calculate boost scores.
        
        Args:
            internal_songs: List of dicts with 'id', 'title', 'artist', 'current_score'
            region_code: Region for trending context
            
        Returns:
            Dict mapping song_id to boost result with confidence and score
        """
        if not self.enabled:
            logger.debug("YouTube boost skipped - integration disabled")
            return {}
        
        # Get trending videos
        trending = self.get_trending_music(region_code)
        if not trending:
            return {}
        
        boost_results = {}
        
        for song in internal_songs:
            song_id = song["id"]
            title = song.get("title", "")
            artist = song.get("artist", "")
            current_score = song.get("current_score", 50.0)
            
            # Try to match song to trending videos
            best_match = None
            best_confidence = 0.0
            
            for video in trending:
                confidence = self._calculate_match_confidence(
                    title, artist, video
                )
                if confidence > best_confidence and confidence >= 0.6:
                    best_confidence = confidence
                    best_match = video
            
            # Also try direct search if no good trending match
            if not best_match:
                search_results = self.search_music_video(title, artist, max_results=3)
                for video in search_results:
                    confidence = self._calculate_match_confidence(title, artist, video)
                    if confidence > best_confidence and confidence >= 0.7:
                        best_confidence = confidence
                        best_match = video
            
            if best_match:
                # Calculate boost based on match confidence and video popularity
                # Max boost is 20% of current score or 20 points, whichever is lower
                view_boost = min(best_match.view_count / 100000, 10)  # Cap at 10 points for views
                confidence_multiplier = best_confidence * 0.5  # Up to 0.5 boost
                
                boost_score = min(
                    (view_boost + confidence_multiplier * 10) * self.boost_weight,
                    self.max_boost_points,
                    current_score * self.boost_weight
                )
                
                boost_results[song_id] = YouTubeBoostResult(
                    song_id=song_id,
                    matched_title=best_match.title,
                    match_confidence=best_confidence,
                    youtube_video_id=best_match.video_id,
                    youtube_views=best_match.view_count,
                    boost_score=round(boost_score, 2)
                )
        
        logger.info(f"YouTube boost applied to {len(boost_results)} songs")
        return boost_results
    
    def _calculate_match_confidence(
        self,
        song_title: str,
        song_artist: Optional[str],
        video: YouTubeTrendingVideo
    ) -> float:
        """
        Calculate confidence score for song-video match.
        Returns 0.0-1.0 confidence level.
        """
        # Normalize for comparison
        song_title_clean = self._clean_string(song_title)
        video_title_clean = self._clean_string(video.title)
        
        confidence = 0.0
        
        # Title similarity (most important)
        if song_title_clean in video_title_clean or video_title_clean in song_title_clean:
            confidence += 0.5
        elif self._calculate_string_similarity(song_title_clean, video_title_clean) > 0.7:
            confidence += 0.4
        
        # Artist match (if available)
        if song_artist and video.artist:
            artist_clean = self._clean_string(song_artist)
            video_artist_clean = self._clean_string(video.artist)
            if artist_clean == video_artist_clean:
                confidence += 0.3
            elif artist_clean in video_artist_clean or video_artist_clean in artist_clean:
                confidence += 0.2
        
        # Channel verification (music channels are more reliable)
        if any(kw in video.channel_title.lower() for kw in ["vevo", "official", "music"]):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _parse_video_item(
        self,
        item: Dict,
        region: str
    ) -> Optional[YouTubeTrendingVideo]:
        """Parse YouTube API video item."""
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            
            video_id = item.get("id")
            if isinstance(video_id, dict):
                video_id = video_id.get("videoId")
            
            title = snippet.get("title", "")
            channel = snippet.get("channelTitle", "")
            published = snippet.get("publishedAt", "")
            
            # Extract artist from title (heuristic)
            artist = self._extract_artist_from_title(title, channel)
            
            # Parse stats
            views = int(statistics.get("viewCount", 0))
            likes = int(statistics.get("likeCount", 0))
            
            # Calculate normalized YouTube score (0-100)
            # Based on view velocity and engagement
            youtube_score = min(views / 10000, 100) * 0.7 + min(likes / 1000, 100) * 0.3
            
            return YouTubeTrendingVideo(
                video_id=video_id,
                title=title,
                artist=artist,
                channel_title=channel,
                view_count=views,
                like_count=likes,
                published_at=datetime.fromisoformat(published.replace("Z", "+00:00")),
                region=region,
                youtube_score=round(youtube_score, 2)
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse video item: {e}")
            return None
    
    def _extract_artist_from_title(self, title: str, channel: str) -> Optional[str]:
        """Extract artist name from video title using heuristics."""
        # Common patterns: "Artist - Title" or "Artist | Title"
        separators = [" - ", " | ", " – ", " — ", " // "]
        for sep in separators:
            if sep in title:
                parts = title.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip()
        
        # Check channel name (often contains artist for VEVO)
        if "vevo" in channel.lower():
            # Extract artist from channel (e.g., "TaylorSwiftVEVO" -> "Taylor Swift")
            return self._format_vevo_artist(channel)
        
        return None
    
    def _format_vevo_artist(self, channel: str) -> str:
        """Format VEVO channel name to artist name."""
        # Remove VEVO suffix
        artist = channel.replace("VEVO", "").replace("vevo", "")
        # Add spaces before capitals
        artist = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', artist)
        return artist.strip()
    
    def _clean_string(self, s: str) -> str:
        """Clean string for comparison."""
        if not s:
            return ""
        # Lowercase, remove special chars, extra spaces
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity (0-1)."""
        if not s1 or not s2:
            return 0.0
        
        # Use word overlap ratio
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _video_to_dict(self, video: YouTubeTrendingVideo) -> Dict:
        """Convert video to dictionary for caching."""
        return {
            "video_id": video.video_id,
            "title": video.title,
            "artist": video.artist,
            "channel_title": video.channel_title,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "published_at": video.published_at.isoformat(),
            "region": video.region,
            "youtube_score": video.youtube_score,
        }


# Global service instance
youtube_service = YouTubeIntegrationService()
