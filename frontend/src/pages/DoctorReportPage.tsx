import { useEffect, useState } from "react";
import { lifetwinApi } from "../api/lifetwinApi";
import { DoctorReportView } from "../components/report/DoctorReportView";
import { EmptyState } from "../components/ui/EmptyState";
import { LoadingState } from "../components/ui/LoadingState";

export function DoctorReportPage() {
  const [report, setReport] = useState<Record<string, unknown>>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const userId = localStorage.getItem("lifetwin_user_id");

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    lifetwinApi
      .getDoctorReport(userId)
      .then(setReport)
      .catch(() => setError("Doctor report is unavailable. Confirm the backend report endpoint is running."))
      .finally(() => setLoading(false));
  }, [userId]);

  if (!userId) return <div className="page-wrap"><EmptyState title="No report yet" message="Launch the demo first to create reportable twin data." /></div>;
  if (loading) return <div className="page-wrap"><LoadingState label="Preparing clinician report..." /></div>;
  if (error || !report) return <div className="page-wrap"><EmptyState title="Report unavailable" message={error || "No report data was returned."} /></div>;

  return (
    <div className="page-wrap">
      <DoctorReportView report={report} />
    </div>
  );
}
