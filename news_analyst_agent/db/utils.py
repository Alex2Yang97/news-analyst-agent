from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def check_db_connection(session: AsyncSession) -> bool:
    """Check if database connection is working"""
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False 