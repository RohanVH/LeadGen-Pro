import { useMemo, useState } from "react";
import { searchLeads } from "../services/leadService";
import { normalizeBusinessType } from "../utils/businessType";

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";
const PAGE_SIZE = 150;

export function useLeadSearch() {
  const [query, setQuery] = useState({ city: "", type: "", country: "" });
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [hotLeadsOnly, setHotLeadsOnly] = useState(false);

  const baseFilteredLeads = useMemo(() => {
    if (filter === "no-website") {
      return leads.filter((lead) => lead.websiteQuality === "NO_WEBSITE");
    }
    if (filter === "weak-website") {
      return leads.filter((lead) => lead.websiteQuality === "WEAK_WEBSITE");
    }
    if (filter === "good-website") {
      return leads.filter((lead) => lead.websiteQuality === "GOOD_WEBSITE");
    }
    if (filter === "high-priority") {
      return leads.filter((lead) => lead.priorityScore === "HIGH");
    }
    if (filter === "has-email") {
      return leads.filter((lead) => Boolean(lead.email));
    }
    return leads;
  }, [leads, filter]);

  const filteredLeads = useMemo(() => {
    if (!hotLeadsOnly) {
      return baseFilteredLeads;
    }
    return baseFilteredLeads.filter((lead) => Boolean(lead.isHotLead));
  }, [baseFilteredLeads, hotLeadsOnly]);

  const stats = useMemo(() => {
    const highPriority = leads.filter((lead) => lead.priorityScore === "HIGH").length;
    const emailsFound = leads.filter((lead) => Boolean(lead.email)).length;
    const hotLeads = leads.filter((lead) => Boolean(lead.isHotLead)).length;
    return { highPriority, emailsFound, hotLeads };
  }, [leads]);

  const mergeUniqueLeads = (existingLeads, incomingLeads) => {
    const seen = new Set(
      existingLeads.map((lead) => lead.placeId || `${lead.name}-${lead.phoneNumber || ""}-${lead.email || ""}`)
    );
    const additions = [];
    for (const lead of incomingLeads) {
      const key = lead.placeId || `${lead.name}-${lead.phoneNumber || ""}-${lead.email || ""}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      additions.push(lead);
    }
    return [...existingLeads, ...additions];
  };

  const submitSearch = async (nextQuery) => {
    if (loading) {
      return;
    }

    setLoading(true);
    setLoadingStage("Fetching leads...");
    setError("");
    const normalizedType = normalizeBusinessType(nextQuery.type || "");
    const effectiveQuery = {
      ...nextQuery,
      type: normalizedType || (nextQuery.type || "").trim(),
    };
    setQuery(effectiveQuery);
    const analysisTimer = window.setTimeout(() => {
      setLoadingStage("Analyzing businesses...");
    }, 1200);

    try {
      const data = await searchLeads({ ...effectiveQuery, offset: 0, limit: PAGE_SIZE });
      setLeads(data.leads ?? []);
      setTotal(data.total ?? 0);
      setOffset((data.leads ?? []).length);
      setHasMore(Boolean(data.hasMore));
    } catch (err) {
      setLeads([]);
      setTotal(0);
      setOffset(0);
      setHasMore(false);
      setError(err.message || DEFAULT_ERROR_MESSAGE);
    } finally {
      window.clearTimeout(analysisTimer);
      setLoading(false);
      setLoadingStage("");
    }
  };

  const loadMore = async () => {
    if (loading || loadingMore || !hasMore || !query.city || !query.type) {
      return;
    }

    setLoadingMore(true);
    setError("");
    try {
      const data = await searchLeads({
        ...query,
        offset,
        limit: PAGE_SIZE,
      });
      const newLeads = data.leads ?? [];
      setLeads((prev) => mergeUniqueLeads(prev, newLeads));
      setOffset((prev) => prev + newLeads.length);
      setHasMore(Boolean(data.hasMore));
      setTotal((prev) => (typeof data.total === "number" ? data.total : prev));
    } catch (err) {
      setError(err.message || DEFAULT_ERROR_MESSAGE);
    } finally {
      setLoadingMore(false);
    }
  };

  return {
    query,
    leads,
    filteredLeads,
    total,
    hasMore,
    loadingMore,
    loading,
    loadingStage,
    error,
    filter,
    setFilter,
    hotLeadsOnly,
    setHotLeadsOnly,
    submitSearch,
    loadMore,
    stats,
  };
}
