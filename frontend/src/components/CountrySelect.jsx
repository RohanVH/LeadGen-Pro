import { memo, useMemo } from "react";
import SearchableSelect from "./SearchableSelect";
import { COUNTRY_OPTIONS } from "../services/searchOptions";

function CountrySelect({ value, onChange }) {
  const options = useMemo(() => COUNTRY_OPTIONS, []);

  return (
    <SearchableSelect
      label="Country"
      name="country"
      placeholder="Select country"
      options={options}
      value={value}
      onChange={onChange}
      required
    />
  );
}

export default memo(CountrySelect);
