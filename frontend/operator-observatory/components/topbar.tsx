export function Topbar() {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white/70 border-b border-[var(--line)] backdrop-blur">
      <h1 className="text-xl font-semibold tracking-tight text-[var(--ink)]">
        Operator Observatory
      </h1>
      <div className="text-xs font-medium uppercase tracking-widest text-[var(--muted)]">
        Read-only Governance Visibility
      </div>
    </header>
  );
}
