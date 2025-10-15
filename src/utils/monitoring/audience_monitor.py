"""
Audience Monitoring Service (T029)

Purpose: Track audience generation performance
- Integrates with existing logging framework (T014)
- Records execution times
- Tracks success/failure rates
- Monitors audience quality metrics
- Alerts on performance degradation

Dependencies: T014 (error handling and logging framework)
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID
from contextlib import asynccontextmanager

from src.utils.database.mongo_client import mongo_client
from src.utils.database.redis_client import redis_client

logger = logging.getLogger(__name__)


class AudienceMonitor:
    """
    Service for monitoring and tracking audience generation performance.

    Provides:
    - Execution time tracking
    - Success/failure rate monitoring
    - Quality metric aggregation
    - Performance alerting
    - Historical trend analysis
    """

    def __init__(self):
        self.metrics_collection = "audience_metrics"
        self.performance_threshold_seconds = 300.0  # 5 minutes per spec
        self.alert_threshold_failure_rate = 0.1  # Alert if >10% failures

    @asynccontextmanager
    async def track_generation(
        self,
        category: str,
        audience_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking audience generation operations.

        Usage:
            async with monitor.track_generation("Electronics", audience_id) as tracker:
                # ... perform audience generation ...
                tracker.record_metric("customers_processed", 50000)

        TODO:
        - Record start time
        - Yield tracker object
        - Calculate duration on exit
        - Record metrics to MongoDB
        - Cache recent metrics in Redis
        - Trigger alerts if needed
        """
        start_time = time.time()
        tracker = GenerationTracker(category, audience_id, metadata or {})

        try:
            logger.info(f"Starting audience generation tracking for category: {category}")
            yield tracker

            # Calculate duration
            duration = time.time() - start_time
            tracker.set_duration(duration)
            tracker.set_status("success")

            # Check performance threshold
            if duration > self.performance_threshold_seconds:
                logger.warning(
                    f"Audience generation exceeded performance threshold: "
                    f"{duration:.2f}s > {self.performance_threshold_seconds}s"
                )
                await self._trigger_performance_alert(category, duration)

            logger.info(
                f"Audience generation completed successfully in {duration:.2f}s "
                f"(audience_id: {audience_id})"
            )

        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            tracker.set_duration(duration)
            tracker.set_status("failed")
            tracker.set_error(str(e))

            logger.error(
                f"Audience generation failed after {duration:.2f}s: {e}",
                exc_info=True
            )

            await self._trigger_failure_alert(category, str(e))
            raise

        finally:
            # Save metrics
            await self._save_metrics(tracker)
            await self._update_aggregates(category, tracker)

    async def _save_metrics(self, tracker: "GenerationTracker") -> None:
        """
        Save generation metrics to MongoDB.

        TODO: Implement MongoDB insert for metrics collection
        """
        try:
            db = mongo_client.get_database()
            metrics_doc = {
                "category": tracker.category,
                "audience_id": str(tracker.audience_id) if tracker.audience_id else None,
                "timestamp": datetime.utcnow(),
                "duration_seconds": tracker.duration,
                "status": tracker.status,
                "error_message": tracker.error_message,
                "metadata": tracker.metadata,
                "custom_metrics": tracker.custom_metrics
            }

            await db[self.metrics_collection].insert_one(metrics_doc)
            logger.debug(f"Saved metrics for audience_id: {tracker.audience_id}")

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}", exc_info=True)

    async def _update_aggregates(self, category: str, tracker: "GenerationTracker") -> None:
        """
        Update aggregate statistics in Redis for fast access.

        TODO: Implement Redis operations for:
        - Increment success/failure counters
        - Update average duration
        - Store recent performance samples
        - Calculate rolling success rate
        """
        try:
            # Update counters
            cache_key_success = f"audience:metrics:{category}:success_count"
            cache_key_failure = f"audience:metrics:{category}:failure_count"
            cache_key_duration = f"audience:metrics:{category}:avg_duration"

            if tracker.status == "success":
                redis_client.increment(cache_key_success)
            else:
                redis_client.increment(cache_key_failure)

            # Update average duration (simple moving average)
            # TODO: Implement proper rolling average calculation
            if tracker.duration:
                redis_client.set(
                    cache_key_duration,
                    tracker.duration,
                    ttl=86400  # 24 hour TTL
                )

            logger.debug(f"Updated aggregate metrics for category: {category}")

        except Exception as e:
            logger.error(f"Failed to update aggregates: {e}", exc_info=True)

    async def _trigger_performance_alert(self, category: str, duration: float) -> None:
        """
        Trigger alert for performance threshold violation.

        TODO: Implement alerting mechanism
        - Log warning
        - Send notification (email, Slack, PagerDuty, etc.)
        - Record alert in database
        """
        alert_message = (
            f"PERFORMANCE ALERT: Audience generation for {category} "
            f"took {duration:.2f}s (threshold: {self.performance_threshold_seconds}s)"
        )

        logger.warning(alert_message)

        # TODO: Integrate with alerting service
        # await alerting_service.send_alert("performance", alert_message)

    async def _trigger_failure_alert(self, category: str, error: str) -> None:
        """
        Trigger alert for audience generation failure.

        TODO: Implement failure alerting
        """
        alert_message = (
            f"FAILURE ALERT: Audience generation failed for {category}: {error}"
        )

        logger.error(alert_message)

        # TODO: Check failure rate and escalate if needed
        # failure_rate = await self._calculate_failure_rate(category)
        # if failure_rate > self.alert_threshold_failure_rate:
        #     await alerting_service.send_alert("high_failure_rate", ...)

    async def get_category_statistics(
        self,
        category: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for a category.

        Returns:
            Dictionary containing:
            - total_generations: Total audience generations
            - success_count: Successful generations
            - failure_count: Failed generations
            - success_rate: Percentage of successful generations
            - avg_duration: Average generation time
            - recent_generations: List of recent generation metrics

        TODO: Implement MongoDB aggregation query
        """
        try:
            db = mongo_client.get_database()
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            # Aggregate pipeline
            pipeline = [
                {
                    "$match": {
                        "category": category,
                        "timestamp": {"$gte": cutoff_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$duration_seconds"}
                    }
                }
            ]

            results = await db[self.metrics_collection].aggregate(pipeline).to_list(None)

            # Process results
            stats = {
                "category": category,
                "time_window_hours": time_window_hours,
                "total_generations": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0
            }

            for result in results:
                count = result['count']
                stats['total_generations'] += count

                if result['_id'] == 'success':
                    stats['success_count'] = count
                    stats['avg_duration'] = result.get('avg_duration', 0.0)
                elif result['_id'] == 'failed':
                    stats['failure_count'] = count

            # Calculate success rate
            if stats['total_generations'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['total_generations']

            return stats

        except Exception as e:
            logger.error(f"Failed to get category statistics: {e}", exc_info=True)
            return {
                "error": str(e),
                "category": category
            }

    async def get_recent_generations(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent audience generation records.

        TODO: Implement MongoDB query with optional category filter
        """
        try:
            db = mongo_client.get_database()
            query = {}
            if category:
                query['category'] = category

            cursor = db[self.metrics_collection].find(query).sort(
                "timestamp", -1
            ).limit(limit)

            results = await cursor.to_list(length=limit)

            # Convert ObjectId to string for JSON serialization
            for doc in results:
                doc['_id'] = str(doc['_id'])

            return results

        except Exception as e:
            logger.error(f"Failed to get recent generations: {e}", exc_info=True)
            return []

    async def check_health(self) -> Dict[str, Any]:
        """
        Check monitoring system health.

        Returns system health metrics including:
        - MongoDB connection status
        - Redis connection status
        - Recent error rate
        - Last successful metric write

        TODO: Implement comprehensive health checks
        """
        health = {
            "status": "healthy",
            "checks": {}
        }

        # Check MongoDB
        try:
            db = mongo_client.get_database()
            await db.command("ping")
            health['checks']['mongodb'] = "ok"
        except Exception as e:
            health['checks']['mongodb'] = f"error: {e}"
            health['status'] = "degraded"

        # Check Redis
        try:
            redis_client.ping()
            health['checks']['redis'] = "ok"
        except Exception as e:
            health['checks']['redis'] = f"error: {e}"
            health['status'] = "degraded"

        return health


class GenerationTracker:
    """
    Tracks metrics for a single audience generation operation.

    Used within the track_generation context manager.
    """

    def __init__(
        self,
        category: str,
        audience_id: Optional[UUID],
        metadata: Dict[str, Any]
    ):
        self.category = category
        self.audience_id = audience_id
        self.metadata = metadata
        self.custom_metrics: Dict[str, Any] = {}
        self.duration: Optional[float] = None
        self.status: Optional[str] = None
        self.error_message: Optional[str] = None

    def record_metric(self, key: str, value: Any) -> None:
        """
        Record a custom metric for this generation.

        Example:
            tracker.record_metric("customers_processed", 50000)
            tracker.record_metric("threshold_adjusted", True)
        """
        self.custom_metrics[key] = value
        logger.debug(f"Recorded metric: {key}={value}")

    def set_duration(self, duration: float) -> None:
        """Set the generation duration in seconds."""
        self.duration = duration

    def set_status(self, status: str) -> None:
        """Set the generation status (success/failed)."""
        self.status = status

    def set_error(self, error: str) -> None:
        """Set error message for failed generation."""
        self.error_message = error

    def add_metadata(self, key: str, value: Any) -> None:
        """Add additional metadata."""
        self.metadata[key] = value


# Global instance
audience_monitor = AudienceMonitor()
