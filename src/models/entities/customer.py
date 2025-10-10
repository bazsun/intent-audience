"""Customer entity model for the audience generation system."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr, validator


class Gender(str, Enum):
    """Gender enumeration."""
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer_not_to_say"


class LifeStage(str, Enum):
    """Customer life stage enumeration."""
    YOUNG_ADULT = "Young_Adult"
    FAMILY = "Family"
    EMPTY_NESTER = "Empty_Nester"
    SENIOR = "Senior"


class Customer(BaseModel):
    """Customer entity representing individual retail customers with loyalty cards."""
    
    customer_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    email_address: Optional[EmailStr] = Field(None, description="For marketing engagement (hashed for privacy)")
    age: int = Field(..., ge=18, le=100, description="Demographic attribute")
    gender: Gender = Field(..., description="Demographic attribute")
    lifestage: LifeStage = Field(..., description="Demographic classification")
    home_postcode: str = Field(..., min_length=4, max_length=10, description="Geographic identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation date")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last modification date")
    
    @validator('home_postcode')
    def validate_postcode(cls, v):
        """Validate postcode format (basic validation)."""
        if not v.replace(' ', '').replace('-', '').isalnum():
            raise ValueError('Invalid postcode format')
        return v.upper().strip()
    
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


class CustomerCreate(BaseModel):
    """Schema for creating new customers."""
    email_address: Optional[EmailStr] = None
    age: int = Field(..., ge=18, le=100)
    gender: Gender
    lifestage: LifeStage
    home_postcode: str = Field(..., min_length=4, max_length=10)
    
    @validator('home_postcode')
    def validate_postcode(cls, v):
        """Validate postcode format."""
        if not v.replace(' ', '').replace('-', '').isalnum():
            raise ValueError('Invalid postcode format')
        return v.upper().strip()


class CustomerUpdate(BaseModel):
    """Schema for updating existing customers."""
    email_address: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[Gender] = None
    lifestage: Optional[LifeStage] = None
    home_postcode: Optional[str] = Field(None, min_length=4, max_length=10)
    
    @validator('home_postcode')
    def validate_postcode(cls, v):
        """Validate postcode format if provided."""
        if v is not None:
            if not v.replace(' ', '').replace('-', '').isalnum():
                raise ValueError('Invalid postcode format')
            return v.upper().strip()
        return v


class CustomerSummary(BaseModel):
    """Lightweight customer representation for lists."""
    customer_id: UUID
    age: int
    gender: Gender
    lifestage: LifeStage
    home_postcode: str
    created_at: datetime