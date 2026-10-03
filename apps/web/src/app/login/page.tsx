"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await api<{ access_token: string; refresh_token: string }>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: form.get("email"),
            password: form.get("password"),
          }),
        },
      );
      localStorage.setItem("fsx_token", result.access_token);
      localStorage.setItem("fsx_refresh", result.refresh_token);
      router.replace("/dashboard");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Link href="/dashboard" className="brand">
          <span className="brand-mark">F</span>
          <span>
            <b>
              FinSphere<span className="brand-x">X</span>
            </b>
            <small>Banking beyond borders</small>
          </span>
        </Link>
      </div>
      <main className="auth-card">
        <span className="eyebrow">WELCOME BACK</span>
        <h1>Sign in to your account</h1>
        <p className="muted">Your financial world, all in one place.</p>
        {error && <div className="notice error">{error}</div>}
        <form className="stack-form" onSubmit={submit}>
          <label>
            Email address
            <input
              name="email"
              type="email"
              autoComplete="username"
              required
              placeholder="you@example.com"
            />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={12}
              placeholder="At least 12 characters"
            />
          </label>
          <Button className="w-full" size="lg" disabled={busy}>
            {busy ? "Signing in…" : "Sign in securely"}
          </Button>
        </form>
        <p className="auth-switch">
          New to FinSphere X? <Link href="/register">Create an account</Link>
        </p>
        <div className="auth-secure">
          🔒 Protected session · 30 minute expiry
        </div>
      </main>
      <footer className="auth-footer">
        © 2026 FinSphere X · Demo environment
      </footer>
    </div>
  );
}
