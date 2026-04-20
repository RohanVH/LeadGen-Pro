import { memo, useEffect, useMemo, useRef, useState } from "react";
import SearchableSelect from "./SearchableSelect";
import { suggestBusinessTypes } from "../services/leadService";
import { BUSINESS_CATEGORY_OPTIONS, BUSINESS_TYPES_BY_CATEGORY } from "../services/businessTypes";
import { getBusinessTypeSuggestions } from "../utils/businessType";

function BusinessTypeSelect({ category, onCategoryChange, value, onChange }) {
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const cacheRef = useRef(new Map());

  const categoryOptions = useMemo(() => BUSINESS_CATEGORY_OPTIONS, []);
  const subtypeOptions = useMemo(() => {
    if (!category) {
      return [];
    }
    return (BUSINESS_TYPES_BY_CATEGORY[category] || []).map((item) => ({
      label: item,
      value: item,
      category,
    }));
  }, [category]);

  const mergedOptions = useMemo(() => {
    const seen = new Set();
    const base = [];
    for (const option of subtypeOptions) {
      const key = option.value.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      base.push(option);
    }
    for (const suggestion of aiSuggestions) {
      const key = suggestion.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      base.push({ label: suggestion, value: suggestion, category: "AI suggestion" });
    }
    return base;
  }, [aiSuggestions, subtypeOptions]);

  const suggestionResolver = useMemo(() => {
    return (keyword, availableOptions) => getBusinessTypeSuggestions(keyword, availableOptions);
  }, []);

  useEffect(() => {
    if (!category) {
      setAiSuggestions([]);
      setAiLoading(false);
      return;
    }
    const typed = (value || "").trim();
    if (!typed) {
      setAiSuggestions([]);
      setAiLoading(false);
      return;
    }

    const localMatches = subtypeOptions.filter((option) => {
      const label = option.label.toLowerCase();
      const query = typed.toLowerCase();
      return label.includes(query) || label.startsWith(query);
    });
    if (localMatches.length > 0) {
      setAiSuggestions([]);
      setAiLoading(false);
      return;
    }

    const cacheKey = `${category.toLowerCase()}|${typed.toLowerCase()}`;
    if (cacheRef.current.has(cacheKey)) {
      setAiSuggestions(cacheRef.current.get(cacheKey));
      setAiLoading(false);
      return;
    }

    setAiLoading(true);
    const timer = window.setTimeout(async () => {
      try {
        const response = await suggestBusinessTypes({ query: typed, category });
        const suggestions = Array.isArray(response?.suggestions) ? response.suggestions : [];
        cacheRef.current.set(cacheKey, suggestions);
        setAiSuggestions(suggestions);
      } catch {
        setAiSuggestions([]);
      } finally {
        setAiLoading(false);
      }
    }, 500);

    return () => window.clearTimeout(timer);
  }, [category, subtypeOptions, value]);

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <SearchableSelect
        label="Category"
        name="businessCategory"
        placeholder="Select business category"
        options={categoryOptions}
        value={category}
        onChange={onCategoryChange}
        required
      />
      <div>
        <SearchableSelect
          label="Sub-type"
          name="businessSubtype"
          placeholder={
            category ? "Select or type sub-type (e.g. cafe, dental clinic)" : "Select category first"
          }
          options={mergedOptions}
          value={value}
          onChange={onChange}
          required
          showCategory
          allowCustomValue
          disabled={!category}
          debounceMs={300}
          suggestionResolver={suggestionResolver}
          hint={category ? "Select suggestion or type your own. Press Enter to search." : "Category is required first"}
          loading={aiLoading}
        />
      </div>
    </div>
  );
}

export default memo(BusinessTypeSelect);
