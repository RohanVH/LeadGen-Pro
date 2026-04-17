function LeadStats({ total, highPriority, emailsFound, hotLeads }) {
  return (
    <section className="grid gap-4 sm:grid-cols-4">
      <article className="rounded-xl border border-slate-200 bg-gray-50 p-5 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Total Leads</p>
        <p className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-slate-100">{total}</p>
      </article>
      <article className="rounded-xl border border-rose-200 bg-rose-50 p-5 shadow-card transition-colors duration-200 dark:border-rose-900/60 dark:bg-rose-950/40">
        <p className="text-xs font-semibold uppercase tracking-wide text-rose-700 dark:text-rose-300">High Priority Leads</p>
        <p className="mt-2 font-display text-3xl font-bold text-rose-700 dark:text-rose-200">{highPriority}</p>
      </article>
      <article className="rounded-xl border border-teal-200 bg-teal-50 p-5 shadow-card transition-colors duration-200 dark:border-teal-900/60 dark:bg-teal-950/40">
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700 dark:text-teal-300">Emails Found</p>
        <p className="mt-2 font-display text-3xl font-bold text-teal-700 dark:text-teal-200">{emailsFound}</p>
      </article>
      <article className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-card transition-colors duration-200 dark:border-amber-900/60 dark:bg-amber-950/40">
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">Hot Leads</p>
        <p className="mt-2 font-display text-3xl font-bold text-amber-700 dark:text-amber-200">{hotLeads}</p>
      </article>
    </section>
  );
}

export default LeadStats;
