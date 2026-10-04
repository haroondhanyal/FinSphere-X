"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearAuthTokens, getAuthToken } from "@/lib/api";
import { WorkspaceHeader } from "./workspace-header";
import { signOut, WorkspaceSidebar } from "./workspace-sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<{ email: string; role: string } | null>(
    null,
  );
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getAuthToken()) {
      router.replace("/login");
      return;
    }
    api<{ email: string; role: string }>("/auth/me")
      .then(setUser)
      .catch(() => {
        clearAuthTokens();
        router.replace("/login");
      })
      .finally(() => setReady(true));
  }, [router]);
  if (!ready || !user)
    return <div className="loading">FinSphere X · Secure workspace</div>;
  return (
    <div className="app-frame">
      <WorkspaceSidebar
        email={user.email}
        role={user.role}
        onSignOut={() => void signOut().finally(() => router.replace("/login"))}
      />
      <main className="main-area">
        <WorkspaceHeader email={user.email} role={user.role} onSignOut={() => void signOut().finally(() => router.replace("/login"))} />
        <div className="content-area">{children}</div>
      </main>
    </div>
  );
}
