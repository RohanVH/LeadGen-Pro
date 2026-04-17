const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "/api");

const buildQuery = (params) => {
  const searchParams = new URLSearchParams();
  searchParams.set("city", params.city);
  searchParams.set("type", params.type);
  if (params.country) {
    searchParams.set("country", params.country);
  }
  return searchParams.toString();
};

export async function searchLeads(params) {
  const queryString = buildQuery(params);
  const response = await fetch(`${API_BASE_URL}/leads/search?${queryString}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail || "Unable to fetch leads.");
  }

  return payload;
}

export function exportLeadsCsv(params) {
  const queryString = buildQuery(params);
  window.open(`${API_BASE_URL}/leads/export?${queryString}`, "_blank");
}

export async function sendOutreachEmail(payload) {
  const response = await fetch(`${API_BASE_URL}/outreach/send-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Unable to send outreach email.");
  }

  return data;
}

export async function fetchLocationSuggestions({ query, country }) {
  const searchParams = new URLSearchParams();
  searchParams.set("q", query);
  if (country) {
    searchParams.set("country", country);
  }

  const response = await fetch(`${API_BASE_URL}/locations/autocomplete?${searchParams.toString()}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail || "Unable to fetch location suggestions.");
  }

  return payload.suggestions ?? [];
}

export async function fetchPopularLocations(country) {
  const searchParams = new URLSearchParams();
  searchParams.set("country", country);

  const response = await fetch(`${API_BASE_URL}/locations/popular?${searchParams.toString()}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail || "Unable to fetch popular locations.");
  }

  return payload.suggestions ?? [];
}

export async function fetchLocationDetails(placeId) {
  const searchParams = new URLSearchParams();
  searchParams.set("placeId", placeId);

  const response = await fetch(`${API_BASE_URL}/locations/details?${searchParams.toString()}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.detail || "Unable to fetch location details.");
  }

  return payload;
}
