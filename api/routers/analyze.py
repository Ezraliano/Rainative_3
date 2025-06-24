from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.gemini_utils import (
    summarize_transcript,
    explain_why_viral,
    generate_content_idea,
    summarize_document
)
from services.transcriber import TranscriberService
from services.viral import ViralAnalysisService
from utils.youtube import YouTubeUtils
import logging

# Impor exception dari pustaka transkrip untuk penanganan error yang lebih baik
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

router = APIRouter()
logger = logging.getLogger(__name__)

# Inisialisasi service
transcriber_service = TranscriberService()
viral_service = ViralAnalysisService()
youtube_utils = YouTubeUtils()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze YouTube video content or document for viral potential and generate recommendations.
    """
    try:
        if not request.youtube_url and not request.file_path:
            raise HTTPException(status_code=400, detail="Either youtube_url or file_path must be provided")

        video_metadata = None
        timeline_summary = None
        doc_summary = None
        transcript = ""

        if request.youtube_url:
            logger.info(f"Analyzing YouTube content: {request.youtube_url}")

            video_metadata = await youtube_utils.get_video_metadata(str(request.youtube_url))
            if not video_metadata:
                raise HTTPException(status_code=404, detail="Invalid YouTube URL or video metadata not accessible.")

            # --- BLOK PENTING UNTUK MENANGANI ERROR TRANSKRIP ---
            try:
                transcript = await transcriber_service.get_transcript(str(request.youtube_url))
            except (NoTranscriptFound, TranscriptsDisabled) as e:
                logger.warning(f"Transcript not available for {request.youtube_url}: {e}")
                raise HTTPException(
                    status_code=404,
                    detail="Sorry, a transcript is not available for this video. Please try another one."
                )
            # --- AKHIR BLOK PENTING ---

            timeline_summary = await _generate_timeline_summary(transcript, video_metadata.duration)

        if request.file_path:
            logger.info(f"Analyzing document: {request.file_path}")
            doc_summary = await summarize_document(request.file_path)
            transcript = doc_summary

        overall_summary = await summarize_transcript(transcript)

        title_for_analysis = video_metadata.title if video_metadata else "Document Analysis"
        views_for_analysis = video_metadata.view_count if video_metadata else 0
        likes_for_analysis = video_metadata.like_count if video_metadata else 0

        viral_score = await viral_service.calculate_viral_score(
            transcript,
            title_for_analysis,
            views_for_analysis,
            likes_for_analysis
        )

        if viral_score >= 80:
            viral_label = "Very Viral"
        elif viral_score >= 60:
            viral_label = "Moderately Viral"
        else:
            viral_label = "Low Reach"

        viral_explanation = await explain_why_viral(
            title_for_analysis,
            views_for_analysis,
            likes_for_analysis,
            overall_summary
        )

        recommendations = await generate_content_idea(
            "general",
            overall_summary,
            viral_explanation
        )

        response = AnalyzeResponse(
            video_metadata=video_metadata,
            summary=overall_summary,
            timeline_summary=timeline_summary,
            viral_score=viral_score,
            viral_label=viral_label,
            viral_explanation=viral_explanation,
            recommendations=recommendations,
            doc_summary=doc_summary
        )

        logger.info(f"Analysis completed successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


async def _generate_timeline_summary(transcript: str, duration_seconds: int):
    """Generate timeline summary by breaking transcript into chunks."""
    try:
        words = transcript.split()
        if not words:
            return []

        num_chunks = max(1, -(-duration_seconds // 60))
        words_per_chunk = max(1, len(words) // num_chunks)

        timeline_items = []
        for i in range(num_chunks):
            start_time = i * 60
            end_time = min((i + 1) * 60, duration_seconds)
            start_word = i * words_per_chunk
            end_word = min((i + 1) * words_per_chunk, len(words))
            chunk_text = " ".join(words[start_word:end_word])

            if chunk_text.strip():
                chunk_summary = await summarize_transcript(chunk_text)
                timeline_items.append({
                    "timestamp": f"{start_time//60:02d}:{start_time%60:02d} - {end_time//60:02d}:{end_time%60:02d}",
                    "summary": chunk_summary
                })

        return timeline_items

    except Exception as e:
        logger.error(f"Error generating timeline summary: {str(e)}")
        return []

@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """
    Get the status of a long-running analysis task.
    """
    return {"task_id": task_id, "status": "completed", "progress": 100}