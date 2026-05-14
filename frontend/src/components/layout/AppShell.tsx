import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  return (
    <div className="min-h-screen bg-life-grid bg-[size:42px_42px]">
      <div className="flex">
        <Sidebar />
        <main className="min-w-0 flex-1">
          <Topbar />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
