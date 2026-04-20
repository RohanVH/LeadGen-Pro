import { useId } from "react";

function LeadFilters({ activeFilters = [], onToggleFilter, hotLeadsOnly, onToggleHotLeads }) {
  const hotToggleLabelId = `${useId()}-hot-only-label`;
  const allSelected = activeFilters.length === 0;
  const items = [
    { label: "All Leads", value: "all" },
    { label: "High Priority", value: "high-priority" },
    { label: "Has Email", value: "has-email" },
    { label: "No Website", value: "no-website" },
    { label: "Weak Website", value: "weak-website" },
    { label: "Good Website", value: "good-website" },
  ];

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
      <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 ring-1 ring-slate-200/80 dark:bg-slate-800 dark:ring-slate-700">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M4 6h16" />
            <path d="M7 12h10" />
            <path d="M10 18h4" />
          </svg>
        </span>
        <span className="text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">View</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isAll = item.value === "all";
          const selected = isAll ? allSelected : activeFilters.includes(item.value);
          return (
            <button
              key={item.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onToggleFilter(item.value)}
              className={`rounded-full px-3.5 py-1.5 text-sm font-semibold transition-all duration-200 ${
                selected
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/25 ring-2 ring-indigo-500/30 ring-offset-2 ring-offset-white dark:ring-offset-slate-900"
                  : "bg-white/90 text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50 hover:ring-slate-300 dark:bg-slate-800/80 dark:text-slate-200 dark:ring-slate-600 dark:hover:bg-slate-700"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <div
        className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-amber-200/90 bg-gradient-to-r from-amber-50 to-amber-50/30 px-3 py-1.5 shadow-sm dark:border-amber-900/50 dark:from-amber-950/40 dark:to-amber-950/20"
        role="group"
        aria-label="Show hot leads only"
      >
        <span className="text-sm font-semibold text-amber-900 dark:text-amber-200" id={hotToggleLabelId}>
          Hot only
        </span>
        <button
          type="button"
          aria-pressed={hotLeadsOnly}
          aria-labelledby={hotToggleLabelId}
          onClick={() => onToggleHotLeads(!hotLeadsOnly)}
          className={`relative h-6 w-11 rounded-full transition-colors duration-200 ${
            hotLeadsOnly ? "bg-amber-500 shadow-inner" : "bg-slate-300 dark:bg-slate-600"
          }`}
        >
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200 dark:bg-slate-100 ${
              hotLeadsOnly ? "left-5" : "left-0.5"
            }`}
          />
        </button>
      </div>
    </div>
  );
}

export default LeadFilters;
