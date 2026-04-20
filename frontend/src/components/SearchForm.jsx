import { useCallback, useMemo, useState } from "react";
import BusinessTypeSelect from "./BusinessTypeSelect";
import CountrySelect from "./CountrySelect";
import LocationDropdown from "./LocationDropdown";

const initialForm = {
  category: "",
  city: "",
  type: "",
  country: "",
  state: "",
  lat: null,
  lng: null,
  displayName: "",
  placeId: "",
};

function SearchForm({ onSearch, loading, loadingStage }) {
  const [form, setForm] = useState(initialForm);

  const setCategory = useCallback((category) => {
    setForm((prev) => ({
      ...prev,
      category,
      type: "",
    }));
  }, []);

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
    return Boolean(form.category && form.type && form.country && form.city) && !loading;
  }, [form.category, form.type, form.country, form.city, loading]);

  return (
    <form
      onSubmit={onSubmit}
      className="relative grid gap-5 rounded-2xl border border-slate-200/90 bg-white/80 p-5 shadow-glow backdrop-blur-sm transition-colors duration-200 dark:border-slate-700/90 dark:bg-slate-900/70 sm:grid-cols-12 sm:p-6"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-400/40 to-transparent dark:via-indigo-500/30" />

      <div className="sm:col-span-12">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100 dark:bg-indigo-950/50 dark:text-indigo-300 dark:ring-indigo-900/60" aria-hidden="true">
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="11" cy="11" r="6" />
                <path d="m20 20-3.5-3.5" />
              </svg>
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Search criteria</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Category, location, and one click to run.</p>
            </div>
          </div>
          <div
            className={`min-h-[1.25rem] overflow-hidden text-xs font-semibold text-indigo-600 transition-all duration-300 dark:text-indigo-300 ${
              loading ? "max-h-8 opacity-100" : "max-h-0 opacity-0"
            }`}
            aria-live="polite"
          >
            {loadingStage || "Fetching leads..."}
          </div>
        </div>
      </div>

      <div className="sm:col-span-5">
        <BusinessTypeSelect
          category={form.category}
          onCategoryChange={setCategory}
          value={form.type}
          onChange={setType}
        />
      </div>

      <div className="sm:col-span-2">
        <CountrySelect value={form.country} onChange={setCountry} />
      </div>

      <div className="sm:col-span-4">
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
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-500/25 transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300 disabled:shadow-none disabled:hover:translate-y-0 dark:disabled:bg-indigo-900"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="11" cy="11" r="6" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          {loading ? loadingStage || "Fetching leads..." : "Search"}
        </button>
      </div>
    </form>
  );
}

export default SearchForm;
