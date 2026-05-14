export function StatePanel({ title, detail }: { title: string; detail: string }) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-8 shadow-soft backdrop-blur">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
        {title}
      </p>
      <p className="mt-3 text-base leading-7 text-[var(--muted)]">{detail}</p>
    </section>
  );
}
