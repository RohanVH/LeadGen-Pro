import { memo, useMemo } from "react";
import SearchableSelect from "./SearchableSelect";
import { AREAS_BY_CITY } from "../services/searchOptions";

function AreaSelect({ city, value, onChange }) {
  const options = useMemo(() => {
    const areas = AREAS_BY_CITY[city] || [];
    return areas.map((area) => ({ label: area, value: area }));
  }, [city]);

  return (
    <SearchableSelect
      label="Area / Locality"
      placeholder="Select area (optional)"
      options={options}
      value={value}
      onChange={onChange}
      disabled={!city}
    />
  );
}

export default memo(AreaSelect);
