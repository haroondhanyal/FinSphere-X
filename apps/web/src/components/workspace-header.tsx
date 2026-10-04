"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, LogOut, Shield, UserRound } from "lucide-react";
import { api } from "@/lib/api";
import { roleNavigation } from "./workspace-navigation";

type Role = keyof typeof roleNavigation;

export function WorkspaceHeader({
  email,
  role,
  onSignOut,
}: {
  email: string;
  role: string;
  onSignOut: () => void;
}) {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const search = useQuery<{ results: { type: string; label: string; detail: string; href: string }[] }>({
    queryKey: ["global-search", searchTerm],
    queryFn: () => api("/search?q=" + encodeURIComponent(searchTerm)),
    enabled: searchTerm.trim().length >= 2,
    staleTime: 15_000,
  });
  const pathname = usePathname();
  const items =
    roleNavigation[(role in roleNavigation ? role : "customer") as Role];
  const title =
    items.find(([href]) => pathname.startsWith(href))?.[1] ?? "Workspace";

  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">FINSPHERE X / PERSONAL</span>
        <h1>{title}</h1>
      </div>
      <div className="topbar-right">
        <div className="global-search">
          <input aria-label="Search your accounts and activity" placeholder="Search accounts and activity" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} />
          {searchTerm.trim().length >= 2 && <div className="global-search-results" role="listbox">
            {search.isFetching && <small>Searching…</small>}
            {search.data?.results.map((result, index) => <Link role="option" key={result.type + result.href + index} href={result.href} onClick={() => setSearchTerm("")}><b>{result.label}</b><small>{result.detail}</small></Link>)}
            {!search.isFetching && !search.data?.results.length && <small>No results found.</small>}
          </div>}
        </div>
        <span className="secure-dot" /> Secure session
        <div className="account-menu-wrap">
          <button className="account-menu-trigger" type="button" aria-expanded={accountMenuOpen} aria-label="Open account menu" onClick={() => setAccountMenuOpen((open) => !open)}>
            <span className="top-avatar">{email.slice(0, 1).toUpperCase()}</span><ChevronDown size={15} />
          </button>
          {accountMenuOpen && <div className="account-menu" role="menu">
            <div className="account-menu-identity"><b>{email.split("@")[0]}</b><small>{email} · {role}</small></div>
            <Link href="/profile" role="menuitem" onClick={() => setAccountMenuOpen(false)}><UserRound size={16} /> Edit profile</Link>
            <Link href="/security" role="menuitem" onClick={() => setAccountMenuOpen(false)}><Shield size={16} /> Security</Link>
            <button type="button" role="menuitem" onClick={onSignOut}><LogOut size={16} /> Sign out</button>
          </div>}
        </div>
      </div>
    </header>
  );
}
