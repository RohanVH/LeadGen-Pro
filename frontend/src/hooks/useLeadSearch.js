import { useMemo, useState } from "react";
import { searchLeads } from "../services/leadService";

export function useLeadSearch() {
  const [query, setQuery] = useState({ city: "", type: "", country: "" });
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
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
    setLoading(true);
    setError("");
    setQuery(nextQuery);
    try {
      const data = await searchLeads(nextQuery);
      setLeads(data.leads ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setLeads([]);
      setTotal(0);
      setError(err.message || "Unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return {
    query,
    leads,
    filteredLeads,
    total,
    loading,
    error,
    filter,
    setFilter,
    hotLeadsOnly,
    setHotLeadsOnly,
    submitSearch,
    stats,
  };
}
