import { memo, useEffect, useMemo, useState } from "react";
import SearchableSelect from "./SearchableSelect";
import { CITIES_BY_COUNTRY } from "../services/searchOptions";

function CitySelect({ country, value, onChange }) {
  const [loadingCities, setLoadingCities] = useState(false);

  useEffect(() => {
    if (!country) {
      setLoadingCities(false);
      return;
    }
    setLoadingCities(true);
    const timer = setTimeout(() => setLoadingCities(false), 300);
    return () => clearTimeout(timer);
  }, [country]);

  const options = useMemo(() => {
    const cities = CITIES_BY_COUNTRY[country] || [];
    return cities.map((city) => ({ label: city, value: city }));
  }, [country]);

  return (
    <SearchableSelect
      label="City"
      placeholder="Select city"
      options={options}
      value={value}
      onChange={onChange}
      disabled={!country}
      required
      loading={loadingCities}
    />
  );
}

export default memo(CitySelect);
