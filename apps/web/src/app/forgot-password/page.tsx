"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");
    const email = new FormData(event.currentTarget).get("email");
    try {
      const result = await api<{
        message: string;
        email_delivery_configured: boolean;
      }>("/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMessage(
        result.email_delivery_configured
          ? result.message
          : "Password recovery email is not configured yet. Please contact your administrator.",
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not request a reset link");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow-one" />
      <div className="auth-glow auth-glow-two" />
      <AuthBrand />
      <main className="auth-card">
        <span className="eyebrow">ACCOUNT RECOVERY</span>
        <h1>Forgot your password?</h1>
        <p className="muted">Enter the email address on your FinSphere X account.</p>
        {error && <div className="notice error">{error}</div>}
        {message && <div className="notice success">{message}</div>}
        <form className="stack-form" onSubmit={submit}>
          <label>
            Email address
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <Button className="w-full" size="lg" disabled={busy}>
            {busy ? "Sending…" : "Send reset link"}
          </Button>
        </form>
        <p className="auth-switch">
          Remembered it? <Link href="/login">Back to sign in</Link>
        </p>
      </main>
      <footer className="auth-footer">© 2026 FinSphere X · Secure account recovery</footer>
    </div>
  );
}

function AuthBrand() {
  return (
    <div className="auth-brand">
      <Link href="/login" className="brand">
        <span className="brand-mark">F</span>
        <span>
          <b>FinSphere<span className="brand-x">X</span></b>
          <small>Banking beyond borders</small>
        </span>
      </Link>
    </div>
  );
}
