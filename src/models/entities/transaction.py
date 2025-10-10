"""Transaction entity model for purchase events."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator


class ProductCategory(str, Enum):
    """Major retail product categories."""
    ELECTRONICS = "Electronics"
    HOME_GARDEN = "Home_Garden"
    FASHION = "Fashion"
    HEALTH_BEAUTY = "Health_Beauty"
    GROCERY = "Grocery"


class Channel(str, Enum):
    """Purchase channel enumeration."""
    ONLINE = "Online"
    IN_STORE = "In_Store"


class Transaction(BaseModel):
    """Transaction entity representing purchase events from in-store and online channels."""
    
    transaction_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    customer_id: UUID = Field(..., description="Links to Customer")
    product_category: ProductCategory = Field(..., description="Product classification")
    transaction_amount: Decimal = Field(..., ge=0.01, decimal_places=2, description="Purchase value")
    transaction_date: datetime = Field(..., description="When purchase occurred")
    channel: Channel = Field(..., description="Purchase channel")
    store_postcode: Optional[str] = Field(None, min_length=4, max_length=10, description="Location for in-store purchases")
    delivery_postcode: Optional[str] = Field(None, min_length=4, max_length=10, description="Delivery location for online orders")
    
    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        """Ensure transaction date is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Transaction date cannot be in the future')
        return v
    
    @validator('store_postcode')
    def validate_store_postcode(cls, v, values):
        """Store postcode is required for in-store purchases."""
        channel = values.get('channel')
        if channel == Channel.IN_STORE and not v:
            raise ValueError('Store postcode is required for in-store purchases')
        if v:
            if not v.replace(' ', '').replace('-', '').isalnum():
                raise ValueError('Invalid store postcode format')
            return v.upper().strip()
        return v
    
    @validator('delivery_postcode')
    def validate_delivery_postcode(cls, v, values):
        """Delivery postcode is required for online purchases."""
        channel = values.get('channel')
        if channel == Channel.ONLINE and not v:
            raise ValueError('Delivery postcode is required for online purchases')
        if v:
            if not v.replace(' ', '').replace('-', '').isalnum():
                raise ValueError('Invalid delivery postcode format')
            return v.upper().strip()
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
            Decimal: float
        }


class TransactionCreate(BaseModel):
    """Schema for creating new transactions."""
    customer_id: UUID
    product_category: ProductCategory
    transaction_amount: Decimal = Field(..., ge=0.01, decimal_places=2)
    transaction_date: datetime
    channel: Channel
    store_postcode: Optional[str] = Field(None, min_length=4, max_length=10)
    delivery_postcode: Optional[str] = Field(None, min_length=4, max_length=10)
    
    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        """Ensure transaction date is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Transaction date cannot be in the future')
        return v
    
    @validator('store_postcode')
    def validate_store_postcode(cls, v, values):
        """Store postcode is required for in-store purchases."""
        channel = values.get('channel')
        if channel == Channel.IN_STORE and not v:
            raise ValueError('Store postcode is required for in-store purchases')
        if v:
            if not v.replace(' ', '').replace('-', '').isalnum():
                raise ValueError('Invalid store postcode format')
            return v.upper().strip()
        return v
    
    @validator('delivery_postcode')
    def validate_delivery_postcode(cls, v, values):
        """Delivery postcode is required for online purchases."""
        channel = values.get('channel')
        if channel == Channel.ONLINE and not v:
            raise ValueError('Delivery postcode is required for online purchases')
        if v:
            if not v.replace(' ', '').replace('-', '').isalnum():
                raise ValueError('Invalid delivery postcode format')
            return v.upper().strip()
        return v


class TransactionSummary(BaseModel):
    """Lightweight transaction representation for aggregations."""
    transaction_id: UUID
    customer_id: UUID
    product_category: ProductCategory
    transaction_amount: Decimal
    transaction_date: datetime
    channel: Channel