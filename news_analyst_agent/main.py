from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from news_analyst_agent.api import chat_agent, health, retrieve_db
from news_analyst_agent.tasks.cleanup import cleanup_orphaned_threads

# Initialize scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    try:
        # Startup: Schedule and start the cleanup task
        scheduler.add_job(
            cleanup_orphaned_threads,
            'interval',
            hours=1,
            next_run_time=datetime.now(),
            id='cleanup_orphaned_threads'
        )
        scheduler.start()
        logger.info("Started background cleanup task scheduler")
        yield
    finally:
        # Shutdown: Clean up resources
        scheduler.shutdown()
        logger.info("Shut down cleanup task scheduler")

app = FastAPI(title="News Analyst API", lifespan=lifespan)

# Include the API router
app.include_router(health.router, prefix="/api")
app.include_router(retrieve_db.router, prefix="/api")
app.include_router(chat_agent.router, prefix="/api") 