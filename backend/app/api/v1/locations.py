"""Location autocomplete API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_google_places_service, get_location_dataset_service
from app.schemas.location import LocationSuggestion, LocationSuggestionsResponse, SelectedLocation
from app.services.google_places import GooglePlacesService
from app.services.location_dataset import LocationDatasetService
from app.utils.location_seeds import LOCATION_SEEDS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])


def _parse_virtual_place_id(place_id: str) -> tuple[str, str, str] | None:
    parts = place_id.split(":", 2)
    if len(parts) != 3:
        return None
    prefix, country, city = parts
    if prefix not in {"seed", "dataset"} or not country or not city:
        return None
    return prefix, country, city


def _build_fallback_suggestions(
    query: str,
    country: str | None,
    location_dataset_service: LocationDatasetService,
) -> list[dict[str, str]]:
    trimmed = query.strip()
    if len(trimmed) < 2:
        return []

    normalized_query = trimmed.casefold()
    suggestions: list[dict[str, str]] = []
    seen_place_ids: set[str] = set()

    if country:
        dataset_cities = location_dataset_service.get_cities_by_country(country_name=country)
        for item in dataset_cities:
            city = (item.get("city") or "").strip()
            state = (item.get("state") or "").strip()
            item_country = (item.get("country") or country).strip()
            if not city or normalized_query not in city.casefold():
                continue

            place_id = f"dataset:{item_country}:{city}"
            if place_id in seen_place_ids:
                continue

            seen_place_ids.add(place_id)
            suggestions.append(
                {
                    "placeId": place_id,
                    "mainText": city,
                    "secondaryText": ", ".join(part for part in [state, item_country] if part),
                }
            )
            if len(suggestions) >= 8:
                return suggestions

    seed_countries = [country] if country else list(LOCATION_SEEDS.keys())
    for seed_country in seed_countries:
        for city in LOCATION_SEEDS.get(seed_country, []):
            if normalized_query not in city.casefold():
                continue

            place_id = f"seed:{seed_country}:{city}"
            if place_id in seen_place_ids:
                continue

            seen_place_ids.add(place_id)
            suggestions.append(
                {
                    "placeId": place_id,
                    "mainText": city,
                    "secondaryText": seed_country,
                }
            )
            if len(suggestions) >= 8:
                return suggestions

    return suggestions


@router.get("/autocomplete", response_model=LocationSuggestionsResponse)
def autocomplete_locations(
    q: str = Query(..., min_length=2, max_length=120),
    country: str | None = Query(default=None, min_length=2, max_length=120),
    places_service: GooglePlacesService = Depends(get_google_places_service),
    location_dataset_service: LocationDatasetService = Depends(get_location_dataset_service),
) -> LocationSuggestionsResponse:
    """Return location suggestions from Google Places Autocomplete."""
    try:
        predictions = places_service.autocomplete_locations(query=q, country=country)
        if not predictions:
            predictions = _build_fallback_suggestions(
                query=q,
                country=country,
                location_dataset_service=location_dataset_service,
            )
            logger.info("Autocomplete fallback output for q=%r country=%r: %s", q, country, predictions)
        suggestions = [
            LocationSuggestion(
                placeId=str(prediction.get("placeId") or f"unknown:{idx}"),
                mainText=prediction.get("mainText", ""),
                secondaryText=prediction.get("secondaryText", ""),
            )
            for idx, prediction in enumerate(predictions)
            if prediction.get("placeId")
        ]
        logger.info("Autocomplete output for q=%r country=%r: %s", q, country, predictions)
        return LocationSuggestionsResponse(suggestions=suggestions)
    except Exception:
        logger.exception("Autocomplete error for q=%r country=%r", q, country)
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
                    placeId=str(place.get("placeId") or f"unknown:{country}:{place.get('mainText', '')}"),
                    mainText=place.get("mainText", ""),
                    secondaryText=place.get("secondaryText", ""),
                )
                for place in places[:20]
                if place.get("placeId")
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
    except Exception:
        logger.exception("Popular locations error for country=%r", country)
        return LocationSuggestionsResponse(suggestions=[])


@router.get("/details", response_model=SelectedLocation)
async def location_details(
    place_id: str = Query(..., min_length=1, alias="placeId"),
    places_service: GooglePlacesService = Depends(get_google_places_service),
    location_dataset_service: LocationDatasetService = Depends(get_location_dataset_service),
) -> SelectedLocation:
    """Return normalized location details for a chosen suggestion."""
    logger.info("Location details requested for place_id=%s", place_id)
    virtual_place = _parse_virtual_place_id(place_id)

    if virtual_place:
        source, country, city = virtual_place
        logger.info("Resolving virtual location source=%s country=%s city=%s", source, country, city)

        google_matches = places_service.autocomplete_locations(query=city, country=country)
        logger.info("Virtual location autocomplete matches for place_id=%s: %s", place_id, google_matches)

        best_match = next(
            (
                item
                for item in google_matches
                if item.get("placeId")
                and item.get("mainText", "").strip().casefold() == city.strip().casefold()
            ),
            google_matches[0] if google_matches else None,
        )

        if best_match and best_match.get("placeId"):
            result = places_service.get_location_details(place_id=str(best_match["placeId"]))
            logger.info("Virtual location resolved through Google for place_id=%s: %s", place_id, result)
            if result:
                return SelectedLocation(
                    city=result.get("city") or city,
                    state=result.get("state") or "",
                    country=result.get("country") or country,
                    lat=float(result.get("lat") or 0.0),
                    lng=float(result.get("lng") or 0.0),
                    displayName=result.get("displayName") or f"{city}, {country}",
                    placeId=result.get("placeId") or str(best_match["placeId"]),
                )

        dataset_match = next(
            (
                item
                for item in location_dataset_service.get_cities_by_country(country_name=country)
                if (item.get("city") or "").strip().casefold() == city.strip().casefold()
            ),
            None,
        )
        if dataset_match:
            fallback = {
                "city": dataset_match.get("city") or city,
                "state": dataset_match.get("state") or "",
                "country": dataset_match.get("country") or country,
                "lat": float(dataset_match.get("lat") or 0.0),
                "lng": float(dataset_match.get("lng") or 0.0),
                "displayName": ", ".join(
                    part
                    for part in [dataset_match.get("city") or city, dataset_match.get("state"), dataset_match.get("country") or country]
                    if part
                ),
                "placeId": place_id,
            }
            logger.info("Virtual location dataset fallback for place_id=%s: %s", place_id, fallback)
            return SelectedLocation(**fallback)

        fallback = {
            "city": city,
            "state": "",
            "country": country,
            "lat": 0.0,
            "lng": 0.0,
            "displayName": f"{city}, {country}",
            "placeId": place_id,
        }
        logger.info("Virtual location seed fallback for place_id=%s: %s", place_id, fallback)
        return SelectedLocation(**fallback)

    result = places_service.get_location_details(place_id=place_id)
    logger.info("Location details API response for place_id=%s: %s", place_id, result)

    if not result:
        fallback = {
            "city": "",
            "state": "",
            "country": "",
            "lat": 0.0,
            "lng": 0.0,
            "displayName": "",
            "placeId": place_id,
        }
        logger.info("Location details empty fallback for place_id=%s: %s", place_id, fallback)
        return SelectedLocation(**fallback)

    return SelectedLocation(**result)
