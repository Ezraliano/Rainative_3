import os
import re
import logging
import tempfile
import subprocess
from typing import Optional

# Impor library yang relevan
# --- Perubahan: Impor jenis error spesifik dari OpenAI ---
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError 
# ----------------------------------------------------
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
import librosa
from xml.etree.ElementTree import ParseError

logger = logging.getLogger(__name__)

class TranscriberService:
    """
    Service for transcribing YouTube videos using youtube-transcript-api
    with a fallback to OpenAI's Whisper API.
    """
    
    def __init__(self):
        """
        Initializes the service by checking for ffmpeg and setting up the OpenAI client.
        """
        self._ffmpeg_available = self._check_ffmpeg_availability()
        try:
            self.openai_client = OpenAI(timeout=20.0) # Menambahkan timeout default
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
    def _check_ffmpeg_availability(self) -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
            logger.info("ffmpeg is available.")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("ffmpeg not found. Audio extraction will not be available.")
            return False
        
    def _extract_video_id(self, youtube_url: str) -> Optional[str]:
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        logger.warning(f"Could not extract video ID from URL: {youtube_url}")
        return None

    async def get_transcript(self, youtube_url: str) -> str:
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL.")

            logger.info(f"Attempting to fetch transcript for video ID: {video_id}")
            
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([item['text'] for item in transcript_list])
                if transcript_text:
                    logger.info(f"Successfully fetched transcript from captions for video ID: {video_id}")
                    return transcript_text.strip()
            except (NoTranscriptFound, TranscriptsDisabled, ParseError) as e:
                logger.warning(f"Could not fetch subtitles ({type(e).__name__}). Falling back to audio transcription for video ID: {video_id}.")
                if not self._ffmpeg_available:
                    raise Exception("No subtitles available, and ffmpeg is not installed.")
                if not self.openai_client:
                    raise Exception("No subtitles available, and OpenAI API is not configured.")
                return await self._extract_audio_and_transcribe_with_whisper(youtube_url)
            
            raise ValueError("Could not obtain a transcript.")

        except VideoUnavailable:
            logger.error(f"Video is unavailable or private: {youtube_url}")
            raise Exception("This video is not available or has been removed.")
        except Exception as e:
            logger.error(f"An unexpected error occurred for {youtube_url}: {str(e)}", exc_info=True)
            raise

    async def _extract_audio_and_transcribe_with_whisper(self, youtube_url: str) -> str:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = os.path.join(temp_dir, "audio.mp3")
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
                cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "--user-agent", user_agent, "-o", audio_path, youtube_url]
                
                logger.info(f"Executing yt-dlp to extract audio from: {youtube_url}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    raise Exception(f"yt-dlp failed to extract audio. Error: {result.stderr}")

                if not os.path.exists(audio_path):
                    raise FileNotFoundError("Audio file was not created by yt-dlp.")
                
                logger.info(f"Audio extracted. Transcribing with Whisper API...")

                with open(audio_path, "rb") as audio_file:
                    transcription = self.openai_client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file,
                        response_format="json" # Meminta format respons yang konsisten
                    )
                
                transcript_text = transcription.text
                if not transcript_text:
                    raise Exception("Whisper API returned an empty transcript.")
                
                logger.info("Whisper API transcription successful.")
                return transcript_text.strip()

        # --- Blok Penanganan Error API Sesuai Dokumentasi OpenAI ---
        except RateLimitError as e:
            logger.error(f"OpenAI API rate limit or quota exceeded: {e}")
            raise Exception("You have exceeded your OpenAI API quota. Please check your plan and billing details on the OpenAI website.")
        except APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise Exception("Could not connect to the OpenAI API. Please check your network connection.")
        except APIStatusError as e:
            logger.error(f"OpenAI API returned an error status: {e}")
            raise Exception(f"OpenAI API returned an error: {e.status_code} - {e.response}")
        # -------------------------------------------------------------
        except subprocess.TimeoutExpired:
            logger.error("The audio extraction process with yt-dlp timed out.")
            raise Exception("Audio extraction timed out. The video might be too long.")
        except Exception as e:
            logger.error(f"An error occurred during audio extraction or transcription: {str(e)}", exc_info=True)
            raise