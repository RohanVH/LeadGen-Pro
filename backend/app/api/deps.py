"""Dependency providers for API routers."""

from app.core.config import get_settings
from app.services.analyzer import LeadAnalyzerService
from app.services.email_sender import EmailSenderService
from app.services.email_scraper import EmailScraperService
from app.services.google_places import GooglePlacesService
from app.services.lead_service import LeadService
from app.services.lead_ai_assistant import LeadAIAssistantService
from app.services.location_dataset import LocationDatasetService
from app.services.social_discovery import SocialDiscoveryService
from app.services.website_analyzer import WebsiteAnalyzerService


def get_lead_service() -> LeadService:
    """Build lead service with concrete runtime dependencies."""
    settings = get_settings()
    places_service = GooglePlacesService(settings=settings)
    email_scraper_service = EmailScraperService(timeout_seconds=settings.scraper_timeout_seconds)
    website_analyzer_service = WebsiteAnalyzerService(timeout_seconds=settings.scraper_timeout_seconds)
    social_discovery_service = SocialDiscoveryService(timeout_seconds=settings.scraper_timeout_seconds)
    analyzer_service = LeadAnalyzerService(settings=settings)
    return LeadService(
        settings=settings,
        places_service=places_service,
        email_scraper_service=email_scraper_service,
        website_analyzer_service=website_analyzer_service,
        social_discovery_service=social_discovery_service,
        analyzer_service=analyzer_service,
    )


def get_google_places_service() -> GooglePlacesService:
    """Build Google Places service for location APIs."""
    settings = get_settings()
    return GooglePlacesService(settings=settings)


def get_location_dataset_service() -> LocationDatasetService:
    """Build structured location dataset service."""
    settings = get_settings()
    return LocationDatasetService(settings=settings)


def get_email_sender_service() -> EmailSenderService:
    """Build SMTP email sender service for outreach APIs."""
    settings = get_settings()
    return EmailSenderService(settings=settings)


def get_lead_ai_assistant_service() -> LeadAIAssistantService:
    """Build lead AI assistant service for per-lead analysis/chat endpoints."""
    settings = get_settings()
    return LeadAIAssistantService(settings=settings)
