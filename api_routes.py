# api_routes.py
from fastapi import APIRouter, File, UploadFile, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
from datetime import datetime
from pathlib import Path
import logging
from real_job_scraper import RealJobScraper
from job_matcher import JobMatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["jobs"])

scraper = RealJobScraper()

@router.post("/search-realtime")
async def search_jobs_realtime(
    job_title: str = Query(...),
    location: str = Query(...),
    resume_data: dict = None
):
    """Real-time search from 20+ websites"""
    try:
        logger.info(f"Real-time search: {job_title} in {location}")
        
        # Scrape jobs from all sources
        jobs = await scraper.scrape_all_sources(job_title, location)
        
        # Calculate match if resume provided
        if resume_data:
            matcher = JobMatcher(resume_data)
            for job in jobs:
                job['match_percentage'] = matcher.calculate_match_percentage(job)
            
            # Sort by match percentage
            jobs = sorted(jobs, key=lambda x: x['match_percentage'], reverse=True)
        
        return {
            "success": True,
            "jobs": jobs,
            "total": len(jobs),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "jobs": []
        }

@router.get("/job-details/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed job information"""
    # This would fetch from stored jobs or scrape specific job page
    return {"job_id": job_id, "details": "Job details here"}

@router.post("/apply-job")
async def apply_to_job(job_url: str, resume_data: dict):
    """Track job application"""
    return {
        "success": True,
        "message": "Job link ready to open",
        "job_url": job_url
    }
