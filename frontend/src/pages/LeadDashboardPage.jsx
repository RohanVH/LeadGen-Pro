import { useEffect, useRef } from "react";
import LeadFilters from "../components/LeadFilters";
import LeadStats from "../components/LeadStats";
import LeadsTable from "../components/LeadsTable";
import PageSection from "../components/PageSection";
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
    <div className="space-y-10">
      <div className="relative overflow-hidden rounded-2xl border border-indigo-200/40 bg-gradient-to-br from-indigo-500/10 via-white to-violet-500/10 p-6 shadow-glow dark:border-indigo-500/20 dark:from-indigo-950/40 dark:via-slate-900/80 dark:to-violet-950/30 sm:p-8">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-indigo-400/20 blur-3xl dark:bg-indigo-500/10" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-violet-400/15 blur-3xl dark:bg-violet-500/10" />
        <div className="relative">
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-indigo-600 dark:text-indigo-400">Command center</p>
          <h1 className="mt-2 font-display text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            Find leads, enrich them, close faster
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
            Search by category and location, then review AI insights, priorities, and outreach in one structured pipeline.
          </p>
        </div>
      </div>

      <PageSection
        eyebrow="Step 1"
        title="Search & targeting"
        description="Pick a category, refine the business type, then choose country and city."
      >
        <SearchForm onSearch={submitSearch} loading={loading} loadingStage={loadingStage} />
      </PageSection>

      <PageSection
        eyebrow="Step 2"
        title="Filter & export"
        description="Narrow the list by priority or website quality, then export when you are ready."
      >
        <div className="flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-white/70 p-4 shadow-card backdrop-blur-sm dark:border-slate-700/80 dark:bg-slate-900/60 sm:flex-row sm:items-center sm:justify-between sm:p-5">
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
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-500/20 transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-300 disabled:shadow-none disabled:hover:translate-y-0 dark:border-indigo-500/30 dark:disabled:bg-slate-700"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 3v12m0 0l4-4m-4 4l-4-4" />
              <path d="M5 19h14" />
            </svg>
            Export CSV
          </button>
        </div>
      </PageSection>

      <PageSection eyebrow="Snapshot" title="Pipeline metrics" description="Key counts from your current result set.">
        <LeadStats
          total={total}
          highPriority={stats.highPriority}
          emailsFound={stats.emailsFound}
          hotLeads={stats.hotLeads}
        />
      </PageSection>

      {error ? (
        <div className="rounded-2xl border border-red-300/80 bg-red-50 px-4 py-3 text-sm font-medium text-red-800 shadow-sm dark:border-red-900/60 dark:bg-red-950/50 dark:text-red-200">
          Something went wrong. Please try again.
        </div>
      ) : null}

      <PageSection
        eyebrow="Step 3"
        title="Lead pipeline"
        description={
          !loading && total > 0
            ? `Loaded ${leads.length} of ${total} leads in this search.`
            : "Results will appear here after you search."
        }
      >
        <LeadsTable leads={filteredLeads} loading={loading} loadingStage={loadingStage} />
      </PageSection>

      {!loading && filteredLeads.length ? (
        <div className="flex justify-center pb-4">
          {hasMore ? (
            <button
              type="button"
              onClick={loadMore}
              disabled={loadingMore}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-800 shadow-lg shadow-slate-900/5 transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-300 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:border-indigo-500/50 dark:hover:text-indigo-300"
            >
              {loadingMore ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-300 border-t-indigo-600" />
                  Loading more...
                </>
              ) : (
                <>
                  <span className="text-indigo-600 dark:text-indigo-400">↓</span>
                  Load more leads
                </>
              )}
            </button>
          ) : (
            <p className="rounded-full border border-slate-200/80 bg-white/80 px-4 py-2 text-sm font-medium text-slate-500 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-400">
              All available leads loaded for this search
            </p>
          )}
        </div>
      ) : null}
      <div ref={loadMoreAnchorRef} className="h-1 w-full" />
    </div>
  );
}

export default LeadDashboardPage;
