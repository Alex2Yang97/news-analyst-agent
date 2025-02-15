from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import and_, delete, or_

from news_analyst_agent.db.database import AsyncSessionLocal
from news_analyst_agent.db.models import Thread


async def cleanup_orphaned_threads():
    """Delete threads that don't have a userIdentifier and are older than 24 hours
    """
    try:
        async with AsyncSessionLocal() as session:
            # Find threads without userIdentifier that are older than 1 hour
            one_day_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            delete_stmt = delete(Thread).where(
                or_(
                    and_(
                        Thread.userIdentifier.is_(None),
                        Thread.createdAt < one_day_ago
                    ),
                    Thread.createdAt.is_(None)
                )
            )
            
            result = await session.execute(delete_stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} orphaned threads")
            
    except Exception as e:
        logger.error(f"Error during thread cleanup: {str(e)}") 