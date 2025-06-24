import os
import logging
from typing import Dict, List
import google.generativeai as genai
from models.schemas import ContentRecommendation

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("GEMINI_API_KEY not found. Using mock responses.")
            self.model = None

    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini API or return mock data."""
        if self.model and self.api_key:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini API error: {str(e)}")
                return self._get_mock_response(prompt)
        else:
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Return mock responses based on prompt type."""
        if "summarize" in prompt.lower():
            return "This content provides valuable insights into the topic, covering key concepts and practical applications that would be useful for the target audience."
        elif "viral" in prompt.lower():
            return "This content has strong viral potential due to its engaging presentation, timely topic, and clear value proposition for viewers."
        elif "content idea" in prompt.lower():
            return "Create engaging tutorial content that provides step-by-step guidance while maintaining viewer interest through clear explanations and practical examples."
        else:
            return "AI-generated response based on the provided content analysis."

# Initialize service instance
gemini_service = GeminiService()

async def summarize_transcript(transcript_chunk: str) -> str:
    """
    Summarize a transcript chunk using Gemini AI.
    
    Args:
        transcript_chunk: Text chunk to summarize
        
    Returns:
        Summary string
    """
    try:
        prompt = f"""
        Please provide a concise summary of the following content in 2-3 sentences, 
        focusing on the key points and main insights:
        
        {transcript_chunk}
        
        Summary:
        """
        
        summary = await gemini_service._generate_content(prompt)
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Error summarizing transcript: {str(e)}")
        return "Unable to generate summary at this time."

async def explain_why_viral(title: str, views: int, likes: int, summary: str) -> str:
    """
    Generate explanation for why content has viral potential.
    
    Args:
        title: Content title
        views: View count
        likes: Like count  
        summary: Content summary
        
    Returns:
        Explanation string
    """
    try:
        prompt = f"""
        Analyze why this content has viral potential based on the following information:
        
        Title: {title}
        Views: {views:,} 
        Likes: {likes:,}
        Summary: {summary}
        
        Provide a detailed explanation (3-4 sentences) covering:
        1. What makes this content engaging
        2. Why it resonates with audiences
        3. Key viral factors (timing, topic, presentation style)
        
        Explanation:
        """
        
        explanation = await gemini_service._generate_content(prompt)
        return explanation.strip()
        
    except Exception as e:
        logger.error(f"Error generating viral explanation: {str(e)}")
        return "This content demonstrates strong viral potential through its engaging presentation and valuable insights that resonate with the target audience."

async def generate_content_idea(category: str, summary: str, reason: str) -> ContentRecommendation:
    """
    Generate content recommendation based on analysis.
    
    Args:
        category: Content category
        summary: Original content summary
        reason: Why original content is viral
        
    Returns:
        ContentRecommendation object
    """
    try:
        prompt = f"""
        Based on this successful content analysis, generate a new content idea:
        
        Category: {category}
        Original Summary: {summary}
        Viral Factors: {reason}
        
        Please provide:
        1. A compelling title for new content
        2. Target audience description
        3. Content style recommendation
        4. Structure breakdown (hook, introduction, main content, call to action)
        5. 4-5 pro tips for maximum engagement
        6. Estimated viral score (0-100)
        
        Format your response as structured data.
        """
        
        # For now, return structured mock data
        # TODO: Parse Gemini response into structured format
        
        recommendation = ContentRecommendation(
            title="Master This Trending Skill in 10 Minutes - Complete Beginner's Guide",
            target_audience="Young professionals, students, and career changers aged 22-35 looking to upskill quickly",
            content_style="Fast-paced tutorial with screen recording, energetic music, and quick visual transitions",
            suggested_structure={
                "hook": "Show the end result first - what viewers will achieve in 10 minutes",
                "introduction": "Brief explanation of why this skill is trending and valuable",
                "main_content": "Step-by-step tutorial broken into digestible 2-minute segments",
                "call_to_action": "Challenge viewers to try it and share their results in comments"
            },
            pro_tips=[
                "Use trending hashtags related to skill development and career growth",
                "Post during peak engagement hours (7-9 PM in target timezone)",
                "Create eye-catching thumbnail with before/after comparison",
                "Respond to comments within the first 2 hours to boost engagement",
                "Include downloadable resources or templates in description"
            ],
            estimated_viral_score=88
        )
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error generating content idea: {str(e)}")
        # Return fallback recommendation
        return ContentRecommendation(
            title="Create Engaging Content That Gets Results",
            target_audience="Content creators and marketers",
            content_style="Educational with practical examples",
            suggested_structure={
                "hook": "Start with a compelling question or statistic",
                "introduction": "Introduce the problem you're solving",
                "main_content": "Provide step-by-step solutions",
                "call_to_action": "Encourage engagement and sharing"
            },
            pro_tips=[
                "Focus on providing genuine value to your audience",
                "Use clear, concise language that's easy to understand",
                "Include visual elements to maintain interest",
                "Optimize for your platform's algorithm"
            ],
            estimated_viral_score=75
        )

async def summarize_document(file_path: str) -> str:
    """
    Summarize document content.
    
    Args:
        file_path: Path to document file
        
    Returns:
        Document summary
    """
    try:
        # TODO: Implement actual document reading and processing
        # This would involve:
        # 1. Reading file content based on type (PDF, Word, etc.)
        # 2. Extracting text
        # 3. Summarizing with Gemini
        
        logger.info(f"Summarizing document: {file_path}")
        
        # Mock document summary for now
        mock_summary = f"""
        Document analysis for {file_path}:
        
        This document contains comprehensive information covering multiple key topics and insights. 
        The content is well-structured and provides valuable information that could be adapted 
        for various content formats. Key themes include strategic planning, implementation 
        guidelines, and best practices that would resonate with professional audiences.
        """
        
        return mock_summary.strip()
        
    except Exception as e:
        logger.error(f"Error summarizing document: {str(e)}")
        return f"Unable to process document: {file_path}"