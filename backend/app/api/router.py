"""Top-level API router."""

from fastapi import APIRouter

from app.api.v1.leads import router as leads_router
from app.api.v1.locations import router as locations_router
from app.api.v1.outreach import router as outreach_router

api_router = APIRouter()
api_router.include_router(leads_router)
api_router.include_router(locations_router)
api_router.include_router(outreach_router)
