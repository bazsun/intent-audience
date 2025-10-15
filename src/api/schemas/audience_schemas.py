"""
Audience API Schemas (T027)

Purpose: Request/response models for audience endpoints
- Pydantic schemas for validation
- OpenAPI 3.0 compatible
- Supports pagination
- Clear error responses

Dependencies: None (can be implemented in parallel)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator

from src.models.entities.transaction import ProductCategory
from src.models.entities.audience import AudienceStatus


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CreateAudienceRequest(BaseModel):
    """
    Request schema for creating a new audience.

    POST /audiences
    """
    category: ProductCategory = Field(
        ...,
        description="Product category to generate audience for"
    )
    audience_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for the audience"
    )
    custom_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Custom intent threshold (overrides category default)"
    )
    max_customers: Optional[int] = Field(
        None,
        ge=1000,
        le=1000000,
        description="Maximum audience size (optional cap)"
    )
    auto_adjust_threshold: bool = Field(
        default=True,
        description="Automatically lower threshold if minimum size not met"
    )
    created_by: UUID = Field(
        ...,
        description="User ID who is creating this audience"
    )

    @validator('audience_name')
    def validate_audience_name(cls, v):
        """Ensure audience name is clean and doesn't contain invalid characters."""
        if not v.strip():
            raise ValueError('Audience name cannot be empty')

        invalid_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f'Audience name cannot contain: {char}')

        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "category": "Electronics",
                "audience_name": "High-Intent Electronics Buyers Q4",
                "custom_threshold": 0.80,
                "max_customers": 50000,
                "auto_adjust_threshold": True,
                "created_by": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class UpdateAudienceStatusRequest(BaseModel):
    """
    Request schema for updating audience status.

    PATCH /audiences/{audience_id}/status
    """
    status: AudienceStatus = Field(
        ...,
        description="New status for the audience"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "Active"
            }
        }


class ListAudiencesQuery(BaseModel):
    """
    Query parameters for listing audiences.

    GET /audiences?category=Electronics&status=Active&limit=50&offset=0
    """
    category: Optional[ProductCategory] = Field(
        None,
        description="Filter by product category"
    )
    status: Optional[AudienceStatus] = Field(
        None,
        description="Filter by audience status"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip (for pagination)"
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AudienceResponse(BaseModel):
    """
    Response schema for audience summary.

    Used in list endpoints and after creation.
    """
    audience_id: UUID = Field(..., description="Unique audience identifier")
    category: ProductCategory = Field(..., description="Product category")
    audience_name: str = Field(..., description="Audience name")
    generation_date: datetime = Field(..., description="When audience was generated")
    threshold_used: float = Field(..., description="Intent score threshold applied")
    total_customers: int = Field(..., description="Number of customers in audience")
    average_intent_score: float = Field(..., description="Average intent score")
    status: AudienceStatus = Field(..., description="Current status")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
        schema_extra = {
            "example": {
                "audience_id": "123e4567-e89b-12d3-a456-426614174000",
                "category": "Electronics",
                "audience_name": "High-Intent Electronics Buyers Q4",
                "generation_date": "2024-01-15T10:30:00Z",
                "threshold_used": 0.75,
                "total_customers": 12500,
                "average_intent_score": 0.82,
                "status": "Active"
            }
        }


class QualityMetricsDetail(BaseModel):
    """Detailed quality metrics for an audience."""
    demographic_distribution: Dict[str, Any] = Field(
        ...,
        description="Breakdown by age, gender, lifestage"
    )
    historical_conversion_rate: float = Field(
        ...,
        description="Expected conversion rate based on historical data"
    )
    geographic_coverage: Dict[str, Any] = Field(
        ...,
        description="Geographic distribution of customers"
    )
    score_distribution: Dict[str, float] = Field(
        ...,
        description="Min, max, median intent scores"
    )


class AudienceDetailResponse(AudienceResponse):
    """
    Detailed response schema for a single audience.

    GET /audiences/{audience_id}
    """
    created_by: UUID = Field(..., description="User who created this audience")
    quality_metrics: QualityMetricsDetail = Field(
        ...,
        description="Detailed quality and performance metrics"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
        schema_extra = {
            "example": {
                "audience_id": "123e4567-e89b-12d3-a456-426614174000",
                "category": "Electronics",
                "audience_name": "High-Intent Electronics Buyers Q4",
                "generation_date": "2024-01-15T10:30:00Z",
                "threshold_used": 0.75,
                "total_customers": 12500,
                "average_intent_score": 0.82,
                "status": "Active",
                "created_by": "550e8400-e29b-41d4-a716-446655440000",
                "quality_metrics": {
                    "demographic_distribution": {
                        "total": 12500,
                        "breakdown": [
                            {"gender": "M", "lifestage": "Young_Adult", "count": 3500},
                            {"gender": "F", "lifestage": "Family", "count": 4200}
                        ]
                    },
                    "historical_conversion_rate": 0.18,
                    "geographic_coverage": {
                        "unique_postcodes": 850,
                        "total_customers": 12500
                    },
                    "score_distribution": {
                        "min": 0.75,
                        "max": 0.98,
                        "median": 0.81
                    }
                }
            }
        }


class CustomerInAudienceResponse(BaseModel):
    """
    Response schema for a customer within an audience.

    Used in GET /audiences/{audience_id}/customers
    """
    customer_id: UUID = Field(..., description="Customer identifier")
    intent_score: float = Field(..., description="Intent score at inclusion")
    rank_in_audience: int = Field(..., description="Rank by intent score (1 = highest)")
    included_at: datetime = Field(..., description="When customer was added")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class AudienceListResponse(BaseModel):
    """
    Paginated response for listing audiences.

    GET /audiences
    """
    audiences: List[AudienceResponse] = Field(
        ...,
        description="List of audience summaries"
    )
    total: int = Field(..., description="Total number of audiences (before pagination)")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Number of results skipped")

    class Config:
        schema_extra = {
            "example": {
                "audiences": [
                    {
                        "audience_id": "123e4567-e89b-12d3-a456-426614174000",
                        "category": "Electronics",
                        "audience_name": "High-Intent Electronics Buyers Q4",
                        "generation_date": "2024-01-15T10:30:00Z",
                        "threshold_used": 0.75,
                        "total_customers": 12500,
                        "average_intent_score": 0.82,
                        "status": "Active"
                    }
                ],
                "total": 45,
                "limit": 100,
                "offset": 0
            }
        }


class AudienceCustomersResponse(BaseModel):
    """
    Paginated response for audience customers.

    GET /audiences/{audience_id}/customers
    """
    audience_id: UUID = Field(..., description="Audience identifier")
    customers: List[CustomerInAudienceResponse] = Field(
        ...,
        description="List of customers in this audience"
    )
    total: int = Field(..., description="Total customers in audience")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Number of results skipped")

    class Config:
        json_encoders = {
            UUID: str
        }


# ============================================================================
# ERROR RESPONSE SCHEMAS
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field that caused the error (if applicable)")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """
    Standard error response schema.

    Used for 4xx and 5xx responses.
    """
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking and debugging"
    )

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "details": [
                    {
                        "field": "custom_threshold",
                        "message": "Threshold must be between 0.0 and 1.0",
                        "code": "VALUE_OUT_OF_RANGE"
                    }
                ],
                "request_id": "req_abc123xyz"
            }
        }


class SuccessResponse(BaseModel):
    """
    Generic success response for operations that don't return data.

    Used for DELETE or PATCH operations.
    """
    success: bool = Field(default=True, description="Operation success flag")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Audience status updated successfully"
            }
        }


# ============================================================================
# HELPER FUNCTIONS FOR CONVERSIONS
# ============================================================================

def audience_to_response(audience: "Audience", category_name: str) -> AudienceResponse:
    """
    Convert Audience entity to AudienceResponse schema.

    TODO: Import Audience type properly to avoid circular imports
    """
    from src.models.entities.audience import Audience

    return AudienceResponse(
        audience_id=audience.audience_id,
        category=ProductCategory(category_name),
        audience_name=audience.audience_name,
        generation_date=audience.generation_date,
        threshold_used=audience.threshold_used,
        total_customers=audience.total_customers,
        average_intent_score=audience.average_intent_score,
        status=audience.status
    )


def audience_to_detail_response(audience: "Audience", category_name: str) -> AudienceDetailResponse:
    """
    Convert Audience entity to AudienceDetailResponse schema.

    TODO: Import Audience type properly to avoid circular imports
    """
    from src.models.entities.audience import Audience

    return AudienceDetailResponse(
        audience_id=audience.audience_id,
        category=ProductCategory(category_name),
        audience_name=audience.audience_name,
        generation_date=audience.generation_date,
        threshold_used=audience.threshold_used,
        total_customers=audience.total_customers,
        average_intent_score=audience.average_intent_score,
        status=audience.status,
        created_by=audience.created_by,
        quality_metrics=QualityMetricsDetail(**audience.quality_metrics)
    )
