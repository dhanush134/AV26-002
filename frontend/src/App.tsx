import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { DailyCheckinPage } from "./pages/DailyCheckinPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DoctorReportPage } from "./pages/DoctorReportPage";
import { LandingPage } from "./pages/LandingPage";
import { SimulationPage } from "./pages/SimulationPage";
import { TwinPage } from "./pages/TwinPage";
import { WatchModePage } from "./pages/WatchModePage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/twin" element={<TwinPage />} />
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/daily-checkin" element={<DailyCheckinPage />} />
        <Route path="/doctor-report" element={<DoctorReportPage />} />
        <Route path="/watch-mode" element={<WatchModePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
