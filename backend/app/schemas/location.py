"""Schemas for location autocomplete and selection."""

from pydantic import BaseModel, ConfigDict, Field


class LocationSuggestion(BaseModel):
    """Autocomplete suggestion returned to the frontend."""

    place_id: str = Field(alias="placeId")
    main_text: str = Field(alias="mainText")
    secondary_text: str = Field(alias="secondaryText")

    model_config = ConfigDict(populate_by_name=True)


class LocationSuggestionsResponse(BaseModel):
    """Suggestion collection wrapper."""

    suggestions: list[LocationSuggestion]


class SelectedLocation(BaseModel):
    """Normalized location details for a selected suggestion."""

    city: str
    state: str | None = None
    country: str
    lat: float
    lng: float
    display_name: str = Field(alias="displayName")
    place_id: str = Field(alias="placeId")

    model_config = ConfigDict(populate_by_name=True)

