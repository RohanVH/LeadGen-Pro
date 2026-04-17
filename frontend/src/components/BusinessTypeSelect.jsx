import { memo, useMemo } from "react";
import SearchableSelect from "./SearchableSelect";
import { BUSINESS_TYPE_OPTIONS } from "../services/searchOptions";

function BusinessTypeSelect({ value, onChange }) {
  const options = useMemo(() => BUSINESS_TYPE_OPTIONS, []);

  return (
    <SearchableSelect
      label="Business Type"
      placeholder="Search business type (e.g., Dental Clinic, Salon)"
      options={options}
      value={value}
      onChange={onChange}
      required
      showCategory
    />
  );
}

export default memo(BusinessTypeSelect);
