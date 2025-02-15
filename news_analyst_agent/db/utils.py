from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_db_connection(session: AsyncSession) -> bool:
    """Check if database connection is working"""
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False 