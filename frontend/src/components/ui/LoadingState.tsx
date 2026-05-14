export function LoadingState({ label = "Syncing LifeTwin intelligence..." }: { label?: string }) {
  return (
    <div className="grid min-h-[280px] place-items-center rounded-3xl border border-white/10 bg-white/[0.03]">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="relative h-16 w-16">
          <div className="absolute inset-0 rounded-full border-2 border-emerald-300/20" />
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-emerald-300" />
          <div className="absolute inset-4 rounded-full bg-emerald-300/20 blur-md" />
        </div>
        <p className="text-sm text-slate-300">{label}</p>
      </div>
    </div>
  );
}
