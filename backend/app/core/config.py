"""Application configuration and settings."""

import os
from functools import lru_cache
from typing import List

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="LeadGen Pro API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    vercel_url: str = Field(default="", alias="VERCEL_URL")
    vercel_branch_url: str = Field(default="", alias="VERCEL_BRANCH_URL")
    vercel_project_production_url: str = Field(default="", alias="VERCEL_PROJECT_PRODUCTION_URL")

    google_places_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_PLACES_API_KEY", "GOOGLE_API_KEY"),
    )
    google_places_text_search_url: str = Field(
        default="https://maps.googleapis.com/maps/api/place/textsearch/json",
        alias="GOOGLE_PLACES_TEXT_SEARCH_URL",
    )
    google_places_details_url: str = Field(
        default="https://maps.googleapis.com/maps/api/place/details/json",
        alias="GOOGLE_PLACES_DETAILS_URL",
    )
    google_places_autocomplete_url: str = Field(
        default="https://maps.googleapis.com/maps/api/place/autocomplete/json",
        alias="GOOGLE_PLACES_AUTOCOMPLETE_URL",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    lead_max_results: int = Field(default=12, alias="LEAD_MAX_RESULTS")
    scraper_max_concurrency: int = Field(default=6, alias="SCRAPER_MAX_CONCURRENCY")
    scraper_timeout_seconds: int = Field(default=6, alias="SCRAPER_TIMEOUT_SECONDS")
    email_host: str = Field(default="", alias="EMAIL_HOST")
    email_port: int = Field(default=587, alias="EMAIL_PORT")
    email_user: str = Field(default="", alias="EMAIL_USER")
    email_pass: str = Field(default="", alias="EMAIL_PASS")
    geodb_api_key: str = Field(default="", alias="GEODB_API_KEY")
    geodb_api_host: str = Field(default="wft-geo-db.p.rapidapi.com", alias="GEODB_API_HOST")
    geodb_countries_url: str = Field(
        default="https://wft-geo-db.p.rapidapi.com/v1/geo/countries",
        alias="GEODB_COUNTRIES_URL",
    )
    geodb_cities_url: str = Field(
        default="https://wft-geo-db.p.rapidapi.com/v1/geo/countries/{country_code}/cities",
        alias="GEODB_CITIES_URL",
    )

    @property
    def frontend_origins(self) -> List[str]:
        """Return normalized frontend origins for CORS configuration."""
        origins: list[str] = [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

        for host in (
            self.vercel_url,
            self.vercel_branch_url,
            self.vercel_project_production_url,
        ):
            if host:
                origins.append(f"https://{host.strip()}")

        seen: set[str] = set()
        normalized: list[str] = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                normalized.append(origin)

        return normalized


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    if os.getenv("VERCEL") and not os.getenv("APP_ENV"):
        os.environ["APP_ENV"] = "production"
    return Settings()
