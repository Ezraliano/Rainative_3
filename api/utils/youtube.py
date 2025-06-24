import httpx
import re
import logging
from typing import Optional
from models.schemas import VideoMetadata
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class YouTubeUtils:
    """
    Utility class for YouTube-related operations.
    """
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Video ID string or None if invalid
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_metadata(self, youtube_url: str) -> Optional[VideoMetadata]:
        """
        Get video metadata from YouTube API.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            VideoMetadata object or None if failed
        """
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                logger.error(f"Invalid YouTube URL: {youtube_url}")
                return None
            
            logger.info(f"Getting metadata for video ID: {video_id}")
            
            # TODO: Implement actual YouTube API call
            # if self.youtube_api_key:
            #     return await self._fetch_from_youtube_api(video_id)
            
            # Mock metadata for development
            mock_metadata = VideoMetadata(
                title="Understanding Machine Learning Basics",
                duration=390,  # 6 minutes 30 seconds
                thumbnail_url="https://images.pexels.com/photos/1181671/pexels-photo-1181671.jpeg",
                channel_name="Tech Education Hub",
                view_count=45000,
                like_count=2100,
                published_at=datetime.now(),
                description="A comprehensive guide to machine learning fundamentals for beginners."
            )
            
            return mock_metadata
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {str(e)}")
            return None
    
    async def _fetch_from_youtube_api(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Fetch video metadata from YouTube Data API v3.
        
        TODO: Implement actual YouTube API integration
        """
        if not self.youtube_api_key:
            logger.warning("YouTube API key not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/videos"
                params = {
                    "part": "snippet,statistics,contentDetails",
                    "id": video_id,
                    "key": self.youtube_api_key
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if not data.get("items"):
                    return None
                
                item = data["items"][0]
                snippet = item["snippet"]
                statistics = item.get("statistics", {})
                content_details = item["contentDetails"]
                
                # Parse duration from ISO 8601 format (PT6M30S)
                duration = self._parse_duration(content_details["duration"])
                
                return VideoMetadata(
                    title=snippet["title"],
                    duration=duration,
                    thumbnail_url=snippet["thumbnails"]["high"]["url"],
                    channel_name=snippet["channelTitle"],
                    view_count=int(statistics.get("viewCount", 0)),
                    like_count=int(statistics.get("likeCount", 0)),
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    description=snippet.get("description", "")
                )
                
        except Exception as e:
            logger.error(f"Error fetching from YouTube API: {str(e)}")
            return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration string to seconds.
        
        Args:
            duration_str: ISO 8601 duration (e.g., "PT6M30S")
            
        Returns:
            Duration in seconds
        """
        # TODO: Implement proper ISO 8601 duration parsing
        # For now, return mock duration
        return 390  # 6 minutes 30 seconds
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid YouTube URL
        """
        return self.extract_video_id(url) is not None