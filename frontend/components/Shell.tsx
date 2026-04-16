"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { LogoMark } from "@/components/LogoMark";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/datasets", label: "Datasets" },
  { href: "/prompts", label: "Prompts" },
  { href: "/runs", label: "Runs" },
  { href: "/compare", label: "Compare" },
  { href: "/settings", label: "Settings" },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-col gap-4 rounded-[28px] border border-black/5 bg-white/80 p-4 shadow-panel backdrop-blur lg:flex-row lg:items-center lg:justify-between">
        <Link href="/dashboard" className="flex items-center gap-3 rounded-2xl px-2 py-1">
          <LogoMark size="sm" />
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Axiom</p>
            <p className="font-display text-2xl leading-none text-ink">Evaluation OS</p>
          </div>
        </Link>
        <nav className="flex flex-wrap gap-2 lg:justify-end">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`${pathname === item.href ? "btn-chip-active" : "btn-nav"} text-sm`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </div>
  );
}
