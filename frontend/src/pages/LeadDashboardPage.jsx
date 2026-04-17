import LeadFilters from "../components/LeadFilters";
import LeadStats from "../components/LeadStats";
import LeadsTable from "../components/LeadsTable";
import SearchForm from "../components/SearchForm";
import { useLeadSearch } from "../hooks/useLeadSearch";
import { exportLeadsCsv } from "../services/leadService";

function LeadDashboardPage() {
  const {
    query,
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
  } = useLeadSearch();

  const onExport = () => {
    if (!query.city || !query.type) return;
    exportLeadsCsv(query);
  };

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

      <LeadsTable leads={filteredLeads} loading={loading} loadingStage={loadingStage} />
    </section>
  );
}

export default LeadDashboardPage;
