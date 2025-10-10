"""Audience entity model for generated customer segments."""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator

from .transaction import ProductCategory


class AudienceStatus(str, Enum):
    """Audience status enumeration."""
    ACTIVE = "Active"
    ARCHIVED = "Archived"
    DRAFT = "Draft"


class Audience(BaseModel):
    """Audience entity for generated customer segments for marketing campaigns."""
    
    audience_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    category_id: UUID = Field(..., description="Links to ProductCategory")
    audience_name: str = Field(..., max_length=100, description="Human-readable name")
    generation_date: datetime = Field(default_factory=datetime.utcnow, description="When audience was created")
    threshold_used: float = Field(..., ge=0.0, le=1.0, description="Intent score threshold applied")
    total_customers: int = Field(..., ge=0, description="Number of customers included")
    average_intent_score: float = Field(..., ge=0.0, le=1.0, description="Mean score of included customers")
    status: AudienceStatus = Field(default=AudienceStatus.DRAFT, description="Audience state")
    created_by: UUID = Field(..., description="User who generated audience")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance and validation metrics")
    
    @validator('average_intent_score')
    def validate_average_score(cls, v, values):
        """Ensure average score is >= threshold used."""
        threshold = values.get('threshold_used')
        if threshold is not None and v < threshold:
            raise ValueError('Average intent score must be >= threshold used')
        return v
    
    @validator('quality_metrics')
    def validate_quality_metrics(cls, v):
        """Ensure required quality metrics are present."""
        required_metrics = [
            'demographic_distribution',
            'historical_conversion_rate',
            'geographic_coverage'
        ]
        for metric in required_metrics:
            if metric not in v:
                # Initialize with default values for new audiences
                if metric == 'demographic_distribution':
                    v[metric] = {}
                elif metric == 'historical_conversion_rate':
                    v[metric] = 0.0
                elif metric == 'geographic_coverage':
                    v[metric] = {}
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class AudienceCreate(BaseModel):
    """Schema for creating new audiences."""
    category: ProductCategory
    audience_name: str = Field(..., max_length=100)
    custom_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override category default")
    max_customers: Optional[int] = Field(None, ge=1000, le=1000000, description="Cap on audience size")
    created_by: UUID
    
    @validator('audience_name')
    def validate_audience_name(cls, v):
        """Ensure audience name is not empty and doesn't contain invalid characters."""
        if not v.strip():
            raise ValueError('Audience name cannot be empty')
        # Remove potentially problematic characters
        invalid_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f'Audience name cannot contain: {char}')
        return v.strip()


class AudienceUpdate(BaseModel):
    """Schema for updating existing audiences."""
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="New intent score threshold")
    status: Optional[AudienceStatus] = None
    audience_name: Optional[str] = Field(None, max_length=100)
    
    @validator('audience_name')
    def validate_audience_name(cls, v):
        """Ensure audience name is valid if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError('Audience name cannot be empty')
            invalid_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f'Audience name cannot contain: {char}')
            return v.strip()
        return v


class AudienceResponse(BaseModel):
    """Response schema for audience data."""
    audience_id: UUID
    category: ProductCategory
    audience_name: str
    generation_date: datetime
    threshold_used: float
    total_customers: int
    average_intent_score: float
    status: AudienceStatus
    estimated_completion_time: Optional[datetime] = None
    
    @classmethod
    def from_audience(cls, audience: Audience, category_name: ProductCategory, estimated_completion: Optional[datetime] = None):
        """Create response from Audience entity."""
        return cls(
            audience_id=audience.audience_id,
            category=category_name,
            audience_name=audience.audience_name,
            generation_date=audience.generation_date,
            threshold_used=audience.threshold_used,
            total_customers=audience.total_customers,
            average_intent_score=audience.average_intent_score,
            status=audience.status,
            estimated_completion_time=estimated_completion
        )


class AudienceDetailResponse(AudienceResponse):
    """Detailed response schema for audience data."""
    quality_metrics: Dict[str, Any]
    created_by: UUID
    
    @classmethod
    def from_audience_detailed(cls, audience: Audience, category_name: ProductCategory, estimated_completion: Optional[datetime] = None):
        """Create detailed response from Audience entity."""
        return cls(
            audience_id=audience.audience_id,
            category=category_name,
            audience_name=audience.audience_name,
            generation_date=audience.generation_date,
            threshold_used=audience.threshold_used,
            total_customers=audience.total_customers,
            average_intent_score=audience.average_intent_score,
            status=audience.status,
            quality_metrics=audience.quality_metrics,
            created_by=audience.created_by,
            estimated_completion_time=estimated_completion
        )


class AudienceMembership(BaseModel):
    """Link table for Customer-Audience many-to-many relationship."""
    
    membership_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    audience_id: UUID = Field(..., description="Links to Audience")
    customer_id: UUID = Field(..., description="Links to Customer")
    intent_score_at_inclusion: float = Field(..., ge=0.0, le=1.0, description="Score when customer was added")
    included_at: datetime = Field(default_factory=datetime.utcnow, description="When customer was added to audience")
    rank_in_audience: int = Field(..., ge=1, description="Customer ranking by intent score")
    
    @validator('rank_in_audience')
    def validate_rank(cls, v):
        """Ensure rank is positive."""
        if v < 1:
            raise ValueError('Rank in audience must be positive')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class CustomerInAudience(BaseModel):
    """Schema for customer data within an audience."""
    customer_id: UUID
    intent_score: float
    rank_in_audience: int
    included_at: datetime