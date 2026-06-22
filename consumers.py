import os
import json
import logging
from datetime import datetime
import redis
from plyer import notification
from sqlalchemy.orm import Session

# Load env since this is a separate script
from dotenv import load_dotenv
load_dotenv()

from database import engine
from models import Incident, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consumers")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# 1. Initialize Redis
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


def process_storage(data):
    """Storage Service: Saves the incident to PostgreSQL"""
    try:
        with Session(engine) as session:
            created_at = None
            if data.get("created_at"):
                created_at = datetime.fromisoformat(data["created_at"])
                
            incident = Incident(
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                incident_type=data.get("incident_type"),
                severity=data.get("severity"),
                severity_score=data.get("severity_score"),
                raw_response=data.get("raw_response"),
                created_at=created_at or datetime.utcnow()
            )
            session.add(incident)
            session.commit()
            logger.info("Storage Service: Saved incident to PostgreSQL")
    except Exception as e:
        logger.error(f"Storage Service Error: {e}")

def process_redis(data):
    """Redis Cache Service: Stores the latest incidents in Redis for quick retrieval (expires in 24 hours)"""
    if not redis_client:
        return
        
    try:
        # We use a Redis Sorted Set (ZSET) to store recent incidents.
        # The score is the timestamp, allowing us to query by time windows and purge old items easily.
        timestamp = datetime.utcnow().timestamp()
        if data.get("created_at"):
            try:
                timestamp = datetime.fromisoformat(data["created_at"]).timestamp()
            except Exception:
                pass
                
        # Add to the sorted set
        redis_client.zadd("recent_incidents_zset", {json.dumps(data): timestamp})
        
        # Keep only the latest 100 to avoid unbounded memory usage
        redis_client.zremrangebyrank("recent_incidents_zset", 0, -101)
        
        # Purge items older than 24 hours (86400 seconds)
        one_day_ago = datetime.utcnow().timestamp() - 86400
        redis_client.zremrangebyscore("recent_incidents_zset", "-inf", one_day_ago)
        
        logger.info("Redis Cache Service: Saved and pruned recent incidents in ZSET")
    except Exception as e:
        logger.error(f"Redis Cache Service Error: {e}")

def process_notification(data):
    """Notification Service: Sends a local desktop notification for high severity incidents"""
    severity = data.get("severity", "low")
    if severity in ("high", "critical"):
        try:
            incident_type = data.get("incident_type", "Unknown Incident").replace("_", " ").title()
            
            notification.notify(
                title="🚨 EMERGENCY ALERT 🚨",
                message=f"A {severity} severity {incident_type} has been reported nearby!",
                app_name="Incident Backend",
                timeout=10
            )
            logger.info("Notification Service: Displayed local desktop alert successfully")
        except Exception as e:
            logger.error(f"Notification Service Error: {e}")


