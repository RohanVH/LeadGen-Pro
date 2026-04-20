"""Pydantic schemas for lead resources."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Lead(BaseModel):
    """Represents a generated business lead."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str
    place_id: str | None = Field(default=None, alias="placeId")
    address: str | None = None
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    website: str | None = None
    instagram_url: str | None = Field(default=None, alias="instagramUrl")
    youtube_url: str | None = Field(default=None, alias="youtubeUrl")
    website_content: str | None = Field(default=None, alias="websiteContent")
    email: str | None = None
    email_source: str = Field(default="missing", alias="emailSource")
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
    rating: float | None = None
    review_count: int = Field(default=0, alias="reviewCount")
    google_reviews: list[str] = Field(default_factory=list, alias="googleReviews")
    business_summary: str = Field(default="Not available", alias="businessSummary")
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    customer_sentiment: Literal["positive", "neutral", "negative"] = Field(default="neutral", alias="customerSentiment")
    recommended_action: Literal["contact", "skip", "manual review"] = Field(
        default="manual review",
        alias="recommendedAction",
    )
    pitch_suggestion: str = Field(default="Not available", alias="pitchSuggestion")


class LeadSearchResponse(BaseModel):
    """Response payload for lead search endpoint."""

    total: int
    leads: list[Lead]
    has_more: bool = Field(alias="hasMore")
