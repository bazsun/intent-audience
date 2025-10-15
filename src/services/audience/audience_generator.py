"""
Audience Generation Service (T022)

Purpose: Generate audiences using ML predictions + thresholds
- Enforces minimum 1000+ customer requirement
- Applies threshold-based filtering (configurable per category)
- Automatic adjustment if below minimum size
- Calculates quality metrics during generation
- Supports Draft/Active/Archived status

Dependencies: T021 (intent_predictor.py)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from src.models.entities.audience import (
    Audience, AudienceCreate, AudienceStatus, AudienceMembership
)
from src.models.entities.transaction import ProductCategory
from src.models.entities.intent_score import IntentScore
from src.utils.config.category_config import category_config_manager
from src.utils.database.postgres_client import postgres_client
from src.utils.database.mongo_client import mongo_client

logger = logging.getLogger(__name__)


class AudienceGenerationError(Exception):
    """Exception raised when audience generation fails."""
    pass


class AudienceGenerator:
    """
    Service for generating customer audiences based on ML intent scores.

    This service orchestrates the audience creation process by:
    1. Fetching active intent scores for the target category
    2. Applying threshold-based filtering
    3. Ensuring minimum audience size requirements
    4. Calculating quality metrics
    5. Persisting audience and membership data
    """

    def __init__(self):
        self.min_audience_size = 1000  # Global minimum, can be overridden per category

    async def generate_audience(
        self,
        request: AudienceCreate,
        auto_adjust_threshold: bool = True
    ) -> Audience:
        """
        Generate a new audience for a product category.

        Args:
            request: Audience creation request with category, name, threshold, etc.
            auto_adjust_threshold: If True, automatically lower threshold to meet min size

        Returns:
            Generated Audience entity with quality metrics

        Raises:
            AudienceGenerationError: If audience generation fails

        TODO:
        - Implement intent score fetching from PostgreSQL
        - Apply threshold filtering
        - Call threshold_adjuster if needed
        - Calculate quality metrics (demographic_distribution, conversion_rate, geographic_coverage)
        - Save audience and memberships to database
        - Integrate with audience_monitor for performance tracking
        """
        logger.info(f"Generating audience for category: {request.category.value}")

        try:
            # Get category configuration
            category_config = category_config_manager.get_category(request.category.value)
            if not category_config:
                raise AudienceGenerationError(f"Category configuration not found: {request.category}")

            # Fetch category_id from product_categories table
            category_id = await self._get_category_id(request.category)

            # Determine threshold to use
            threshold = request.custom_threshold or category_config.default_threshold
            min_size = category_config.min_audience_size

            # Fetch active intent scores for this category
            intent_scores = await self._fetch_intent_scores(category_id, threshold)

            logger.info(f"Found {len(intent_scores)} customers above threshold {threshold}")

            # Check if we need threshold adjustment
            if len(intent_scores) < min_size and auto_adjust_threshold:
                logger.warning(
                    f"Audience size {len(intent_scores)} below minimum {min_size}. "
                    f"Auto-adjusting threshold..."
                )
                # Call threshold_adjuster to find optimal threshold
                from src.services.audience.threshold_adjuster import ThresholdAdjuster
                adjuster = ThresholdAdjuster()
                adjusted_threshold, intent_scores = await adjuster.adjust_threshold(
                    category_id=category_id,
                    target_size=min_size,
                    max_threshold=threshold
                )
                threshold = adjusted_threshold
                logger.info(f"Adjusted threshold to {threshold}, new size: {len(intent_scores)}")

            # Validate minimum size requirement
            if len(intent_scores) < min_size:
                raise AudienceGenerationError(
                    f"Cannot generate audience: only {len(intent_scores)} customers found, "
                    f"minimum required is {min_size}"
                )

            # Apply max_customers cap if specified
            if request.max_customers and len(intent_scores) > request.max_customers:
                # Sort by intent score descending and take top N
                intent_scores = sorted(
                    intent_scores,
                    key=lambda x: x['intent_score'],
                    reverse=True
                )[:request.max_customers]
                logger.info(f"Capped audience size to {request.max_customers}")

            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                intent_scores,
                category_id
            )

            # Calculate average intent score
            avg_score = sum(s['intent_score'] for s in intent_scores) / len(intent_scores)

            # Create audience entity
            audience = Audience(
                audience_id=uuid4(),
                category_id=category_id,
                audience_name=request.audience_name,
                generation_date=datetime.utcnow(),
                threshold_used=threshold,
                total_customers=len(intent_scores),
                average_intent_score=avg_score,
                status=AudienceStatus.DRAFT,
                created_by=request.created_by,
                quality_metrics=quality_metrics
            )

            # Save audience to PostgreSQL
            await self._save_audience(audience)

            # Create audience memberships
            await self._create_memberships(audience.audience_id, intent_scores)

            logger.info(
                f"Successfully generated audience '{audience.audience_name}' "
                f"with {audience.total_customers} customers"
            )

            return audience

        except Exception as e:
            logger.error(f"Audience generation failed: {e}", exc_info=True)
            raise AudienceGenerationError(f"Failed to generate audience: {str(e)}")

    async def _get_category_id(self, category: ProductCategory) -> UUID:
        """
        Fetch category_id from product_categories table.
        """
        query = """
            SELECT category_id
            FROM product_categories
            WHERE category_name = $1
        """
        try:
            result = await postgres_client.fetch_one(query, category.value)

            if not result:
                raise AudienceGenerationError(f"Product category not found: {category}")

            return UUID(result['category_id'])
        except Exception as e:
            logger.error(f"Error fetching category_id: {e}")
            raise AudienceGenerationError(f"Database error: {str(e)}")

    async def _fetch_intent_scores(
        self,
        category_id: UUID,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Fetch active (non-expired) intent scores above threshold.
        """
        query = """
            SELECT
                score_id,
                customer_id,
                intent_score,
                prediction_date,
                model_version
            FROM intent_scores
            WHERE category_id = $1
                AND intent_score >= $2
                AND expires_at > CURRENT_TIMESTAMP
            ORDER BY intent_score DESC
        """
        try:
            results = await postgres_client.fetch_all(query, str(category_id), threshold)
            return results
        except Exception as e:
            logger.error(f"Error fetching intent scores: {e}")
            raise AudienceGenerationError(f"Database error: {str(e)}")

    async def _calculate_quality_metrics(
        self,
        intent_scores: List[Dict[str, Any]],
        category_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for the audience (MVP: simplified).
        """
        # OPTION C: Minimal viable - basic metrics without complex queries
        return {
            'demographic_distribution': {
                'total': len(intent_scores),
                'breakdown': []  # MVP: Skip detailed demographics
            },
            'historical_conversion_rate': 0.15,  # Placeholder for MVP
            'geographic_coverage': {
                'unique_postcodes': 0,  # MVP: Skip geographic analysis
                'total_customers': len(intent_scores)
            },
            'score_distribution': {
                'min': float(min(s['intent_score'] for s in intent_scores)) if intent_scores else 0,
                'max': float(max(s['intent_score'] for s in intent_scores)) if intent_scores else 0,
                'median': float(sorted(s['intent_score'] for s in intent_scores)[len(intent_scores) // 2]) if intent_scores else 0
            }
        }

    async def _save_audience(self, audience: Audience) -> None:
        """
        Save audience to PostgreSQL.

        TODO: Implement INSERT query for audiences table
        """
        query = """
            INSERT INTO audiences (
                audience_id, category_id, audience_name, generation_date,
                threshold_used, total_customers, average_intent_score,
                status, created_by, quality_metrics
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        await postgres_client.execute_sql(
            query,
            str(audience.audience_id),
            str(audience.category_id),
            audience.audience_name,
            audience.generation_date,
            audience.threshold_used,
            audience.total_customers,
            audience.average_intent_score,
            audience.status.value,
            str(audience.created_by),
            audience.quality_metrics  # asyncpg supports JSON/JSONB natively
        )

    async def _create_memberships(
        self,
        audience_id: UUID,
        intent_scores: List[Dict[str, Any]]
    ) -> None:
        """
        Create audience membership records for all customers.

        TODO: Implement batch INSERT for audience_memberships table
        """
        # Rank customers by intent score
        ranked_scores = sorted(
            enumerate(intent_scores, start=1),
            key=lambda x: x[1]['intent_score'],
            reverse=True
        )

        # Prepare batch insert values
        membership_records = []
        for rank, score_data in ranked_scores:
            membership_records.append((
                uuid4(),  # membership_id
                audience_id,
                score_data['customer_id'],
                score_data['intent_score'],
                datetime.utcnow(),  # included_at
                rank
            ))

        # TODO: Batch insert memberships (use executemany or COPY for performance)
        # For now, use multiple inserts (optimize in production)
        query = """
            INSERT INTO audience_memberships (
                membership_id, audience_id, customer_id,
                intent_score_at_inclusion, included_at, rank_in_audience
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """

        for record in membership_records:
            await postgres_client.execute_sql(
                query,
                str(record[0]),  # membership_id
                str(record[1]),  # audience_id
                str(record[2]),  # customer_id
                record[3],       # intent_score_at_inclusion
                record[4],       # included_at
                record[5]        # rank_in_audience
            )

        logger.info(f"Created {len(membership_records)} membership records")

    async def get_audience_by_id(self, audience_id: UUID) -> Optional[Audience]:
        """
        Retrieve an audience by ID.

        TODO: Implement SELECT query for audiences table
        """
        query = """
            SELECT * FROM audiences WHERE audience_id = $1
        """
        result = await postgres_client.fetch_one(query, str(audience_id))

        if not result:
            return None

        # Convert to Audience entity
        return Audience(
            audience_id=UUID(result['audience_id']),
            category_id=UUID(result['category_id']),
            audience_name=result['audience_name'],
            generation_date=result['generation_date'],
            threshold_used=float(result['threshold_used']),
            total_customers=result['total_customers'],
            average_intent_score=float(result['average_intent_score']),
            status=AudienceStatus(result['status']),
            created_by=UUID(result['created_by']),
            quality_metrics=result['quality_metrics']
        )

    async def list_audiences(
        self,
        category: Optional[ProductCategory] = None,
        status: Optional[AudienceStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Audience]:
        """
        List audiences with optional filtering.

        TODO: Implement SELECT query with filters and pagination
        """
        # Build dynamic query
        conditions = []
        params = []
        param_count = 1

        if category:
            # Need to join with product_categories to filter by name
            category_id = await self._get_category_id(category)
            conditions.append(f"category_id = ${param_count}")
            params.append(str(category_id))
            param_count += 1

        if status:
            conditions.append(f"status = ${param_count}")
            params.append(status.value)
            param_count += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT * FROM audiences
            {where_clause}
            ORDER BY generation_date DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        results = await postgres_client.fetch_all(query, *params)

        # Convert to Audience entities
        audiences = []
        for result in results:
            audiences.append(Audience(
                audience_id=UUID(result['audience_id']),
                category_id=UUID(result['category_id']),
                audience_name=result['audience_name'],
                generation_date=result['generation_date'],
                threshold_used=float(result['threshold_used']),
                total_customers=result['total_customers'],
                average_intent_score=float(result['average_intent_score']),
                status=AudienceStatus(result['status']),
                created_by=UUID(result['created_by']),
                quality_metrics=result['quality_metrics']
            ))

        return audiences

    async def update_audience_status(
        self,
        audience_id: UUID,
        new_status: AudienceStatus
    ) -> Audience:
        """
        Update the status of an audience.

        TODO: Implement UPDATE query for audiences table
        """
        query = """
            UPDATE audiences
            SET status = $1
            WHERE audience_id = $2
            RETURNING *
        """
        result = await postgres_client.fetch_one(
            query,
            new_status.value,
            str(audience_id)
        )

        if not result:
            raise AudienceGenerationError(f"Audience not found: {audience_id}")

        logger.info(f"Updated audience {audience_id} status to {new_status.value}")

        return Audience(
            audience_id=UUID(result['audience_id']),
            category_id=UUID(result['category_id']),
            audience_name=result['audience_name'],
            generation_date=result['generation_date'],
            threshold_used=float(result['threshold_used']),
            total_customers=result['total_customers'],
            average_intent_score=float(result['average_intent_score']),
            status=AudienceStatus(result['status']),
            created_by=UUID(result['created_by']),
            quality_metrics=result['quality_metrics']
        )


# Global instance
audience_generator = AudienceGenerator()
