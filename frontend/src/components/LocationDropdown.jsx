import { memo, useEffect, useId, useMemo, useRef, useState } from "react";
import {
  fetchLocationDetails,
  fetchLocationSuggestions,
  fetchPopularLocations,
} from "../services/leadService";
import { LOCATION_SEEDS } from "../services/locationSeeds";

function SectionHeader({ title }) {
  return (
    <div className="border-b border-slate-100 px-3 py-2 dark:border-slate-800">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{title}</p>
    </div>
  );
}

function LocationDropdown({ country, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [popularLocations, setPopularLocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const rootRef = useRef(null);
  const searchCacheRef = useRef(new Map());
  const popularCacheRef = useRef(new Map());
  const detailsCacheRef = useRef(new Map());
  const baseId = useId();
  const locationInputId = `${baseId}-location`;

  const displayValue = useMemo(() => {
    if (open) {
      return query;
    }
    return value?.displayName || "";
  }, [open, query, value]);

  const fallbackSeedItems = useMemo(() => {
    const seeds = LOCATION_SEEDS[country] || [];
    return seeds.slice(0, 8).map((name) => ({
      placeId: `seed:${country}:${name}`,
      mainText: name,
      secondaryText: country,
      isSeed: true,
    }));
  }, [country]);

  const activePopularItems = useMemo(() => {
    if (popularLocations.length) {
      return popularLocations.slice(0, 10);
    }
    return fallbackSeedItems;
  }, [fallbackSeedItems, popularLocations]);

  const visibleSuggestions = useMemo(() => suggestions.slice(0, 8), [suggestions]);

  useEffect(() => {
    if (!open) {
      setQuery(value?.displayName || "");
    }
  }, [open, value]);

  useEffect(() => {
    setQuery("");
    setSuggestions([]);
    setPopularLocations([]);
    setError("");
    setLoading(false);
  }, [country]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!country || !open || query.trim().length > 0) {
      return;
    }

    const cachedPopular = popularCacheRef.current.get(country);
    if (cachedPopular) {
      setPopularLocations(cachedPopular);
      return;
    }

    let active = true;
    setLoading(true);
    setError("");

    const loadPopularLocations = async () => {
      try {
        const results = await fetchPopularLocations(country);
        if (!active) {
          return;
        }
        popularCacheRef.current.set(country, results);
        setPopularLocations(results);
      } catch {
        if (!active) {
          return;
        }
        setPopularLocations([]);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadPopularLocations();

    return () => {
      active = false;
    };
  }, [country, open, query]);

  useEffect(() => {
    if (!country) {
      setSuggestions([]);
      setQuery("");
      setLoading(false);
      return;
    }

    const trimmed = query.trim();
    if (!open || trimmed.length < 2) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    const cacheKey = `${country}:${trimmed.toLowerCase()}`;
    const cached = searchCacheRef.current.get(cacheKey);
    if (cached) {
      setSuggestions(cached);
      setError("");
      return;
    }

    let active = true;
    setLoading(true);
    setError("");

    const timer = setTimeout(async () => {
      try {
        const results = await fetchLocationSuggestions({ query: trimmed, country });
        if (!active) {
          return;
        }
        const limitedResults = results.slice(0, 8);
        searchCacheRef.current.set(cacheKey, limitedResults);
        setSuggestions(limitedResults);
      } catch (nextError) {
        if (!active) {
          return;
        }
        setSuggestions([]);
        setError(nextError.message || "Unable to load locations.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [country, open, query]);

  const handleSelect = async (suggestion) => {
    setLoading(true);
    setError("");

    try {
      let resolvedPlaceId = suggestion.placeId;

      if (suggestion.isSeed || suggestion.placeId.startsWith("dataset:")) {
        const seedCacheKey = `${country}:${suggestion.mainText}`;
        const cachedDetails = detailsCacheRef.current.get(seedCacheKey);
        if (cachedDetails) {
          onChange(cachedDetails);
          setQuery(cachedDetails.displayName);
          setOpen(false);
          return;
        }

        const results = await fetchLocationSuggestions({
          query: suggestion.mainText,
          country,
        });
        const bestMatch = results[0];
        if (!bestMatch) {
          setError("Type to search more locations");
          return;
        }
        resolvedPlaceId = bestMatch.placeId;
      }

      const details = await fetchLocationDetails(resolvedPlaceId);
      if (suggestion.isSeed || suggestion.placeId.startsWith("dataset:")) {
        detailsCacheRef.current.set(`${country}:${suggestion.mainText}`, details);
      }
      onChange(details);
      setQuery(details.displayName);
      setOpen(false);
    } catch (nextError) {
      setError(nextError.message || "Unable to select this location.");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (event) => {
    const nextValue = event.target.value;
    setQuery(nextValue);
    if (value && nextValue !== value.displayName) {
      onChange(null);
    }
    if (!open) {
      setOpen(true);
    }
  };

  return (
    <div ref={rootRef} className="relative">
      <label
        htmlFor={locationInputId}
        className="mb-1 block text-sm font-semibold text-slate-700 dark:text-slate-200"
      >
        Location <span className="text-rose-600">*</span>
      </label>
      <input
        id={locationInputId}
        name="location"
        autoComplete="off"
        value={displayValue}
        onChange={handleInputChange}
        onFocus={() => setOpen(true)}
        disabled={!country}
        placeholder="Search or select location (city, area, town)"
        aria-expanded={open}
        aria-haspopup="listbox"
        className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm text-slate-900 outline-none transition-colors duration-200 focus:ring-2 disabled:cursor-not-allowed disabled:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:disabled:bg-slate-800"
      />
      <span className="pointer-events-none absolute left-3 top-[38px] text-slate-400 dark:text-slate-500" aria-hidden="true">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 21s6-5.8 6-11a6 6 0 1 0-12 0c0 5.2 6 11 6 11Z" />
          <circle cx="12" cy="10" r="2.5" />
        </svg>
      </span>

      <div
        role="listbox"
        className={`absolute z-50 mt-2 max-h-80 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl transition-all duration-150 dark:border-slate-700 dark:bg-slate-900 ${
          open ? "pointer-events-auto translate-y-0 opacity-100" : "pointer-events-none -translate-y-1 opacity-0"
        }`}
      >
        {!country ? (
          <div className="px-3 py-3 text-sm text-slate-500 dark:text-slate-400">Select a country first</div>
        ) : loading ? (
          <div className="flex items-center gap-2 px-3 py-3 text-sm text-slate-500 dark:text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            Finding locations...
          </div>
        ) : error ? (
          <div className="px-3 py-3 text-sm text-rose-600">{error}</div>
        ) : query.trim().length === 0 && activePopularItems.length ? (
          <>
            <SectionHeader title="Popular locations" />
            {activePopularItems.map((suggestion) => (
              <button
                key={suggestion.placeId}
                type="button"
                onClick={() => handleSelect(suggestion)}
                className="block w-full px-3 py-3 text-left transition-colors duration-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <span className="block text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {suggestion.mainText} <span className="font-normal text-slate-500 dark:text-slate-400">- {suggestion.secondaryText}</span>
                </span>
              </button>
            ))}
          </>
        ) : query.trim().length >= 2 && visibleSuggestions.length ? (
          <>
            <SectionHeader title="Search results" />
            {visibleSuggestions.map((suggestion) => (
              <button
                key={suggestion.placeId}
                type="button"
                onClick={() => handleSelect(suggestion)}
                className="block w-full px-3 py-3 text-left transition-colors duration-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <span className="block text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {suggestion.mainText} <span className="font-normal text-slate-500 dark:text-slate-400">- {suggestion.secondaryText}</span>
                </span>
              </button>
            ))}
          </>
        ) : (
          <div className="px-3 py-3 text-sm text-slate-500 dark:text-slate-400">Type to search more locations</div>
        )}
      </div>
    </div>
  );
}

export default memo(LocationDropdown);
