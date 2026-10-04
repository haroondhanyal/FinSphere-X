"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PasswordField } from "@/components/auth-fields";

export default function ResetPasswordPage() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") ?? "");
    if (password !== form.get("confirm_password")) {
      setError("Passwords do not match.");
      setBusy(false);
      return;
    }
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setError("This reset link is missing its token. Request a new link.");
      setBusy(false);
      return;
    }
    try {
      const result = await api<{ message: string }>(
        "/auth/password-reset/confirm",
        {
          method: "POST",
          body: JSON.stringify({ token, new_password: password }),
        },
      );
      setMessage(result.message);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not reset password");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow-one" />
      <div className="auth-glow auth-glow-two" />
      <div className="auth-brand">
        <Link href="/login" className="brand">
          <span className="brand-mark">F</span>
          <span><b>FinSphere<span className="brand-x">X</span></b><small>Banking beyond borders</small></span>
        </Link>
      </div>
      <main className="auth-card">
        <span className="eyebrow">CHOOSE A NEW PASSWORD</span>
        <h1>Reset your password</h1>
        <p className="muted">Use at least 12 characters. Reset links expire after 20 minutes.</p>
        {error && <div className="notice error">{error}</div>}
        {message && <div className="notice success">{message}</div>}
        {!message && (
          <form className="stack-form" onSubmit={submit}>
            <PasswordField name="password" label="New password" autoComplete="new-password" />
            <PasswordField name="confirm_password" label="Confirm new password" autoComplete="new-password" />
            <Button className="w-full" size="lg" disabled={busy}>
              {busy ? "Updating…" : "Update password"}
            </Button>
          </form>
        )}
        <p className="auth-switch"><Link href="/login">Back to sign in</Link></p>
      </main>
      <footer className="auth-footer">© 2026 FinSphere X · Secure account recovery</footer>
    </div>
  );
}
