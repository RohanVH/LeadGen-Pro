"""Lead-related API routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_lead_service
from app.schemas.lead import LeadSearchResponse
from app.schemas.search import LeadSearchParams
from app.services.lead_service import LeadService
from app.utils.csv_exporter import leads_to_csv

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/search", response_model=LeadSearchResponse)
async def search_leads(
    city: str = Query(..., min_length=2, max_length=120),
    type: str = Query(..., min_length=2, max_length=120),
    country: str | None = Query(default=None, min_length=2, max_length=120),
    lead_service: LeadService = Depends(get_lead_service),
) -> LeadSearchResponse:
    """Search leads by city and business type."""
    params = LeadSearchParams(city=city, type=type, country=country)
    leads = await lead_service.search(
        city=params.city,
        business_type=params.business_type,
        country=params.country,
    )
    return LeadSearchResponse(total=len(leads), leads=leads)


@router.get("/export")
async def export_leads_csv(
    city: str = Query(..., min_length=2, max_length=120),
    type: str = Query(..., min_length=2, max_length=120),
    country: str | None = Query(default=None, min_length=2, max_length=120),
    lead_service: LeadService = Depends(get_lead_service),
) -> StreamingResponse:
    """Export searched leads as CSV."""
    params = LeadSearchParams(city=city, type=type, country=country)
    leads = await lead_service.search(
        city=params.city,
        business_type=params.business_type,
        country=params.country,
    )
    csv_content = leads_to_csv(leads)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"leads-{params.city.lower().replace(' ', '-')}-{timestamp}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

