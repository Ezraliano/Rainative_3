import os
import logging
from typing import Dict, List
import google.generativeai as genai
from models.schemas import ContentRecommendation
import json

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.error("GEMINI_API_KEY not found. GeminiService cannot function.")
            self.model = None

    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini API."""
        if not self.model:
            raise Exception("Gemini model is not initialized. Check API key.")
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Failed to generate content from Gemini: {str(e)}")


gemini_service = GeminiService()

async def summarize_transcript(transcript_chunk: str) -> str:
    """
    Summarize a transcript chunk using Gemini AI.
    """
    prompt = f"""
    Please provide a concise summary of the following content in 2-3 sentences, 
    focusing on the key points and main insights:
    
    "{transcript_chunk}"
    
    Summary:
    """
    summary = await gemini_service._generate_content(prompt)
    return summary.strip()

async def explain_why_viral(title: str, views: int, likes: int, summary: str) -> str:
    """
    Generate explanation for why content has viral potential.
    """
    prompt = f"""
    Analyze why this content has viral potential based on the following information:
    
    Title: {title}
    Summary: {summary}
    
    Provide a detailed explanation (3-4 sentences) covering:
    1. What makes this content engaging
    2. Why it resonates with audiences
    3. Key viral factors (e.g., topic, presentation style, value)
    
    Explanation:
    """
    explanation = await gemini_service._generate_content(prompt)
    return explanation.strip()

async def generate_content_idea(category: str, summary: str, reason: str) -> ContentRecommendation:
    """
    Generate content recommendation based on analysis by requesting a JSON object.
    """
    prompt = f"""
    Based on this successful content analysis, generate a new content idea:
    
    Category: {category}
    Original Summary: {summary}
    Viral Factors: {reason}
    
    Please provide a response in a valid JSON format only. The JSON object should have the following keys:
    - "title": A compelling title for the new content (string).
    - "target_audience": A description of the target audience (string).
    - "content_style": The recommended content style (string).
    - "suggested_structure": An object with keys "hook", "introduction", "main_content", and "call_to_action" (object of strings).
    - "pro_tips": A list of 4-5 pro tips for maximum engagement (list of strings).
    - "estimated_viral_score": An estimated viral score between 0 and 100 (integer).

    Example JSON structure:
    {{
        "title": "Example Title",
        "target_audience": "Example Audience",
        "content_style": "Example Style",
        "suggested_structure": {{
            "hook": "Example Hook",
            "introduction": "Example Introduction",
            "main_content": "Example Main Content",
            "call_to_action": "Example CTA"
        }},
        "pro_tips": ["Tip 1", "Tip 2", "Tip 3", "Tip 4"],
        "estimated_viral_score": 85
    }}

    JSON response:
    """
    try:
        response_text = await gemini_service._generate_content(prompt)
        # Membersihkan response untuk memastikan hanya JSON yang tersisa
        clean_json_text = response_text.strip().replace('```json', '').replace('```', '').strip()
        
        # Parsing teks JSON menjadi dictionary Python
        data = json.loads(clean_json_text)
        
        # Membuat objek ContentRecommendation dari dictionary
        recommendation = ContentRecommendation(**data)
        return recommendation
        
    except Exception as e:
        logger.error(f"Error generating or parsing content idea: {str(e)}")
        # Fallback jika terjadi error
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
            ],
            estimated_viral_score=75
        )

async def summarize_document(file_path: str) -> str:
    """
    Summarize document content.
    """
    # TODO: Implement actual document reading and processing
    logger.info(f"Summarizing document: {file_path}")
    
    mock_summary = f"""
    This document contains comprehensive information. Key themes include strategic planning, 
    implementation guidelines, and best practices.
    """
    
    return await summarize_transcript(mock_summary)