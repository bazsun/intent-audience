"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter, status
from typing import Dict, Any
import logging

from ...utils.database.postgres_client import postgres_client
from ...utils.database.mongo_client import mongo_client
from ...utils.database.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check system health and component status."""
    start_time = datetime.utcnow()
    
    # Check database connections
    postgres_healthy = await postgres_client.health_check()
    mongo_healthy = await mongo_client.health_check()
    redis_healthy = await redis_client.health_check()
    
    # Determine overall health
    all_healthy = all([postgres_healthy, mongo_healthy, redis_healthy])
    
    # Calculate response time
    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    health_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": start_time.isoformat(),
        "components": {
            "database": "up" if postgres_healthy else "down",
            "document_store": "up" if mongo_healthy else "down", 
            "cache": "up" if redis_healthy else "down",
            "ml_models": "up"  # Placeholder - will check actual models later
        },
        "response_time_ms": int(response_time)
    }
    
    # Return appropriate status code
    if all_healthy:
        return health_data
    else:
        from fastapi import Response
        return Response(
            content=health_data,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )