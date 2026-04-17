function LeadFilters({ filter, onChange, hotLeadsOnly, onToggleHotLeads }) {
  const items = [
    { label: "All Leads", value: "all" },
    { label: "High Priority", value: "high-priority" },
    { label: "Has Email", value: "has-email" },
    { label: "No Website", value: "no-website" },
    { label: "Weak Website", value: "weak-website" },
    { label: "Good Website", value: "good-website" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M4 6h16" />
          <path d="M7 12h10" />
          <path d="M10 18h4" />
        </svg>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => onChange(item.value)}
            className={`rounded-xl px-3 py-1.5 text-sm font-semibold transition-colors duration-200 ${
              filter === item.value
                ? "bg-indigo-600 text-white shadow-sm hover:bg-indigo-700"
                : "bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700 dark:hover:bg-slate-700"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-amber-50 px-3 py-1.5 ring-1 ring-amber-200 transition-colors duration-200 dark:bg-amber-950/40 dark:ring-amber-900/60">
        <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">Hot Leads Only</span>
        <button
          type="button"
          aria-pressed={hotLeadsOnly}
          onClick={() => onToggleHotLeads(!hotLeadsOnly)}
          className={`relative h-6 w-11 rounded-full transition-colors duration-200 ${
            hotLeadsOnly ? "bg-amber-500" : "bg-slate-300 dark:bg-slate-600"
          }`}
        >
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-colors duration-200 dark:bg-slate-100 ${
              hotLeadsOnly ? "left-5" : "left-0.5"
            }`}
          />
        </button>
      </label>
    </div>
  );
}

export default LeadFilters;
