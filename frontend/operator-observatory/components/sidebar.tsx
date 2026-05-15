"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { label: "Overview", href: "/overview" },
  { label: "Domain Panels", href: "/panels" },
  { label: "Projections", href: "/projections" },
  { label: "Surfaces", href: "/surfaces" },
  { label: "Route Governance", href: "/route-governance" },
  { label: "Release Governance", href: "/release-governance" },
  { label: "Evidence Package", href: "/evidence-package" },
  { label: "Evidence Package Integrity", href: "/evidence-package-integrity" },
  { label: "Evidence Package Readiness", href: "/evidence-package-readiness" },
  { label: "Human Review Intent", href: "/human-review-intent" },


] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-64 h-screen bg-white border-r border-[var(--line)]">
      <div className="p-6">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--accent)]">
          Observatory
        </p>
      </div>
      <nav className="flex-1 px-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "text-[var(--muted)] hover:bg-gray-50 hover:text-[var(--ink)]"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
