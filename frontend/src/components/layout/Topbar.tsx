import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { ActivitySquare, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { lifetwinApi } from "../../api/lifetwinApi";
import { apiBaseUrl } from "../../api/client";
import { Button } from "../ui/Button";

const mobileNav = [
  ["Home", "/"],
  ["Dashboard", "/dashboard"],
  ["Twin", "/twin"],
  ["Sim", "/simulation"],
  ["Check-in", "/daily-checkin"],
  ["Report", "/doctor-report"],
  ["Watch", "/watch-mode"],
];

export function Topbar({ onRefresh }: { onRefresh?: () => void }) {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        await lifetwinApi.health();
        if (active) setHealthy(true);
      } catch {
        if (active) setHealthy(false);
      }
    };
    check();
    const id = window.setInterval(check, 15000);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-ink/75 backdrop-blur-2xl">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3 lg:hidden">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-emerald-300 to-blue-400 text-slate-950">
            <ActivitySquare size={20} />
          </div>
          <span className="font-bold text-white">LifeTwin AI</span>
        </Link>

        <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 text-xs text-slate-300 sm:flex">
          {healthy ? <Wifi size={15} className="text-emerald-300" /> : <WifiOff size={15} className="text-rose-300" />}
          <span>{healthy === null ? "Checking backend" : healthy ? "Backend online" : "Backend unavailable"}</span>
          <span className="text-slate-500">{apiBaseUrl}</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {onRefresh ? (
            <Button variant="secondary" onClick={onRefresh} className="min-h-10 rounded-full px-3" aria-label="Refresh dashboard">
              <RefreshCw size={16} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          ) : null}
          <Button
            variant="ghost"
            className="min-h-10 rounded-full px-3"
            onClick={() => {
              localStorage.removeItem("lifetwin_user_id");
              window.location.href = "/";
            }}
          >
            Reset Demo
          </Button>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto border-t border-white/10 px-4 py-2 lg:hidden">
        {mobileNav.map(([label, to]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-semibold ${
                isActive ? "bg-white/15 text-white" : "text-slate-400"
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
