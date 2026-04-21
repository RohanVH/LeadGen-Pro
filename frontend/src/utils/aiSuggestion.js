export function getAISuggestion(businessType, isBusinessTime) {
  if (!businessType) return "Reach out during active hours with a clear value proposition.";

  const type = businessType.toLowerCase();

  // 🍽️ FOOD
  if (type.includes("restaurant") || type.includes("cafe") || type.includes("food")) {
    return isBusinessTime
      ? "Catch them between rush hours and pitch how you can increase orders."
      : "Avoid rush hours — contact before lunch or after 3 PM for better response.";
  }

  // 🏥 HEALTH
  if (type.includes("clinic") || type.includes("hospital")) {
    return isBusinessTime
      ? "Highlight patient growth and online booking improvements."
      : "Best to contact early morning or evening when doctors are free.";
  }

  // 🛍️ RETAIL
  if (type.includes("store") || type.includes("shop")) {
    return isBusinessTime
      ? "Focus on increasing walk-ins and local visibility."
      : "Reach out during mid-day when store activity is stable.";
  }

  // 💼 DEFAULT
  return isBusinessTime
    ? "Pitch quick wins and immediate business impact."
    : "Wait for business hours and lead with a strong hook.";
}