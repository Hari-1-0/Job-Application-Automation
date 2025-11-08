from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from backend.ml_models.advanced_resume_parser import AdvancedResumeParser
from backend.ml_models.ml_trained_chatbot import MLChatbot
from backend.ml_models.ai_autofill import AIAutoFill
from backend.scrapers.real_job_scraper import RealJobScraper
from backend.core.logging_config import setup_logging
from backend.core.config import settings

load_dotenv()
logger = setup_logging(__name__)

app = FastAPI(title="JobMatch AI - Production", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_parser = AdvancedResumeParser()
chatbot = MLChatbot()
autofill = AIAutoFill()
scraper = RealJobScraper()

# Mount static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

@app.get("/")
async def root():
    return {"message": "JobMatch AI - Production v3.0", "status": "running", "features": ["Real jobs", "ML chatbot", "AI autofill"]}

@app.get("/production.html")
async def production_page():
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    index_file = frontend_path / "production.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    return {"error": "production.html not found"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume and extract all information"""
    try:
        logger.info(f"Parsing resume: {file.filename}")
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        
        parsed_data = resume_parser.parse_resume(text)
        
        logger.info(f"Resume parsed - Found {len(parsed_data['skills'])} skills")
        
        return {"success": True, "parsed_data": parsed_data}
        
    except Exception as e:
        logger.error(f"Resume parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/jobs/search-by-title-city")
async def search_jobs(job_title: str, city: str):
    """Search for REAL jobs from multiple websites"""
    try:
        logger.info(f"Searching real jobs: {job_title} in {city}")
        
        # Use async scraper to get real jobs
        jobs = await scraper.scrape_all_sources(job_title, city)
        
        logger.info(f"Found {len(jobs)} unique jobs from real sources")
        
        return {
            "success": True,
            "jobs": jobs,
            "count": len(jobs),
            "sources": ["Indeed", "LinkedIn", "Naukri", "Glassdoor"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Job search error: {str(e)}")
        # Return mock jobs if scraping fails
        return {
            "success": True,
            "jobs": [],
            "count": 0,
            "error": "Real job sources temporarily unavailable"
        }

@app.post("/api/v1/chatbot/chat")
async def chat(user_message: str):
    """ML-trained chatbot with dataset"""
    try:
        logger.info(f"Chatbot: {user_message[:50]}")
        
        intent_data = chatbot.predict_intent(user_message)
        intent = intent_data.get("intent", "general")
        confidence = intent_data.get("confidence", 0.0)
        
        response = chatbot.generate_response(intent)
        
        return {
            "success": True,
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/jobs/autofill")
async def autofill_application(resume_data: dict, job_data: dict):
    """AI auto-fill job application"""
    try:
        logger.info(f"Auto-filling application for: {job_data.get('title')}")
        
        filled_application = autofill.auto_fill_application(resume_data, job_data)
        
        return {
            "success": True,
            "filled_application": filled_application,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auto-fill error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, workers=1, reload=True)
