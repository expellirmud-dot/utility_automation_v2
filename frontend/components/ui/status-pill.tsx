import { cn } from "@/lib/utils";

type StatusTone = "success" | "warning" | "danger" | "neutral";

const toneClass: Record<StatusTone, string> = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
  danger: "bg-orange-50 text-orange-700 ring-orange-200",
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function StatusPill({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: StatusTone;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1",
        toneClass[tone],
      )}
    >
      {children}
    </span>
  );
}
