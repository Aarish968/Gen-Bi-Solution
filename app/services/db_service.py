from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from app.core.config import settings


class DBService:
    """
    Database service — creates a fresh engine per instance.

    Why NullPool:
      - Default connection pool holds connections across event loops
      - Celery creates a new event loop per task via asyncio.run()
      - NullPool disables pooling — each query opens/closes its own connection
      - This prevents "another operation is in progress" errors in Celery workers

    Why fresh engine per instance:
      - Module-level engine shares state across event loops → conflict
      - Per-instance engine is created inside the correct event loop → safe
    """

    def __init__(self):
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,   # no connection pooling — safe for Celery
            echo=False,
        )
        self.AsyncSessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def execute(self, sql: str) -> list:
        async with self.AsyncSessionLocal() as session:
            result = await session.execute(text(sql))
            rows = result.fetchall()
            keys = result.keys()
            return [dict(zip(keys, row)) for row in rows]
