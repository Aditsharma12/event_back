import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set in .env")

# For Neon Postgres, we ensure sslmode=require is in the URL.
# If it's missing, let's make sure we warn or append it, but it's already in the user's string.
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# FastAPI dependency to handle DB sessions safely (auto-closes connection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
