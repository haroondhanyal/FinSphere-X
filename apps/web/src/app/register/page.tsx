"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: form.get("name"),
          email: form.get("email"),
          phone: form.get("phone"),
          password: form.get("password"),
        }),
      });
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
      setError(
        cause instanceof Error ? cause.message : "Unable to create account",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Link href="/login" className="brand">
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
        <span className="eyebrow">GET STARTED</span>
        <h1>Open your account</h1>
        <p className="muted">Create your secure FinSphere X profile.</p>
        {error && <div className="notice error">{error}</div>}
        <form className="stack-form" onSubmit={submit}>
          <label>
            Full name
            <input
              name="name"
              required
              minLength={2}
              maxLength={160}
              autoComplete="name"
            />
          </label>
          <label>
            Email address
            <input name="email" type="email" required autoComplete="email" />
          </label>
          <label>
            Phone number
            <input name="phone" type="tel" autoComplete="tel" />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              required
              minLength={12}
              autoComplete="new-password"
            />
            <small className="form-hint">Use at least 12 characters.</small>
          </label>
          <Button className="w-full" size="lg" disabled={busy}>
            {busy ? "Creating account…" : "Create secure account"}
          </Button>
        </form>
        <p className="auth-switch">
          Already registered? <Link href="/login">Sign in</Link>
        </p>
        <div className="auth-secure">
          Your password is protected with a one-way password hash.
        </div>
      </main>
      <footer className="auth-footer">
        © 2026 FinSphere X · Demo environment
      </footer>
    </div>
  );
}
