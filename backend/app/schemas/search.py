"""Search query schemas for lead generation."""

from pydantic import BaseModel, Field


class LeadSearchParams(BaseModel):
    """Validated lead search parameters."""

    city: str = Field(min_length=2, max_length=120)
    business_type: str = Field(min_length=2, max_length=120, alias="type")
    country: str | None = Field(default=None, min_length=2, max_length=120)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=150, ge=1, le=300)

