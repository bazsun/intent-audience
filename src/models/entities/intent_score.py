"""Intent score entity model for ML predictions."""

from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator

from .transaction import ProductCategory


class IntentScore(BaseModel):
    """IntentScore entity for ML predictions of customer purchase probability."""
    
    score_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    customer_id: UUID = Field(..., description="Links to Customer")
    category_id: UUID = Field(..., description="Links to ProductCategory")
    intent_score: float = Field(..., ge=0.0, le=1.0, description="Predicted 30-day purchase probability")
    model_version: str = Field(..., description="ML model used for prediction")
    feature_values: Dict[str, Any] = Field(default_factory=dict, description="Input features used (for explainability)")
    prediction_date: datetime = Field(default_factory=datetime.utcnow, description="When score was generated")
    expires_at: datetime = Field(..., description="Score validity period (30 days)")
    
    def __init__(self, **data):
        # Auto-calculate expires_at if not provided
        if 'expires_at' not in data and 'prediction_date' in data:
            data['expires_at'] = data['prediction_date'] + timedelta(days=30)
        elif 'expires_at' not in data:
            prediction_date = data.get('prediction_date', datetime.utcnow())
            data['expires_at'] = prediction_date + timedelta(days=30)
        super().__init__(**data)
    
    @validator('prediction_date')
    def validate_prediction_date(cls, v):
        """Ensure prediction date is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Prediction date cannot be in the future')
        return v
    
    @validator('expires_at')
    def validate_expires_at(cls, v, values):
        """Ensure expires_at is after prediction_date."""
        prediction_date = values.get('prediction_date')
        if prediction_date and v <= prediction_date:
            raise ValueError('Expiration date must be after prediction date')
        return v
    
    @validator('model_version')
    def validate_model_version(cls, v):
        """Validate semantic versioning format."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError('Model version must follow semantic versioning (e.g., "1.2.3")')
        try:
            for part in parts:
                int(part)
        except ValueError:
            raise ValueError('Model version parts must be integers')
        return v
    
    @property
    def is_expired(self) -> bool:
        """Check if the intent score has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_until_expiration(self) -> int:
        """Get days until score expires."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class IntentScoreCreate(BaseModel):
    """Schema for creating new intent scores."""
    customer_id: UUID
    category_id: UUID
    intent_score: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    feature_values: Dict[str, Any] = Field(default_factory=dict)
    prediction_date: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('prediction_date')
    def validate_prediction_date(cls, v):
        """Ensure prediction date is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Prediction date cannot be in the future')
        return v
    
    @validator('model_version')
    def validate_model_version(cls, v):
        """Validate semantic versioning format."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError('Model version must follow semantic versioning (e.g., "1.2.3")')
        try:
            for part in parts:
                int(part)
        except ValueError:
            raise ValueError('Model version parts must be integers')
        return v


class IntentScoreBatch(BaseModel):
    """Schema for batch intent score generation."""
    category: ProductCategory
    customer_ids: list[UUID] = Field(default_factory=list, description="Specific customers to score (empty = all eligible)")
    model_version: Optional[str] = Field(None, description="Specific model version (None = use latest)")
    force_refresh: bool = Field(default=False, description="Generate new scores even if current ones exist")
    
    @validator('customer_ids')
    def validate_customer_ids(cls, v):
        """Limit batch size for performance."""
        if len(v) > 100000:
            raise ValueError('Batch size cannot exceed 100,000 customers')
        return v


class IntentScoreResponse(BaseModel):
    """Response schema for intent scores."""
    score_id: UUID
    customer_id: UUID
    category: ProductCategory
    intent_score: float
    model_version: str
    prediction_date: datetime
    expires_at: datetime
    days_until_expiration: int
    is_expired: bool
    
    @classmethod
    def from_intent_score(cls, score: IntentScore, category_name: ProductCategory):
        """Create response from IntentScore entity."""
        return cls(
            score_id=score.score_id,
            customer_id=score.customer_id,
            category=category_name,
            intent_score=score.intent_score,
            model_version=score.model_version,
            prediction_date=score.prediction_date,
            expires_at=score.expires_at,
            days_until_expiration=score.days_until_expiration,
            is_expired=score.is_expired
        )