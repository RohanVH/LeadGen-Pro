import { useEffect, useRef } from "react";
import LeadFilters from "../components/LeadFilters";
import LeadStats from "../components/LeadStats";
import LeadsTable from "../components/LeadsTable";
import SearchForm from "../components/SearchForm";
import { useLeadSearch } from "../hooks/useLeadSearch";
import { exportLeadsCsv } from "../services/leadService";

function LeadDashboardPage() {
  const {
    query,
    leads,
    filteredLeads,
    total,
    hasMore,
    loading,
    loadingMore,
    loadingStage,
    error,
    filter,
    setFilter,
    hotLeadsOnly,
    setHotLeadsOnly,
    submitSearch,
    loadMore,
    stats,
  } = useLeadSearch();
  const loadMoreAnchorRef = useRef(null);

  const onExport = () => {
    if (!query.city || !query.type) return;
    exportLeadsCsv(query);
  };

  useEffect(() => {
    if (!loadMoreAnchorRef.current) {
      return undefined;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry?.isIntersecting) {
          return;
        }
        if (loading || loadingMore || !hasMore) {
          return;
        }
        loadMore();
      },
      { root: null, rootMargin: "300px 0px", threshold: 0.01 }
    );
    observer.observe(loadMoreAnchorRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadMore, loading, loadingMore]);

  return (
    <section className="space-y-6">
      <SearchForm onSearch={submitSearch} loading={loading} loadingStage={loadingStage} />

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-gray-50 p-4 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800">
        <LeadFilters
          filter={filter}
          onChange={setFilter}
          hotLeadsOnly={hotLeadsOnly}
          onToggleHotLeads={setHotLeadsOnly}
        />
        <button
          type="button"
          onClick={onExport}
          disabled={!query.city || !query.type || loading}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300 disabled:hover:translate-y-0 dark:disabled:bg-indigo-900"
        >
          Export CSV
        </button>
      </div>

      <LeadStats
        total={total}
        highPriority={stats.highPriority}
        emailsFound={stats.emailsFound}
        hotLeads={stats.hotLeads}
      />

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 transition-colors duration-200 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
          Something went wrong. Please try again.
        </div>
      ) : null}

      {!loading && total > 0 ? (
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Loaded {leads.length} / {total} leads</p>
      ) : null}

      <LeadsTable leads={filteredLeads} loading={loading} loadingStage={loadingStage} />

      {!loading && filteredLeads.length ? (
        <div className="flex justify-center">
          {hasMore ? (
            <button
              type="button"
              onClick={loadMore}
              disabled={loadingMore}
              className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400 disabled:hover:translate-y-0 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-slate-300"
            >
              {loadingMore ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-100 dark:border-slate-500 dark:border-t-slate-900" />
                  Loading more...
                </span>
              ) : (
                "Load More"
              )}
            </button>
          ) : (
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">All available leads loaded</p>
          )}
        </div>
      ) : null}
      <div ref={loadMoreAnchorRef} className="h-1 w-full" />
    </section>
  );
}

export default LeadDashboardPage;
