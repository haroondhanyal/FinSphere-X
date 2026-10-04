"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, Palette } from "lucide-react";
import { useEffect, useState, type CSSProperties } from "react";
import { api, clearAuthTokens, getRefreshToken } from "@/lib/api";
import { roleNavigation } from "./workspace-navigation";

type Role = keyof typeof roleNavigation;
const themes = [
  ["ocean", "Ocean", "#1264f4"], ["emerald", "Emerald", "#087f5b"],
  ["violet", "Violet", "#7048e8"], ["sunset", "Sunset", "#c2410c"],
  ["rose", "Rose", "#be185d"], ["teal", "Teal", "#0f766e"],
  ["indigo", "Indigo", "#4338ca"], ["ruby", "Ruby", "#b42335"],
  ["gold", "Gold", "#92620a"], ["slate", "Slate", "#475569"],
];

export function WorkspaceSidebar({
  email,
  role,
  onSignOut,
}: {
  email: string;
  role: string;
  onSignOut: () => void;
}) {
  const pathname = usePathname();
  const [theme, setTheme] = useState("ocean");
  useEffect(() => {
    const saved = localStorage.getItem("fsx_theme") || "ocean";
    setTheme(saved);
    document.documentElement.dataset.theme = saved;
  }, []);
  function changeTheme(value: string) {
    setTheme(value);
    document.documentElement.dataset.theme = value;
    localStorage.setItem("fsx_theme", value);
  }
  const visibleItems =
    roleNavigation[(role in roleNavigation ? role : "customer") as Role];

  return (
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
        {visibleItems.map(([href, label, Icon]) => (
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
      <div className="theme-picker">
        <span className="nav-label"><Palette size={13} /> COLOR THEME</span>
        <div className="theme-options" aria-label="Choose color theme">
          {themes.map(([value, label, color]) => (
            <button key={value} type="button" title={label} aria-label={`${label} theme`} aria-pressed={theme === value}
              className={theme === value ? "theme-swatch selected" : "theme-swatch"}
              style={{ "--swatch": color } as CSSProperties} onClick={() => changeTheme(value)} />
          ))}
        </div>
        <small>{themes.find(([value]) => value === theme)?.[1]} theme</small>
      </div>
      <div className="sidebar-bottom">
        <div className="user-chip">
          <span className="avatar">{email.slice(0, 1).toUpperCase()}</span>
          <span className="user-meta">
            <b>{email.split("@")[0]}</b>
            <small>{role}</small>
          </span>
        </div>
        <button className="logout" onClick={onSignOut} aria-label="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
}

export async function signOut() {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    await api("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => undefined);
  }
  clearAuthTokens();
}
