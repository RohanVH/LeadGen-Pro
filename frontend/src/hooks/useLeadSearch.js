import { useMemo, useState } from "react";
import { searchLeads } from "../services/leadService";

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";

export function useLeadSearch() {
  const [query, setQuery] = useState({ city: "", type: "", country: "" });
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
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

  const submitSearch = async (nextQuery) => {
    if (loading) {
      return;
    }

    setLoading(true);
    setLoadingStage("Fetching leads...");
    setError("");
    setQuery(nextQuery);
    const analysisTimer = window.setTimeout(() => {
      setLoadingStage("Analyzing businesses...");
    }, 1200);

    try {
      const data = await searchLeads(nextQuery);
      setLeads(data.leads ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setLeads([]);
      setTotal(0);
      setError(err.message || DEFAULT_ERROR_MESSAGE);
    } finally {
      window.clearTimeout(analysisTimer);
      setLoading(false);
      setLoadingStage("");
    }
  };

  return {
    query,
    leads,
    filteredLeads,
    total,
    loading,
    loadingStage,
    error,
    filter,
    setFilter,
    hotLeadsOnly,
    setHotLeadsOnly,
    submitSearch,
    stats,
  };
}
