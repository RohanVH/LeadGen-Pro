import ThemeToggle from "../components/ThemeToggle";
import AppLogo from "../components/AppLogo";

function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen text-gray-900 transition-colors duration-200 dark:text-gray-100">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/95 shadow-sm shadow-slate-900/5 backdrop-blur-xl transition-colors duration-200 dark:border-slate-800/80 dark:bg-slate-950/90 dark:shadow-black/20">
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" aria-hidden />
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="hidden rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 p-0.5 shadow-lg shadow-indigo-500/25 sm:block">
              <div className="rounded-[14px] bg-white p-1 dark:bg-slate-950">
                <AppLogo className="h-9 w-9 sm:h-10 sm:w-10" />
              </div>
            </div>
            <div className="sm:hidden">
              <AppLogo className="h-10 w-10" />
            </div>
            <div>
              <p className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white sm:text-xl">
                LeadGen Pro
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 sm:text-sm">
                AI-powered client acquisition & lead intelligence
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <div className="hidden rounded-full border border-indigo-200/80 bg-indigo-50/90 px-3 py-1.5 text-xs font-semibold text-indigo-800 shadow-sm dark:border-indigo-500/30 dark:bg-indigo-950/50 dark:text-indigo-200 md:block">
              Live pipeline
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">{children}</main>
    </div>
  );
}

export default DashboardLayout;
