"""Schemas for AI-assisted business type suggestions."""

from pydantic import BaseModel, Field


class BusinessTypeSuggestRequest(BaseModel):
    query: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=120)


class BusinessTypeSuggestResponse(BaseModel):
    suggestions: list[str]
