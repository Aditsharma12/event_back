from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, JSON, DateTime, text
from database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    incident_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    severity_score = Column(Integer, nullable=True)

    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
