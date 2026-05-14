import { NavLink } from "react-router-dom";
import { ActivitySquare, FileHeart, Gauge, HeartPulse, Radar, Rotate3D, Watch } from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/twin", label: "Digital Twin", icon: Rotate3D },
  { to: "/simulation", label: "Simulation", icon: Radar },
  { to: "/daily-checkin", label: "Daily Check-in", icon: HeartPulse },
  { to: "/doctor-report", label: "Doctor Report", icon: FileHeart },
  { to: "/watch-mode", label: "Watch Mode", icon: Watch },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-white/10 bg-black/20 p-5 backdrop-blur-xl lg:block">
      <NavLink to="/" className="mb-8 flex items-center gap-3 rounded-2xl p-2">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-emerald-300 to-blue-400 text-slate-950 shadow-glow">
          <ActivitySquare size={23} />
        </div>
        <div>
          <p className="text-lg font-bold text-white">LifeTwin AI</p>
          <p className="text-xs text-slate-400">Preventive twin OS</p>
        </div>
      </NavLink>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                isActive ? "bg-white/12 text-white shadow-glow-blue" : "text-slate-400 hover:bg-white/8 hover:text-white"
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 rounded-3xl border border-emerald-300/20 bg-emerald-300/10 p-4">
        <p className="text-sm font-semibold text-emerald-100">Demo narrative</p>
        <p className="mt-2 text-xs leading-5 text-slate-300">
          Current twin, ideal future twin, risk intelligence, daily adaptation, and watch data in one loop.
        </p>
      </div>
    </aside>
  );
}
