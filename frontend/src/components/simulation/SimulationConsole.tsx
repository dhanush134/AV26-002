import { motion } from "framer-motion";
import { TerminalSquare } from "lucide-react";
import { Card } from "../ui/Card";

const events = [
  "Streaming wearable readings...",
  "Detecting baseline deviation...",
  "Generating preventive alert...",
  "Updating digital twin alignment...",
  "Re-ranking tomorrow's routine...",
];

export function SimulationConsole({ running }: { running: boolean }) {
  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <TerminalSquare className="h-5 w-5 text-emerald-200" />
          <span>Event Console</span>
        </div>
      }
    >
      <div className="rounded-2xl border border-emerald-300/15 bg-black/40 p-4 font-mono text-sm">
        {events.map((event, index) => (
          <motion.div
            key={event}
            initial={{ opacity: 0.25 }}
            animate={{ opacity: running ? [0.25, 1, 0.45] : 1 }}
            transition={{ duration: 1.2, repeat: running ? Infinity : 0, delay: index * 0.18 }}
            className="flex gap-3 border-b border-white/5 py-2 last:border-0"
          >
            <span className="text-emerald-300">{String(index + 1).padStart(2, "0")}</span>
            <span className="text-slate-200">{event}</span>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}
