from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional
from datetime import datetime

class AnalyzeRequest(BaseModel):
    """Request model for content analysis."""
    youtube_url: HttpUrl = Field(..., description="YouTube video URL to analyze")

class VideoMetadata(BaseModel):
    """Video metadata information."""
    title: str = Field(..., description="Video title")
    duration: int = Field(..., description="Video duration in seconds")
    thumbnail_url: str = Field(..., description="Video thumbnail URL")
    channel_name: str = Field(..., description="Channel name")
    view_count: Optional[int] = Field(None, description="Number of views")
    like_count: Optional[int] = Field(None, description="Number of likes")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    description: Optional[str] = Field(None, description="Video description")

class TimelineItem(BaseModel):
    """Timeline summary item."""
    timestamp: str = Field(..., description="Time range (e.g., '00:00 - 01:00')")
    summary: str = Field(..., description="Summary for this time segment")

class ViralAnalysis(BaseModel):
    """Viral potential analysis results."""
    score: int = Field(..., ge=0, le=100, description="Viral score from 0-100")
    label: str = Field(..., description="Viral potential label")
    explanation: str = Field(..., description="Explanation of viral potential")

class ContentRecommendation(BaseModel):
    """Content recommendation based on analysis."""
    title: str = Field(..., description="Recommended content title")
    target_audience: str = Field(..., description="Target audience description")
    content_style: str = Field(..., description="Recommended content style")
    suggested_structure: Dict[str, str] = Field(..., description="Suggested content structure")
    pro_tips: List[str] = Field(..., description="Pro tips for maximum engagement")
    estimated_viral_score: int = Field(..., ge=0, le=100, description="Estimated viral score")

class AnalyzeResponse(BaseModel):
    """Response model for content analysis."""
    video_metadata: VideoMetadata = Field(..., description="Video metadata")
    summary: str = Field(..., description="Overall content summary")
    timeline_summary: List[TimelineItem] = Field(..., description="Timeline-based summary")
    viral_score: int = Field(..., ge=0, le=100, description="Viral potential score")
    viral_label: str = Field(..., description="Viral potential label")
    viral_explanation: str = Field(..., description="Explanation of viral potential")
    recommendations: ContentRecommendation = Field(..., description="Content recommendations")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")