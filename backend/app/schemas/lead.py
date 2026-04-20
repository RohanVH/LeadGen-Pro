"""Pydantic schemas for lead resources."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Lead(BaseModel):
    """Represents a generated business lead."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str
    address: str | None = None
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    website: str | None = None
    email: str | None = None
    email_type: Literal["owner", "founder", "name", "info", "contact", "hello", "generated", "missing"] = Field(
        default="missing",
        alias="emailType",
    )
    email_confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="LOW", alias="emailConfidence")
    city: str | None = None
    business_type: str | None = Field(default=None, alias="businessType")
    priority_score: Literal["HIGH", "MEDIUM", "LOW"] = Field(alias="priorityScore")
    is_hot_lead: bool = Field(default=False, alias="isHotLead")
    website_quality: Literal["NO_WEBSITE", "WEAK_WEBSITE", "GOOD_WEBSITE"] = Field(alias="websiteQuality")


class LeadSearchResponse(BaseModel):
    """Response payload for lead search endpoint."""

    total: int
    leads: list[Lead]
