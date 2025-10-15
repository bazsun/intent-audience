"""
Automatic Threshold Adjustment Service (T028)

Purpose: Auto-adjust thresholds to meet minimum audience size
- Enhancement to T022 (audience_generator)
- Binary search algorithm to find optimal threshold
- Ensures minimum customer count is met
- Prevents excessive lowering of quality standards

Dependencies: T022 (called by audience_generator.py)
"""

import logging
from typing import Dict, Any, List, Tuple
from uuid import UUID

from src.utils.database.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class ThresholdAdjustmentError(Exception):
    """Exception raised when threshold adjustment fails."""
    pass


class ThresholdAdjuster:
    """
    Service for automatically adjusting intent score thresholds to meet audience size requirements.

    Uses binary search to efficiently find the optimal threshold that:
    1. Meets the minimum audience size requirement
    2. Maintains the highest possible quality (highest scores)
    3. Doesn't go below a safety minimum threshold
    """

    def __init__(self):
        self.min_threshold = 0.3  # Safety minimum - never go below 30% intent
        self.max_iterations = 20  # Prevent infinite loops

    async def adjust_threshold(
        self,
        category_id: UUID,
        target_size: int,
        max_threshold: float,
        tolerance: int = 100
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Find the optimal threshold to meet target audience size.

        Uses binary search between min_threshold and max_threshold to find
        a threshold that yields an audience size within tolerance of target_size.

        Args:
            category_id: Product category to generate audience for
            target_size: Desired minimum audience size
            max_threshold: Starting maximum threshold (from category config)
            tolerance: Acceptable deviation from target_size (default 100)

        Returns:
            Tuple of (adjusted_threshold, intent_scores_list)

        Raises:
            ThresholdAdjustmentError: If no valid threshold can be found

        TODO:
        - Implement binary search algorithm
        - Query intent scores at each threshold iteration
        - Handle edge cases (too few customers even at min threshold)
        - Log adjustment iterations for monitoring
        """
        logger.info(
            f"Adjusting threshold for category {category_id}: "
            f"target_size={target_size}, max_threshold={max_threshold}"
        )

        # Validate inputs
        if target_size < 1000:
            raise ThresholdAdjustmentError("Target size must be at least 1000")

        if max_threshold <= self.min_threshold:
            raise ThresholdAdjustmentError(
                f"Max threshold ({max_threshold}) must be greater than "
                f"min threshold ({self.min_threshold})"
            )

        # Initialize binary search bounds
        low_threshold = self.min_threshold
        high_threshold = max_threshold
        best_threshold = None
        best_scores = None
        iteration = 0

        # TODO: Implement binary search
        while iteration < self.max_iterations:
            iteration += 1

            # Calculate midpoint threshold
            current_threshold = (low_threshold + high_threshold) / 2.0

            # Fetch intent scores at current threshold
            scores = await self._fetch_scores_at_threshold(category_id, current_threshold)
            current_size = len(scores)

            logger.debug(
                f"Iteration {iteration}: threshold={current_threshold:.4f}, "
                f"size={current_size}, target={target_size}"
            )

            # Check if we've found a good threshold
            if abs(current_size - target_size) <= tolerance and current_size >= target_size:
                # Found acceptable solution
                logger.info(
                    f"Found optimal threshold: {current_threshold:.4f} "
                    f"(size: {current_size}, target: {target_size})"
                )
                return current_threshold, scores

            # Update best candidate if this is better than previous
            if current_size >= target_size:
                if best_threshold is None or current_threshold > best_threshold:
                    best_threshold = current_threshold
                    best_scores = scores

            # Adjust search bounds
            if current_size < target_size:
                # Need more customers - lower the threshold
                high_threshold = current_threshold
            else:
                # Too many customers - can try raising threshold
                low_threshold = current_threshold

            # Check for convergence
            if high_threshold - low_threshold < 0.001:
                logger.debug("Search converged")
                break

        # Binary search complete - use best result found
        if best_threshold is not None and len(best_scores) >= target_size:
            logger.info(
                f"Threshold adjusted to {best_threshold:.4f} "
                f"(size: {len(best_scores)}, target: {target_size})"
            )
            return best_threshold, best_scores

        # Could not find valid threshold
        final_scores = await self._fetch_scores_at_threshold(category_id, self.min_threshold)
        final_size = len(final_scores)

        if final_size < target_size:
            raise ThresholdAdjustmentError(
                f"Cannot meet target size {target_size}. "
                f"Only {final_size} customers available even at minimum threshold {self.min_threshold}"
            )

        # Return minimum threshold result
        logger.warning(
            f"Using minimum threshold {self.min_threshold} to meet target. "
            f"Size: {final_size}, Target: {target_size}"
        )
        return self.min_threshold, final_scores

    async def _fetch_scores_at_threshold(
        self,
        category_id: UUID,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Fetch active intent scores at or above the given threshold.

        TODO: Implement efficient PostgreSQL query
        - Filter by category_id
        - Filter by threshold
        - Filter by expires_at > NOW()
        - Include: score_id, customer_id, intent_score, prediction_date
        - Order by intent_score DESC
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
            results = await postgres_client.fetch_all(
                query,
                str(category_id),
                threshold
            )
            return results
        except Exception as e:
            logger.error(f"Error fetching scores at threshold {threshold}: {e}")
            raise ThresholdAdjustmentError(f"Failed to fetch intent scores: {str(e)}")

    async def estimate_threshold_for_size(
        self,
        category_id: UUID,
        target_size: int
    ) -> float:
        """
        Estimate what threshold would be needed to achieve target size.

        This is a faster estimation method that doesn't fetch full score lists.
        Useful for providing threshold recommendations to users.

        TODO: Implement estimation using aggregation query
        - Use PERCENTILE_CONT or similar to estimate threshold
        - Count total active scores
        - Calculate what percentile would give target_size
        """
        # Get total count of active scores
        count_query = """
            SELECT COUNT(*) as total
            FROM intent_scores
            WHERE category_id = $1
                AND expires_at > CURRENT_TIMESTAMP
        """
        count_result = await postgres_client.fetch_one(count_query, str(category_id))
        total_scores = count_result['total'] if count_result else 0

        if total_scores == 0:
            raise ThresholdAdjustmentError("No active intent scores found for category")

        if total_scores < target_size:
            logger.warning(
                f"Total available customers ({total_scores}) less than target ({target_size})"
            )
            return self.min_threshold

        # Calculate what percentile we need
        percentile = 1.0 - (target_size / total_scores)

        # TODO: Use percentile_cont to get threshold estimate
        percentile_query = """
            SELECT PERCENTILE_CONT($1) WITHIN GROUP (ORDER BY intent_score DESC) as estimated_threshold
            FROM intent_scores
            WHERE category_id = $2
                AND expires_at > CURRENT_TIMESTAMP
        """

        result = await postgres_client.fetch_one(
            percentile_query,
            percentile,
            str(category_id)
        )

        if result and result['estimated_threshold']:
            estimated = float(result['estimated_threshold'])
            # Ensure it's within bounds
            estimated = max(self.min_threshold, min(1.0, estimated))
            logger.info(
                f"Estimated threshold {estimated:.4f} for target size {target_size} "
                f"(total customers: {total_scores})"
            )
            return estimated

        # Fallback to minimum threshold
        return self.min_threshold

    def get_min_threshold(self) -> float:
        """Get the safety minimum threshold."""
        return self.min_threshold

    def set_min_threshold(self, threshold: float) -> None:
        """
        Set the safety minimum threshold.

        Args:
            threshold: New minimum threshold (must be between 0.0 and 1.0)

        Raises:
            ValueError: If threshold is out of range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")

        self.min_threshold = threshold
        logger.info(f"Updated minimum threshold to {threshold}")


# Global instance
threshold_adjuster = ThresholdAdjuster()
