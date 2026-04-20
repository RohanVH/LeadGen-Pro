import { memo, useMemo } from "react";
import SearchableSelect from "./SearchableSelect";
import { BUSINESS_TYPE_OPTIONS } from "../services/searchOptions";
import { getBusinessTypeSuggestions } from "../utils/businessType";

function BusinessTypeSelect({ value, onChange }) {
  const options = useMemo(() => BUSINESS_TYPE_OPTIONS, []);
  const suggestionResolver = useMemo(
    () => (keyword, availableOptions) => getBusinessTypeSuggestions(keyword, availableOptions),
    []
  );

  return (
    <SearchableSelect
      label="Business Type"
      placeholder="Search business type (e.g. salon, dentist, clothing store)"
      options={options}
      value={value}
      onChange={onChange}
      required
      showCategory
      allowCustomValue
      debounceMs={300}
      suggestionResolver={suggestionResolver}
      hint="Press Enter to search"
    />
  );
}

export default memo(BusinessTypeSelect);
