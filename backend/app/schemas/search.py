"""Search query schemas for lead generation."""

from pydantic import BaseModel, Field


class LeadSearchParams(BaseModel):
    """Validated lead search parameters."""

    city: str = Field(min_length=2, max_length=120)
    business_type: str = Field(min_length=2, max_length=120, alias="type")
    country: str | None = Field(default=None, min_length=2, max_length=120)

