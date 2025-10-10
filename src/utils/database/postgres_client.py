"""PostgreSQL database client and connection management."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import asyncpg
from asyncpg import Pool, Connection
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """PostgreSQL connection manager with connection pooling."""
    
    def __init__(self):
        self._pool: Optional[Pool] = None
        self._connection_url = settings.database_url
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is not None:
            logger.warning("PostgreSQL pool already initialized")
            return
            
        try:
            self._pool = await asyncpg.create_pool(
                self._connection_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def execute_sql(self, query: str, *args) -> str:
        """Execute a SQL command and return status."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[dict]:
        """Fetch a single row as dictionary."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> list[dict]:
        """Fetch all rows as list of dictionaries."""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.get_connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False


# Global client instance
postgres_client = PostgresClient()