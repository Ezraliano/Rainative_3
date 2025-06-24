import httpx
import logging
from typing import Optional
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

class TranscriberService:
    """
    Service for transcribing YouTube videos using youtube-transcript-api.
    """
    
    def __init__(self):
        # Inisialisasi tidak memerlukan apa-apa untuk pustaka ini
        pass
        
    def _extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from a YouTube URL.
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

    async def get_transcript(self, youtube_url: str) -> str:
        """
        Extract transcript from a YouTube video using its generated captions.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Video transcript as a single string.
        """
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL, could not extract video ID.")

            logger.info(f"Getting transcript for video ID: {video_id}")
            
            # Mengambil daftar transkrip menggunakan pustaka
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Menggabungkan semua teks dari transkrip menjadi satu string
            transcript_text = " ".join([item['text'] for item in transcript_list])
            
            if not transcript_text:
                logger.warning(f"Transcript for {video_id} is empty.")
                raise ValueError("No transcript available for this video.")

            return transcript_text.strip()
            
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            raise Exception(f"Failed to get transcript: {str(e)}")
    
    async def _extract_audio_from_youtube(self, youtube_url: str) -> str:
        """
        Extract audio from YouTube video for transcription.
        
        TODO: Implement using yt-dlp or similar library
        """
        pass
    
    async def _transcribe_with_whisper(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        TODO: Implement Whisper API integration
        """
        pass