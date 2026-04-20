const NORMALIZATION_MAP = {
  "cloth store": "clothing store",
  "clothes store": "clothing store",
  "garment shop": "clothing store",
  "dog shop": "pet store",
  "pet shop": "pet store",
  "mobile shop": "electronics store",
  "phone shop": "electronics store",
  "cell phone shop": "electronics store",
  "medical shop": "pharmacy",
  "chemist shop": "pharmacy",
  "beauty parlour": "salon",
  "beauty parlor": "salon",
};

const TOKEN_MAP = {
  cloth: "clothing",
  clothes: "clothing",
  garment: "clothing",
  mobile: "electronics",
  phone: "electronics",
  dog: "pet",
  vet: "veterinary",
  parlour: "salon",
  parlor: "salon",
  chemist: "pharmacy",
  medical: "pharmacy",
};

function normalizeText(value) {
  return (value || "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ");
}

function tokenize(value) {
  return normalizeText(value)
    .split(" ")
    .map((token) => TOKEN_MAP[token] || token)
    .filter(Boolean);
}

function similarityScore(source, target) {
  if (!source || !target) return 0;
  if (source === target) return 1;
  if (target.startsWith(source)) return 0.92;
  if (target.includes(source)) return 0.78;

  const sourceTokens = new Set(tokenize(source));
  const targetTokens = new Set(tokenize(target));
  const intersection = [...sourceTokens].filter((token) => targetTokens.has(token)).length;
  const union = new Set([...sourceTokens, ...targetTokens]).size || 1;
  return intersection / union;
}

export function normalizeBusinessType(input) {
  const normalized = normalizeText(input);
  if (!normalized) return "";
  if (NORMALIZATION_MAP[normalized]) {
    return NORMALIZATION_MAP[normalized];
  }
  const mappedTokens = tokenize(normalized);
  return mappedTokens.join(" ");
}

export function getBusinessTypeSuggestions(query, options) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) {
    return options.slice(0, 40);
  }

  const normalizedTarget = normalizeBusinessType(normalizedQuery);
  const scored = options
    .map((option) => {
      const optionLabel = normalizeText(option.label);
      const baseScore = Math.max(
        similarityScore(normalizedQuery, optionLabel),
        similarityScore(normalizedTarget, optionLabel)
      );
      const normalizedMatchBoost =
        normalizedTarget && optionLabel.includes(normalizedTarget) && normalizedTarget !== normalizedQuery ? 0.12 : 0;
      return { option, score: baseScore + normalizedMatchBoost };
    })
    .filter((entry) => entry.score >= 0.2)
    .sort((a, b) => b.score - a.score || a.option.label.localeCompare(b.option.label))
    .slice(0, 10)
    .map((entry) => entry.option);

  return scored;
}
