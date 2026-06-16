from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os
import json
import logging

import redis

from database import engine, Base, get_db
from models import Incident
from hf_client import analyze_image
from consumers import process_storage, process_redis, process_notification

# Initialize Redis (for /incidents caching)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables in the database if they don't exist
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Incident Reporting Backend",
    description="FastAPI Backend for storing and analyzing emergency incidents reported from a Flutter app.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Flutter app integration (running on local emulator, web, or device)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Welcome to the Incident Reporting Backend API. Go to /docs for interactive API documentation.",
        "status": "online"
    }

@app.get("/health", tags=["General"])
def health_check(db: Session = Depends(get_db)):
    try:
        # Verify database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    return {
        "status": "healthy",
        "database": db_status
    }

@app.post("/report", tags=["Incidents"])
async def report_incident(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receives incident details from Flutter client:
    - image: Multipart image file
    - latitude: Location latitude from GPS
    - longitude: Location longitude from GPS
    
    Processes the image using Grounding DINO on Hugging Face and saves the result in Neon Postgres.
    """
    try:
        # Process image via Hugging Face Space API
        result = analyze_image(image)
        
        # Dispatch events to the internal FastAPI bus (Background Tasks)
        incident_data = {
            "latitude": latitude,
            "longitude": longitude,
            "incident_type": result.get("incident_type"),
            "severity": result.get("severity"),
            "severity_score": result.get("severity_score"),
            "raw_response": result,
            "created_at": datetime.utcnow().isoformat()
        }
        
        background_tasks.add_task(process_storage, incident_data)
        background_tasks.add_task(process_redis, incident_data)
        background_tasks.add_task(process_notification, incident_data)
            
        return {
            "success": True,
            "message": "Incident report received and queued for processing.",
            "location": {
                "lat": latitude,
                "lng": longitude
            },
            "analysis": result,
            "queued": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while reporting the incident: {str(e)}"
        )

@app.get("/incidents", tags=["Incidents"])
def get_incidents(db: Session = Depends(get_db)):
    """
    Retrieves all reported incidents from Redis cache. Falls back to database.
    """
    try:
        # Try fetching from Redis first
        if redis_client:
            cached_incidents = redis_client.lrange("recent_incidents", 0, -1)
            if cached_incidents:
                return {
                    "success": True,
                    "count": len(cached_incidents),
                    "incidents": [json.loads(i) for i in cached_incidents],
                    "source": "redis_cache"
                }
    except Exception as e:
        print(f"Redis cache error: {e}")
        
    # Fallback to DB
    try:
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
        return {
            "success": True,
            "count": len(incidents),
            "incidents": incidents,
            "source": "database"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch incidents: {str(e)}"
        )
