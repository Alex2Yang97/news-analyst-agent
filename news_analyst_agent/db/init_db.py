import asyncio
from news_analyst_agent.db.database import sync_engine
from news_analyst_agent.db.models import Base
from news_analyst_agent.config import get_settings

def init_db():
    """Initialize the database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("Database tables created successfully!")

def drop_db():
    """Drop all database tables"""
    print("Dropping database tables...")
    Base.metadata.drop_all(bind=sync_engine)
    print("Database tables dropped successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_db()
    init_db()