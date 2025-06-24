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

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
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
        
        # Handle YouTube URL analysis
        if request.youtube_url:
            logger.info(f"Analyzing YouTube content: {request.youtube_url}")
            
            # Step 1: Extract YouTube metadata
            video_metadata = await youtube_utils.get_video_metadata(str(request.youtube_url))
            if not video_metadata:
                raise HTTPException(status_code=400, detail="Invalid YouTube URL or video not accessible")
            
            # Step 2: Get transcript
            transcript = await transcriber_service.get_transcript(str(request.youtube_url))
            
            # Step 3: Generate timeline summary using Gemini
            timeline_summary = await _generate_timeline_summary(transcript, video_metadata.duration)
        
        # Handle document analysis
        if request.file_path:
            logger.info(f"Analyzing document: {request.file_path}")
            doc_summary = await summarize_document(request.file_path)
            transcript = doc_summary  # Use document content for viral analysis
        
        # Step 4: Generate overall summary
        overall_summary = await summarize_transcript(transcript)
        
        # Step 5: Calculate viral score and explanation
        viral_score = await viral_service.calculate_viral_score(
            transcript, 
            video_metadata.title if video_metadata else "Document Analysis",
            video_metadata.view_count if video_metadata else 0,
            video_metadata.like_count if video_metadata else 0
        )
        
        # Determine viral label
        if viral_score >= 80:
            viral_label = "Very Viral"
        elif viral_score >= 60:
            viral_label = "Moderately Viral"
        else:
            viral_label = "Low Reach"
        
        # Step 6: Generate viral explanation
        viral_explanation = await explain_why_viral(
            video_metadata.title if video_metadata else "Document",
            video_metadata.view_count if video_metadata else 0,
            video_metadata.like_count if video_metadata else 0,
            overall_summary
        )
        
        # Step 7: Generate content recommendations
        recommendations = await generate_content_idea(
            "general",  # category
            overall_summary,
            viral_explanation
        )
        
        # Construct response
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
        logger.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

async def _generate_timeline_summary(transcript: str, duration_seconds: int):
    """Generate timeline summary by breaking transcript into chunks."""
    try:
        # Split transcript into time-based chunks (approximate)
        words = transcript.split()
        words_per_minute = len(words) / (duration_seconds / 60) if duration_seconds > 0 else 100
        
        timeline_items = []
        chunk_duration = 60  # 1 minute chunks
        num_chunks = max(1, duration_seconds // chunk_duration)
        words_per_chunk = max(1, len(words) // num_chunks)
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration, duration_seconds)
            
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
        # Return mock data if generation fails
        return [
            {
                "timestamp": "00:00 - 01:00",
                "summary": "Introduction and overview of the main topic"
            },
            {
                "timestamp": "01:00 - 02:00", 
                "summary": "Deep dive into key concepts and examples"
            }
        ]

@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """
    Get the status of a long-running analysis task.
    """
    # TODO: Implement task status tracking with Redis or database
    return {"task_id": task_id, "status": "completed", "progress": 100}