function PageSection({ eyebrow, title, description, children, className = "" }) {
  return (
    <section className={`space-y-4 ${className}`}>
      {(eyebrow || title || description) && (
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            {eyebrow ? (
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-400">{eyebrow}</p>
            ) : null}
            {title ? (
              <h2 className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white">{title}</h2>
            ) : null}
            {description ? <p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{description}</p> : null}
          </div>
        </div>
      )}
      {children}
    </section>
  );
}

export default PageSection;
