import httpx
import logging
from typing import Optional
import os
import re
import tempfile
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

logger = logging.getLogger(__name__)

class TranscriberService:
    """
    Service for transcribing YouTube videos using youtube-transcript-api.
    """
    
    def __init__(self):
        # Inisialisasi tidak memerlukan apa-apa untuk pustaka ini
        self._ffmpeg_available = self._check_ffmpeg_availability()
        
    def _check_ffmpeg_availability(self) -> bool:
        """
        Check if ffmpeg is available in the system.
        """
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
        
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
        Falls back to audio extraction if no subtitles are available.
        
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
            
            # Coba ambil transkrip dari subtitle terlebih dahulu
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([item['text'] for item in transcript_list])
                
                if transcript_text:
                    return transcript_text.strip()
                    
            except (NoTranscriptFound, TranscriptsDisabled):
                logger.info(f"No subtitles available for {video_id}, attempting audio extraction...")
                # Fallback ke audio extraction jika subtitle tidak tersedia
                if not self._ffmpeg_available:
                    raise Exception("No subtitles available for this video and audio extraction requires ffmpeg (not installed). Please install ffmpeg or try a video with subtitles enabled.")
                return await self._extract_audio_and_transcribe(youtube_url)
            
            raise ValueError("No transcript available for this video.")

        except VideoUnavailable:
            logger.error(f"Video is unavailable for video ID: {video_id}")
            raise Exception("This video is not available or has been removed. Please check the URL and try again.")
            
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            raise Exception(f"Failed to get transcript: {str(e)}")
    
    async def _extract_audio_and_transcribe(self, youtube_url: str) -> str:
        """
        Extract audio from YouTube video and transcribe it using yt-dlp.
        This is a fallback method when subtitles are not available.
        """
        try:
            # Buat temporary directory untuk menyimpan audio
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_file = os.path.join(temp_dir, "audio.mp3")
                
                # Extract audio menggunakan yt-dlp dengan opsi yang lebih sederhana
                cmd = [
                    "yt-dlp",
                    "-x",  # Extract audio
                    "--audio-format", "mp3",
                    "--audio-quality", "0",  # Best quality
                    "--no-playlist",  # Skip playlists
                    "--no-warnings",  # Reduce noise in logs
                    "-o", audio_file,
                    youtube_url
                ]
                
                logger.info(f"Extracting audio from {youtube_url}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    # Cek apakah error disebabkan oleh ffmpeg
                    if "ffprobe and ffmpeg not found" in result.stderr:
                        logger.error("ffmpeg not found. Audio extraction requires ffmpeg to be installed.")
                        raise Exception("Audio extraction requires ffmpeg to be installed. Please install ffmpeg or try a video with subtitles enabled.")
                    elif "HTTP Error 403" in result.stderr:
                        logger.error("YouTube blocked access to this video")
                        raise Exception("YouTube blocked access to this video. Please try a video with subtitles enabled.")
                    else:
                        logger.error(f"yt-dlp failed: {result.stderr}")
                        raise Exception("Failed to extract audio from video. Please try a video with subtitles enabled.")
                
                # Cari file audio yang dihasilkan
                audio_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                if not audio_files:
                    raise Exception("No audio file was extracted.")
                
                audio_path = os.path.join(temp_dir, audio_files[0])
                
                # TODO: Implement transcription using Whisper API or local model
                # Untuk sementara, return placeholder
                logger.warning("Audio extraction successful, but transcription not implemented yet.")
                raise Exception("Audio extraction successful, but automatic transcription is not yet implemented. Please try a video with subtitles enabled.")
                
        except subprocess.TimeoutExpired:
            raise Exception("Audio extraction timed out. Please try a shorter video or one with subtitles enabled.")
        except Exception as e:
            logger.error(f"Error in audio extraction: {str(e)}")
            raise Exception(f"Failed to extract and transcribe audio: {str(e)}")
    
    async def _transcribe_with_whisper(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        TODO: Implement Whisper API integration
        """
        pass 