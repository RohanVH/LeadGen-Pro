const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "/api/v1");

async function parseJsonSafely(response) {
  const text = await response.text();
  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error("Something went wrong. Please try again.");
  }

  const payload = await parseJsonSafely(response);

  if (!response.ok) {
    throw new Error(payload.detail || "Something went wrong. Please try again.");
  }

  return payload;
}

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
return apiRequest(`/v1/leads/search?${queryString}`);
}

export function exportLeadsCsv(params) {
  const queryString = buildQuery(params);
window.open(`${API_BASE_URL}/v1/leads/export?${queryString}`, "_blank");
}

export async function sendOutreachEmail(payload) {
return apiRequest("/v1/outreach/send-email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchLocationSuggestions({ query, country }) {
  const searchParams = new URLSearchParams();
  searchParams.set("q", query);
  if (country) {
    searchParams.set("country", country);
  }

const payload = await apiRequest(`/v1/locations/autocomplete?${searchParams.toString()}`);

  return payload.suggestions ?? [];
}

export async function fetchPopularLocations(country) {
  const searchParams = new URLSearchParams();
  searchParams.set("country", country);

const payload = await apiRequest(`/v1/locations/popular?${searchParams.toString()}`);

  return payload.suggestions ?? [];
}

export async function fetchLocationDetails(placeId) {
  const searchParams = new URLSearchParams();
  searchParams.set("placeId", placeId);

return apiRequest(`/v1/locations/details?${searchParams.toString()}`);
}
