import { memo, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

function SearchableSelect({
  label,
  name,
  placeholder,
  options,
  value,
  onChange,
  disabled = false,
  required = false,
  loading = false,
  showCategory = false,
  allowCustomValue = false,
  debounceMs = 0,
  suggestionResolver = null,
  hint = "",
}) {
  const baseId = useId();
  const inputId = `${baseId}-input`;
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const rootRef = useRef(null);

  const selectedLabel = useMemo(() => {
    const selected = options.find((option) => option.value === value);
    return selected?.label || value || "";
  }, [options, value]);

  useEffect(() => {
    if (!open) {
      setQuery(selectedLabel);
    }
  }, [open, selectedLabel]);

  useEffect(() => {
    if (!debounceMs) {
      setDebouncedQuery(query);
      return undefined;
    }
    const timer = window.setTimeout(() => setDebouncedQuery(query), debounceMs);
    return () => window.clearTimeout(timer);
  }, [debounceMs, query]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = useMemo(() => {
    const keyword = debouncedQuery.trim().toLowerCase();
    if (typeof suggestionResolver === "function") {
      return suggestionResolver(keyword, options);
    }
    if (!keyword) {
      return options.slice(0, 30);
    }
    return options.filter((option) => option.label.toLowerCase().includes(keyword));
  }, [debouncedQuery, options, suggestionResolver]);

  const highlightMatch = useCallback(
    (text) => {
      const keyword = query.trim();
      if (!keyword) {
        return text;
      }

      const lowerText = text.toLowerCase();
      const lowerKeyword = keyword.toLowerCase();
      const matchIndex = lowerText.indexOf(lowerKeyword);

      if (matchIndex === -1) {
        return text;
      }

      const before = text.slice(0, matchIndex);
      const match = text.slice(matchIndex, matchIndex + keyword.length);
      const after = text.slice(matchIndex + keyword.length);

      return (
        <>
          {before}
          <span className="rounded bg-cyan-100 px-0.5 text-slate-900">{match}</span>
          {after}
        </>
      );
    },
    [query]
  );

  const handleInputChange = useCallback((event) => {
    const nextValue = event.target.value;
    setQuery(nextValue);
    if (allowCustomValue) {
      onChange(nextValue);
    }
    if (!open) setOpen(true);
  }, [allowCustomValue, onChange, open]);

  const handleBlurCommit = useCallback(() => {
    if (!allowCustomValue) {
      return;
    }
    onChange(query.trim());
  }, [allowCustomValue, onChange, query]);

  const handleSelect = useCallback((option) => {
    onChange(option.value);
    setQuery(option.label);
    setOpen(false);
  }, [onChange]);

  return (
    <div ref={rootRef} className="relative">
      <label
        htmlFor={inputId}
        className="mb-1 block text-sm font-semibold text-slate-700 dark:text-slate-200"
      >
        {label} {required ? <span className="text-rose-600">*</span> : null}
      </label>
      <input
        id={inputId}
        name={name || undefined}
        autoComplete="off"
        value={open ? query : selectedLabel}
        onChange={handleInputChange}
        onFocus={() => setOpen(true)}
        onBlur={handleBlurCommit}
        disabled={disabled}
        placeholder={placeholder}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-colors duration-200 focus:ring-2 disabled:cursor-not-allowed disabled:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:disabled:bg-slate-800"
      />
      {hint ? <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">{hint}</p> : null}

      <div
        role="listbox"
        className={`absolute z-50 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg transition-colors duration-200 dark:border-slate-700 dark:bg-slate-900 ${
          open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        {loading ? (
          <div className="flex items-center gap-2 px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            Loading options...
          </div>
        ) : filteredOptions.length ? (
          filteredOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSelect(option)}
              className="block w-full px-3 py-2 text-left text-sm text-slate-700 transition-colors duration-200 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <span className="block font-medium">{highlightMatch(option.label)}</span>
              {showCategory && option.category ? (
                <span className="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">{option.category}</span>
              ) : null}
            </button>
          ))
        ) : (
          <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">No matching options</div>
        )}
      </div>
    </div>
  );
}

export default memo(SearchableSelect);
