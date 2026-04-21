export function getCountryInsight(country) {
  const data = {
    Cambodia: {
      currency: "Cambodian Riel (KHR)",
      strength: "Weak",
      mindset: "Price-sensitive and relationship-driven",
      tip: "Focus on affordability and long-term value. Trust building is key."
    },

    India: {
      currency: "Indian Rupee (INR)",
      strength: "Moderate",
      mindset: "Value-conscious but open to growth",
      tip: "Highlight ROI and cost vs benefit clearly."
    },

    "United States": {
      currency: "US Dollar (USD)",
      strength: "Strong",
      mindset: "Results-driven and fast decision-making",
      tip: "Focus on revenue growth and efficiency."
    },

    Germany: {
      currency: "Euro (EUR)",
      strength: "Strong",
      mindset: "Detail-oriented and quality-focused",
      tip: "Show structured solutions and reliability."
    }
  };

  return data[country] || {
    currency: "Unknown",
    strength: "Unknown",
    mindset: "Varies",
    tip: "Focus on clear value and professionalism."
  };
}