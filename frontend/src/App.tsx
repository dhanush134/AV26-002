import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { AppShell } from "./components/layout/AppShell";
import { DailyCheckinPage } from "./pages/DailyCheckinPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DoctorReportPage } from "./pages/DoctorReportPage";
import { LandingPage } from "./pages/LandingPage";
import { SimulationPage } from "./pages/SimulationPage";
import { TwinPage } from "./pages/TwinPage";
import { WatchModePage } from "./pages/WatchModePage";

const Page = ({ children }: { children: React.ReactNode }) => (
  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }}>
    {children}
  </motion.div>
);

export default function App() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<LandingPage />} />
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<Page><DashboardPage /></Page>} />
          <Route path="/twin" element={<Page><TwinPage /></Page>} />
          <Route path="/simulation" element={<Page><SimulationPage /></Page>} />
          <Route path="/daily-checkin" element={<Page><DailyCheckinPage /></Page>} />
          <Route path="/doctor-report" element={<Page><DoctorReportPage /></Page>} />
          <Route path="/watch-mode" element={<Page><WatchModePage /></Page>} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}
