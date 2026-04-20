function AppLogo({ className = "h-9 w-9", withWordmark = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <img src="/logo.svg" alt="" width={36} height={36} className={`shrink-0 ${className}`} />
      {withWordmark ? (
        <span className="font-display text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">LeadGen Pro</span>
      ) : null}
    </div>
  );
}

export default AppLogo;
