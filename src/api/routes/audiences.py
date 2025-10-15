"""
Audience Management API Endpoints (T024-T026)

Purpose: RESTful endpoints for audience operations
- T024: POST /audiences - Create new audience
- T025: GET /audiences - List all audiences
- T026: GET /audiences/{id} - Get audience details

Dependencies: T022 (audience_generator), T027 (audience_schemas)
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from uuid import UUID
import logging

from src.api.schemas.audience_schemas import (
    CreateAudienceRequest,
    AudienceResponse,
    AudienceDetailResponse,
    AudienceListResponse,
    AudienceCustomersResponse,
    UpdateAudienceStatusRequest,
    ListAudiencesQuery,
    ErrorResponse
)
from src.models.entities.transaction import ProductCategory
from src.models.entities.audience import AudienceStatus
from src.services.audience.audience_generator import audience_generator, AudienceGenerationError
from src.utils.monitoring.audience_monitor import audience_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["audiences"])


@router.post(
    "/audiences",
    response_model=AudienceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Audience generation failed"}
    }
)
async def create_audience(request: CreateAudienceRequest) -> AudienceResponse:
    """
    Create a new audience for a product category.

    Generates an audience by:
    1. Fetching active intent scores for the category
    2. Applying threshold filtering
    3. Auto-adjusting threshold if below minimum size (optional)
    4. Calculating quality metrics
    5. Saving audience and memberships to database

    TODO:
    - Integrate with audience_generator.generate_audience()
    - Wrap in audience_monitor.track_generation() for performance tracking
    - Handle AudienceGenerationError exceptions
    - Convert Audience entity to AudienceResponse schema
    - Return created audience with 201 status
    """
    logger.info(
        f"POST /audiences - Creating audience: '{request.audience_name}' "
        f"for category: {request.category.value}"
    )

    try:
        # OPTION C: Minimal viable - skip monitoring for MVP
        # Convert API request to AudienceCreate entity
        from src.models.entities.audience import AudienceCreate
        audience_create = AudienceCreate(
            category=request.category,
            audience_name=request.audience_name,
            custom_threshold=request.custom_threshold,
            max_customers=request.max_customers,
            created_by=request.created_by
        )

        # Call audience generator
        audience = await audience_generator.generate_audience(
            audience_create,
            auto_adjust_threshold=request.auto_adjust_threshold
        )

        # Convert to response schema
        from src.api.schemas.audience_schemas import audience_to_response
        response = audience_to_response(audience, request.category.value)

        return response

    except AudienceGenerationError as e:
        logger.error(f"Audience generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audience: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating audience: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/audiences",
    response_model=AudienceListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"}
    }
)
async def list_audiences(
    category: Optional[ProductCategory] = Query(None, description="Filter by product category"),
    status_filter: Optional[AudienceStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> AudienceListResponse:
    """
    List all audiences with optional filtering and pagination.

    Query Parameters:
    - category: Filter by product category (Electronics, Home_Garden, etc.)
    - status: Filter by audience status (Active, Archived, Draft)
    - limit: Maximum results to return (1-1000)
    - offset: Number of results to skip (for pagination)

    TODO:
    - Call audience_generator.list_audiences() with filters
    - Get total count for pagination
    - Convert audience entities to response schemas
    - Return paginated list
    """
    logger.info(
        f"GET /audiences - category: {category}, status: {status_filter}, "
        f"limit: {limit}, offset: {offset}"
    )

    try:
        # OPTION C: Minimal viable - simplified pagination
        audiences = await audience_generator.list_audiences(
            category=category,
            status=status_filter,
            limit=limit,
            offset=offset
        )

        # For MVP, total_count = number returned
        total_count = len(audiences)

        # Convert to response schemas (MVP: use placeholder category name)
        from src.api.schemas.audience_schemas import audience_to_response
        audience_responses = []
        for audience in audiences:
            # MVP: Extract category name from audience (simplification)
            cat_name = category.value if category else "Electronics"
            response = audience_to_response(audience, cat_name)
            audience_responses.append(response)

        return AudienceListResponse(
            audiences=audience_responses,
            total=total_count,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing audiences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list audiences"
        )


@router.get(
    "/audiences/{audience_id}",
    response_model=AudienceDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Audience not found"}
    }
)
async def get_audience(audience_id: UUID) -> AudienceDetailResponse:
    """
    Get detailed information about a specific audience.

    Returns:
    - Audience metadata (name, category, size, etc.)
    - Quality metrics (demographics, conversion rate, geographic coverage)
    - Generation details (threshold used, creation date, creator)

    TODO:
    - Call audience_generator.get_audience_by_id()
    - Handle not found case with 404
    - Convert to detailed response schema
    - Include category name lookup
    """
    logger.info(f"GET /audiences/{audience_id}")

    try:
        # Fetch audience by ID
        audience = await audience_generator.get_audience_by_id(audience_id)

        if not audience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audience not found: {audience_id}"
            )

        # MVP: Use placeholder category name (would need lookup in full implementation)
        category_name = "Electronics"

        # Convert to detailed response
        from src.api.schemas.audience_schemas import audience_to_detail_response
        response = audience_to_detail_response(audience, category_name)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audience {audience_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audience"
        )


@router.patch(
    "/audiences/{audience_id}/status",
    response_model=AudienceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Audience not found"}
    }
)
async def update_audience_status(
    audience_id: UUID,
    request: UpdateAudienceStatusRequest
) -> AudienceResponse:
    """
    Update the status of an audience (Draft -> Active -> Archived).

    Allowed transitions:
    - Draft -> Active
    - Active -> Archived
    - Draft -> Archived

    TODO:
    - Call audience_generator.update_audience_status()
    - Validate status transition
    - Return updated audience
    """
    logger.info(f"PATCH /audiences/{audience_id}/status - new status: {request.status}")

    try:
        # TODO: Update audience status
        audience = await audience_generator.update_audience_status(
            audience_id,
            request.status
        )

        if not audience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audience not found: {audience_id}"
            )

        # TODO: Convert to response
        from src.api.schemas.audience_schemas import audience_to_response
        category_name = "Electronics"  # Placeholder - need category lookup
        response = audience_to_response(audience, category_name)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating audience status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update audience status"
        )


@router.get(
    "/audiences/{audience_id}/customers",
    response_model=AudienceCustomersResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Audience not found"}
    }
)
async def get_audience_customers(
    audience_id: UUID,
    limit: int = Query(100, ge=1, le=10000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> AudienceCustomersResponse:
    """
    Get list of customers in an audience with their intent scores and rankings.

    Returns paginated list ordered by rank (highest intent score first).

    TODO:
    - Query audience_memberships table
    - Join with customers for additional details (optional)
    - Return paginated customer list with scores and rankings
    """
    logger.info(f"GET /audiences/{audience_id}/customers - limit: {limit}, offset: {offset}")

    # TODO: Implement customer listing
    # Query: SELECT * FROM audience_memberships WHERE audience_id = $1 ORDER BY rank_in_audience LIMIT $2 OFFSET $3

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Customer listing not yet implemented"
    )