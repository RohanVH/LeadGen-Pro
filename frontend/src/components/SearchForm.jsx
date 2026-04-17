import { useCallback, useMemo, useState } from "react";
import BusinessTypeSelect from "./BusinessTypeSelect";
import CountrySelect from "./CountrySelect";
import LocationDropdown from "./LocationDropdown";

const initialForm = {
  city: "",
  type: "",
  country: "",
  state: "",
  lat: null,
  lng: null,
  displayName: "",
  placeId: "",
};

function SearchForm({ onSearch, loading }) {
  const [form, setForm] = useState(initialForm);

  const setType = useCallback((type) => {
    setForm((prev) => ({ ...prev, type }));
  }, []);

  const setCountry = useCallback((country) => {
    setForm((prev) => ({
      ...prev,
      country,
      city: "",
      state: "",
      lat: null,
      lng: null,
      displayName: "",
      placeId: "",
    }));
  }, []);

  const setLocation = useCallback((location) => {
    if (!location) {
      setForm((prev) => ({
        ...prev,
        city: "",
        state: "",
        lat: null,
        lng: null,
        displayName: "",
        placeId: "",
      }));
      return;
    }

    setForm((prev) => ({
      ...prev,
      city: location.city || "",
      state: location.state || "",
      country: location.country || prev.country,
      lat: location.lat,
      lng: location.lng,
      displayName: location.displayName || "",
      placeId: location.placeId || "",
    }));
  }, []);

  const onSubmit = (event) => {
    event.preventDefault();
    onSearch(form);
  };

  const canSearch = useMemo(() => {
    return Boolean(form.type && form.country && form.city) && !loading;
  }, [form.type, form.country, form.city, loading]);

  return (
    <form
      onSubmit={onSubmit}
      className="grid gap-4 rounded-xl border border-slate-200 bg-gray-50 p-5 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800 sm:grid-cols-12"
    >
      <div className="sm:col-span-12">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 dark:text-slate-400" aria-hidden="true">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="11" cy="11" r="6" />
              <path d="m20 20-3.5-3.5" />
            </svg>
          </span>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Lead Search</p>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Structured search for cleaner, location-accurate lead generation.
        </p>
      </div>

      <div className="sm:col-span-3">
        <BusinessTypeSelect value={form.type} onChange={setType} />
      </div>

      <div className="sm:col-span-3">
        <CountrySelect value={form.country} onChange={setCountry} />
      </div>

      <div className="sm:col-span-5">
        <LocationDropdown
          country={form.country}
          value={
            form.placeId
              ? {
                  city: form.city,
                  state: form.state,
                  country: form.country,
                  lat: form.lat,
                  lng: form.lng,
                  displayName: form.displayName,
                  placeId: form.placeId,
                }
              : null
          }
          onChange={setLocation}
        />
      </div>

      <div className="sm:col-span-1 sm:self-end">
        <button
          type="submit"
          disabled={!canSearch}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors duration-200 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300 dark:disabled:bg-indigo-900"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="11" cy="11" r="6" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
    </form>
  );
}

export default SearchForm;
