"""Schemas for interactive lead AI analysis and chat."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LeadAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    business_type: str = Field(alias="businessType")
    website_content: str | None = Field(default=None, alias="websiteContent")
    website: str | None = Field(default=None, description="Public website URL if known")
    rating: float | None = None
    reviews: list[str] = Field(default_factory=list)


class LeadAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    overview: str
    strengths: list[str]
    weaknesses: list[str]
    customer_perception: str = Field(alias="customerPerception")
    opportunities: list[str]
    what_to_sell: str = Field(alias="whatToSell")
    outreach_angle: str = Field(alias="outreachAngle")


class LeadChatMessage(BaseModel):
    role: str
    content: str


class LeadContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    business_type: str = Field(alias="businessType")
    website_content: str | None = Field(default=None, alias="websiteContent")
    rating: float | None = None
    reviews: list[str] = Field(default_factory=list)
    overview: str | None = None
    what_to_sell: str | None = Field(default=None, alias="whatToSell")
    outreach_angle: str | None = Field(default=None, alias="outreachAngle")
    email: str | None = None
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    website: str | None = None


class LeadChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    previous_conversation: list[LeadChatMessage] = Field(default_factory=list, alias="previousConversation")
    messages: list[LeadChatMessage] = Field(default_factory=list)
    message: str = ""
    lead_context: LeadContext | None = Field(default=None, alias="leadContext")
    lead: LeadContext | None = None


class LeadChatResponse(BaseModel):
    response: str
