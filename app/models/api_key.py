from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKey(BaseModel):
    """Model for API key records"""
    api_key: str
    api_secret: str
    name: str
    rate_limit: int = Field(default=100, description="Rate limit per minute")
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)


class ApiKeyInDB(ApiKey):
    """Model for API key records in the database"""
    id: str


class ApiKeyCreate(BaseModel):
    """Model for creating a new API key"""
    name: str
    rate_limit: Optional[int] = 100 