import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BrainCircuit, HeartPulse, Radar, Watch } from "lucide-react";
import { lifetwinApi } from "../api/lifetwinApi";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { toText } from "../utils/formatters";

const sections = [
  { title: "Current Twin vs Ideal Twin", icon: BrainCircuit, copy: "See your current physiological state beside the healthspan target you are working toward." },
  { title: "Preventive Risk Intelligence", icon: Radar, copy: "Turn wearable, lifestyle, and lab signals into risk clusters judges can understand instantly." },
  { title: "Daily Adaptive Routine", icon: HeartPulse, copy: "Check in once a day and watch the twin adapt tomorrow's plan around real behavior." },
  { title: "Wearable Monitoring Mode", icon: Watch, copy: "Demo a serious input layer for Samsung Watch, Apple Health, Fitbit, and Garmin." },
];

export function LandingPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const launchDemo = async () => {
    setLoading(true);
    setError("");
    try {
      const demo = await lifetwinApi.runFullDemo();
      const userId = toText(demo.user_id ?? demo.id, "");
      if (!userId) throw new Error("Demo user id missing from response");
      localStorage.setItem("lifetwin_user_id", userId);
      navigate("/dashboard");
    } catch {
      setError("Could not launch the demo. Check that the FastAPI backend is running on the configured URL.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-life-grid bg-[size:44px_44px]">
      <section className="page-wrap grid min-h-screen items-center gap-10 py-10 lg:grid-cols-[1fr_0.92fr]">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
          <div className="mb-5 inline-flex rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 text-sm font-semibold text-emerald-100">
            Preventive healthcare, made visible
          </div>
          <h1 className="max-w-4xl text-5xl font-extrabold leading-[1.02] text-white sm:text-7xl">
            Meet your preventive health digital twin.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            LifeTwin AI turns wearable, lifestyle, and lab data into a living health twin that helps you close the gap
            between who you are today and your ideal future self.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button onClick={launchDemo} disabled={loading}>
              {loading ? "Launching..." : "Launch Demo"} <ArrowRight size={18} />
            </Button>
            <Button variant="secondary" onClick={() => navigate("/watch-mode")}>
              View Watch Mode
            </Button>
          </div>
          {error ? <p className="mt-4 rounded-2xl border border-rose-400/25 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</p> : null}
        </motion.div>

        <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="relative">
          <div className="glass-card p-4 sm:p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Twin alignment</p>
                <p className="text-3xl font-bold text-white">72% today</p>
              </div>
              <div className="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1 text-xs font-semibold text-amber-100">
                Moderate risk
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-rose-300/15 bg-rose-400/10 p-5">
                <p className="text-sm font-semibold text-rose-100">Current You</p>
                <div className="mt-5 space-y-3">
                  {["Sleep 6.4h", "Steps 7.2k", "Resting HR 72", "LDL 132"].map((item) => (
                    <div key={item} className="rounded-xl bg-black/20 px-3 py-2 text-sm text-slate-200">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-3xl border border-emerald-300/20 bg-emerald-300/10 p-5 shadow-glow">
                <p className="text-sm font-semibold text-emerald-100">Ideal Future Twin</p>
                <div className="mt-5 space-y-3">
                  {["Sleep 7.6h", "Steps 10k", "Resting HR 62", "LDL 95"].map((item) => (
                    <div key={item} className="rounded-xl bg-black/20 px-3 py-2 text-sm text-slate-200">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-5 h-28 rounded-3xl border border-white/10 bg-black/25 p-4">
              <div className="flex h-full items-end gap-2">
                {[34, 56, 44, 72, 61, 78, 69, 84, 76, 91].map((height, index) => (
                  <div
                    key={index}
                    className="flex-1 rounded-t-lg bg-gradient-to-t from-emerald-400 to-cyan-300"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="page-wrap grid gap-4 pb-16 md:grid-cols-2 xl:grid-cols-4">
        {sections.map((section) => (
          <Card key={section.title} className="min-h-56">
            <section.icon className="mb-5 h-8 w-8 text-cyan-200" />
            <h2 className="text-xl font-bold text-white">{section.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">{section.copy}</p>
          </Card>
        ))}
      </section>
    </main>
  );
}
