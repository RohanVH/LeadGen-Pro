"""Schemas for interactive lead AI analysis and chat."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LeadAnalyzeRequest(BaseModel):
    name: str
    business_type: str = Field(alias="businessType")
    website_content: str | None = Field(default=None, alias="websiteContent")
    rating: float | None = None
    reviews: list[str] = Field(default_factory=list)


class LeadAnalyzeResponse(BaseModel):
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
    name: str
    business_type: str = Field(alias="businessType")
    website_content: str | None = Field(default=None, alias="websiteContent")
    rating: float | None = None
    reviews: list[str] = Field(default_factory=list)
    overview: str | None = None
    what_to_sell: str | None = Field(default=None, alias="whatToSell")


class LeadChatRequest(BaseModel):
    previous_conversation: list[LeadChatMessage] = Field(default_factory=list, alias="previousConversation")
    message: str
    lead_context: LeadContext = Field(alias="leadContext")


class LeadChatResponse(BaseModel):
    response: str
