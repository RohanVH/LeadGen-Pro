function IconUsers() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function IconTarget() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}

function IconMail() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 6h16v12H4z" />
      <path d="m4 8 8 6 8-6" />
    </svg>
  );
}

function IconFlame() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3s4 4.5 4 9a4 4 0 1 1-8 0c0-4.5 4-9 4-9z" />
    </svg>
  );
}

function StatCard({ label, value, icon: Icon, tone }) {
  const tones = {
    neutral:
      "border-slate-200/90 bg-white/90 text-slate-600 ring-slate-100 dark:border-slate-700/90 dark:bg-slate-900/70 dark:text-slate-300 dark:ring-slate-800",
    rose: "border-rose-200/80 bg-gradient-to-br from-rose-50 to-white text-rose-700 ring-rose-100 dark:border-rose-900/50 dark:from-rose-950/50 dark:to-slate-900/80 dark:text-rose-200 dark:ring-rose-900/40",
    teal: "border-teal-200/80 bg-gradient-to-br from-teal-50 to-white text-teal-700 ring-teal-100 dark:border-teal-900/50 dark:from-teal-950/50 dark:to-slate-900/80 dark:text-teal-200 dark:ring-teal-900/40",
    amber:
      "border-amber-200/80 bg-gradient-to-br from-amber-50 to-white text-amber-800 ring-amber-100 dark:border-amber-900/50 dark:from-amber-950/50 dark:to-slate-900/80 dark:text-amber-200 dark:ring-amber-900/40",
  };
  const valueColors = {
    neutral: "text-slate-900 dark:text-white",
    rose: "text-rose-700 dark:text-rose-100",
    teal: "text-teal-700 dark:text-teal-100",
    amber: "text-amber-800 dark:text-amber-100",
  };

  return (
    <article
      className={`relative overflow-hidden rounded-2xl border p-5 shadow-card ring-1 backdrop-blur-sm transition-colors duration-200 ${tones[tone]}`}
    >
      <div className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/40 blur-2xl dark:bg-white/5" />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.14em] opacity-90">{label}</p>
          <p className={`mt-2 font-display text-3xl font-bold tabular-nums ${valueColors[tone]}`}>{value}</p>
        </div>
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/80 ring-1 ring-inset ring-black/5 dark:bg-slate-800/80 dark:ring-white/10`}
          aria-hidden="true"
        >
          <Icon />
        </span>
      </div>
    </article>
  );
}

function LeadStats({ total, highPriority, emailsFound, hotLeads }) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="Total leads" value={total} icon={IconUsers} tone="neutral" />
      <StatCard label="High priority" value={highPriority} icon={IconTarget} tone="rose" />
      <StatCard label="Emails found" value={emailsFound} icon={IconMail} tone="teal" />
      <StatCard label="Hot leads" value={hotLeads} icon={IconFlame} tone="amber" />
    </section>
  );
}

export default LeadStats;
