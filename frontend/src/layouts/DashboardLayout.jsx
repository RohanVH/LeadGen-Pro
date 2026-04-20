import ThemeToggle from "../components/ThemeToggle";
import AppLogo from "../components/AppLogo";

function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 transition-colors duration-200 dark:bg-gray-900 dark:text-gray-100">
      <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/85 backdrop-blur-md transition-colors duration-200 dark:border-slate-800 dark:bg-slate-900/85">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-3">
            <AppLogo className="h-10 w-10 sm:h-11 sm:w-11" />
            <div>
              <p className="font-display text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">LeadGen Pro</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Global lead generation and client acquisition dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 transition-colors duration-200 dark:bg-slate-800 dark:text-slate-300 sm:block">
              Agency Suite
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}

export default DashboardLayout;
