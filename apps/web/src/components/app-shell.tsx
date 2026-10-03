"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Activity,
  ArrowLeftRight,
  Banknote,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Wallet,
  UserRound,
  FileText,
  ShieldCheck,
} from "lucide-react";

const items = [
  ["/dashboard", "Overview", LayoutDashboard],
  ["/accounts", "Accounts", Banknote],
  ["/wallet", "Wallet", Wallet],
  ["/transfers", "Transfers", ArrowLeftRight],
  ["/payments", "Payments", Activity],
  ["/cards", "Cards", CreditCard],
  ["/statements", "Statements", FileText],
  ["/profile", "Profile & KYC", UserRound],
  ["/security", "Security", ShieldCheck],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<{ email: string; role: string } | null>(
    null,
  );
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("fsx_token")) {
      router.replace("/login");
      return;
    }
    api<{ email: string; role: string }>("/auth/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("fsx_token");
        router.replace("/login");
      })
      .finally(() => setReady(true));
  }, [router]);
  if (!ready || !user)
    return <div className="loading">FinSphere X · Secure workspace</div>;
  return (
    <div className="app-frame">
      <aside className="sidebar">
        <Link href="/dashboard" className="brand">
          <span className="brand-mark">F</span>
          <span>
            <b>
              FinSphere<span className="brand-x">X</span>
            </b>
            <small>Banking beyond borders</small>
          </span>
        </Link>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {items.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${pathname.startsWith(href) ? "active" : ""}`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="user-chip">
            <span className="avatar">
              {user.email.slice(0, 1).toUpperCase()}
            </span>
            <span className="user-meta">
              <b>{user.email.split("@")[0]}</b>
              <small>{user.role}</small>
            </span>
          </div>
          <button
            className="logout"
            onClick={() => {
              const refreshToken = localStorage.getItem("fsx_refresh");
              if (refreshToken)
                void api("/auth/logout", {
                  method: "POST",
                  body: JSON.stringify({ refresh_token: refreshToken }),
                }).catch(() => undefined);
              localStorage.removeItem("fsx_token");
              localStorage.removeItem("fsx_refresh");
              router.replace("/login");
            }}
            aria-label="Sign out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div>
            <span className="eyebrow">FINSPHERE X / PERSONAL</span>
            <h1>
              {items.find(([href]) => pathname.startsWith(href))?.[1] ??
                "Workspace"}
            </h1>
          </div>
          <div className="topbar-right">
            <span className="secure-dot" /> Secure session{" "}
            <span className="top-avatar">
              {user.email.slice(0, 1).toUpperCase()}
            </span>
          </div>
        </header>
        <div className="content-area">{children}</div>
      </main>
    </div>
  );
}
