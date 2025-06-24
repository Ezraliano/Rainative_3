from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.transcriber import TranscriberService
from services.summarizer import SummarizerService
from services.viral import ViralAnalysisService
from services.recommender import RecommenderService
from utils.youtube import YouTubeUtils
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
transcriber_service = TranscriberService()
summarizer_service = SummarizerService()
viral_service = ViralAnalysisService()
recommender_service = RecommenderService()
youtube_utils = YouTubeUtils()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze YouTube video content for viral potential and generate recommendations.
    """
    try:
        logger.info(f"Analyzing content: {request.youtube_url}")
        
        # Step 1: Extract YouTube metadata
        video_metadata = await youtube_utils.get_video_metadata(request.youtube_url)
        if not video_metadata:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL or video not accessible")
        
        # Step 2: Get transcript (mock for now)
        transcript = await transcriber_service.get_transcript(request.youtube_url)
        
        # Step 3: Generate timeline summary
        timeline_summary = await summarizer_service.generate_timeline_summary(transcript, video_metadata.duration)
        
        # Step 4: Generate overall summary
        overall_summary = await summarizer_service.generate_summary(transcript)
        
        # Step 5: Calculate viral score and explanation
        viral_analysis = await viral_service.analyze_viral_potential(
            transcript, video_metadata, timeline_summary
        )
        
        # Step 6: Generate content recommendations
        recommendations = await recommender_service.generate_recommendations(
            transcript, video_metadata, viral_analysis
        )
        
        # Construct response
        response = AnalyzeResponse(
            video_metadata=video_metadata,
            summary=overall_summary,
            timeline_summary=timeline_summary,
            viral_score=viral_analysis.score,
            viral_label=viral_analysis.label,
            viral_explanation=viral_analysis.explanation,
            recommendations=recommendations
        )
        
        logger.info(f"Analysis completed for: {request.youtube_url}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """
    Get the status of a long-running analysis task.
    """
    # TODO: Implement task status tracking with Redis or database
    return {"task_id": task_id, "status": "completed", "progress": 100}