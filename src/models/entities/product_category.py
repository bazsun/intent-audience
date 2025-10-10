"""Product category entity model with ML model configurations."""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator

from .transaction import ProductCategory as ProductCategoryEnum


class ProductCategoryModel(BaseModel):
    """ProductCategory entity for major retail segments with ML model configurations."""
    
    category_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    category_name: ProductCategoryEnum = Field(..., description="Display name")
    intent_threshold: float = Field(..., ge=0.0, le=1.0, description="Minimum score for audience inclusion")
    min_audience_size: int = Field(..., ge=1000, description="Minimum customers required")
    model_version: str = Field(..., description="Current ML model version")
    model_config: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters and feature definitions")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Category creation date")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last configuration change")
    
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
    
    @validator('model_config')
    def validate_model_config(cls, v):
        """Ensure required config keys exist."""
        required_keys = ['algorithm', 'hyperparameters', 'features']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'Missing required model config key: {key}')
        return v
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Ensure updated_at is set to current time on updates."""
        return datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class ProductCategoryCreate(BaseModel):
    """Schema for creating new product categories."""
    category_name: ProductCategoryEnum
    intent_threshold: float = Field(..., ge=0.0, le=1.0)
    min_audience_size: int = Field(default=1000, ge=1000)
    model_version: str
    model_config: Dict[str, Any] = Field(default_factory=dict)
    
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


class ProductCategoryUpdate(BaseModel):
    """Schema for updating existing product categories."""
    intent_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_audience_size: Optional[int] = Field(None, ge=1000)
    model_version: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    
    @validator('model_version')
    def validate_model_version(cls, v):
        """Validate semantic versioning format if provided."""
        if v is not None:
            parts = v.split('.')
            if len(parts) != 3:
                raise ValueError('Model version must follow semantic versioning (e.g., "1.2.3")')
            try:
                for part in parts:
                    int(part)
            except ValueError:
                raise ValueError('Model version parts must be integers')
        return v


# Default configurations for each category
DEFAULT_CATEGORY_CONFIGS = {
    ProductCategoryEnum.ELECTRONICS: {
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42
        },
        "features": [
            "transaction_frequency",
            "average_order_value", 
            "days_since_last_purchase",
            "demographic_score",
            "marketing_engagement",
            "seasonal_patterns"
        ],
        "intent_threshold": 0.75,
        "min_audience_size": 1000
    },
    ProductCategoryEnum.HOME_GARDEN: {
        "algorithm": "gradient_boosting",
        "hyperparameters": {
            "learning_rate": 0.1,
            "n_estimators": 150,
            "max_depth": 8,
            "random_state": 42
        },
        "features": [
            "seasonal_purchase_patterns",
            "home_ownership_indicators",
            "age_demographic",
            "geographic_clustering",
            "previous_category_purchases"
        ],
        "intent_threshold": 0.70,
        "min_audience_size": 1500
    },
    ProductCategoryEnum.FASHION: {
        "algorithm": "xgboost",
        "hyperparameters": {
            "learning_rate": 0.05,
            "n_estimators": 200,
            "max_depth": 6,
            "subsample": 0.8,
            "random_state": 42
        },
        "features": [
            "age_group",
            "gender",
            "seasonal_trends",
            "brand_affinity",
            "price_sensitivity"
        ],
        "intent_threshold": 0.65,
        "min_audience_size": 2000
    },
    ProductCategoryEnum.HEALTH_BEAUTY: {
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 120,
            "max_depth": 12,
            "min_samples_split": 3,
            "random_state": 42
        },
        "features": [
            "age_lifestage_combination",
            "gender_preferences",
            "loyalty_program_engagement",
            "purchase_consistency",
            "marketing_channel_response"
        ],
        "intent_threshold": 0.72,
        "min_audience_size": 1200
    },
    ProductCategoryEnum.GROCERY: {
        "algorithm": "gradient_boosting",
        "hyperparameters": {
            "learning_rate": 0.08,
            "n_estimators": 180,
            "max_depth": 7,
            "random_state": 42
        },
        "features": [
            "purchase_frequency",
            "basket_size",
            "store_loyalty",
            "geographic_convenience",
            "family_size_indicators"
        ],
        "intent_threshold": 0.68,
        "min_audience_size": 3000
    }
}