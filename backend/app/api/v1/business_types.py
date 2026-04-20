"""Business type AI suggestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_business_type_suggester_service
from app.schemas.business_types import BusinessTypeSuggestRequest, BusinessTypeSuggestResponse
from app.services.business_type_suggester import BusinessTypeSuggesterService

router = APIRouter(prefix="/v1/business-types", tags=["business-types"])


@router.post("/suggest", response_model=BusinessTypeSuggestResponse)
async def suggest_business_types(
    payload: BusinessTypeSuggestRequest,
    suggester: BusinessTypeSuggesterService = Depends(get_business_type_suggester_service),
) -> BusinessTypeSuggestResponse:
    """Suggest related sub-types using Gemini as a support layer."""
    suggestions = await suggester.suggest(query=payload.query, category=payload.category)
    return BusinessTypeSuggestResponse(suggestions=suggestions)
