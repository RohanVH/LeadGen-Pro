"""Location autocomplete API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_google_places_service, get_location_dataset_service
from app.schemas.location import LocationSuggestion, LocationSuggestionsResponse, SelectedLocation
from app.services.google_places import GooglePlacesService
from app.services.location_dataset import LocationDatasetService
from app.utils.location_seeds import LOCATION_SEEDS

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/autocomplete", response_model=LocationSuggestionsResponse)
def autocomplete_locations(
    q: str = Query(..., min_length=2, max_length=120),
    country: str | None = Query(default=None, min_length=2, max_length=120),
    places_service: GooglePlacesService = Depends(get_google_places_service),
) -> LocationSuggestionsResponse:
    """Return location suggestions from Google Places Autocomplete."""
    try:
        predictions = places_service.autocomplete_locations(query=q, country=country)
        suggestions = [
            LocationSuggestion(
                placeId=prediction["place_id"],
                mainText=prediction.get("structured_formatting", {}).get("main_text") or prediction.get("description", ""),
                secondaryText=prediction.get("structured_formatting", {}).get("secondary_text") or "",
            )
            for prediction in predictions
        ]
        return LocationSuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        print("Autocomplete error:", str(e))
        return LocationSuggestionsResponse(suggestions=[])


@router.get("/popular", response_model=LocationSuggestionsResponse)
def popular_locations(
    country: str = Query(..., min_length=2, max_length=120),
    places_service: GooglePlacesService = Depends(get_google_places_service),
    location_dataset_service: LocationDatasetService = Depends(get_location_dataset_service),
) -> LocationSuggestionsResponse:
    """Return popular cities and towns using GeoDB first, then fallbacks."""
    try:
        suggestions: list[LocationSuggestion] = []

        dataset_cities = location_dataset_service.get_cities_by_country(country_name=country)
        if dataset_cities:
            suggestions = [
                LocationSuggestion(
                    placeId=f"dataset:{country}:{item['city']}",
                    mainText=item["city"],
                    secondaryText=", ".join(part for part in [item["state"], item["country"]] if part),
                )
                for item in dataset_cities[:20]
            ]
            return LocationSuggestionsResponse(suggestions=suggestions)

        places = places_service.popular_locations(country=country)
        if places:
            suggestions = [
                LocationSuggestion(
                    placeId=place["place_id"],
                    mainText=place.get("name", ""),
                    secondaryText=place.get("formatted_address", ""),
                )
                for place in places[:20]
            ]
            return LocationSuggestionsResponse(suggestions=suggestions)

        seed_locations = LOCATION_SEEDS.get(country, [])
        suggestions = [
            LocationSuggestion(
                placeId=f"seed:{country}:{city}",
                mainText=city,
                secondaryText=country,
            )
            for city in seed_locations[:20]
        ]
        return LocationSuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        print("Popular locations error:", str(e))
        return LocationSuggestionsResponse(suggestions=[])


@router.get("/details", response_model=SelectedLocation)
async def location_details(
    place_id: str = Query(..., min_length=1, alias="placeId"),
    places_service: GooglePlacesService = Depends(get_google_places_service),
) -> SelectedLocation:
    """Return normalized location details for a chosen suggestion."""
    result = places_service.get_location_details(place_id=place_id)
    components = result.get("address_components", [])

    def find_component(*types: str) -> str | None:
        for component in components:
            component_types = component.get("types", [])
            if any(component_type in component_types for component_type in types):
                return component.get("long_name")
        return None

    city = (
        find_component("locality", "postal_town", "administrative_area_level_2")
        or find_component("sublocality", "neighborhood")
        or result.get("name")
        or ""
    )
    state = find_component("administrative_area_level_1")
    country = find_component("country") or ""
    geometry = result.get("geometry", {}).get("location", {})

    return SelectedLocation(
        city=city,
        state=state,
        country=country,
        lat=geometry.get("lat", 0),
        lng=geometry.get("lng", 0),
        displayName=result.get("formatted_address") or result.get("name") or city,
        placeId=place_id,
    )
