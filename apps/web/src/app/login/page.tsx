"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, storeAuthTokens } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PasswordField } from "@/components/auth-fields";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [challengeToken, setChallengeToken] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await api<
        | { access_token: string; refresh_token: string }
        | { mfa_required: true; challenge_token: string }
      >(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: form.get("email"),
            password: form.get("password"),
          }),
        },
      );
      if ("mfa_required" in result) {
        setRememberDevice(form.get("remember_me") === "on");
        setChallengeToken(result.challenge_token);
        return;
      }
      storeAuthTokens(result.access_token, result.refresh_token, form.get("remember_me") === "on");
      router.replace("/dashboard");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }
  async function verifyMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await api<{ access_token: string; refresh_token: string }>(
        "/auth/mfa/verify",
        {
          method: "POST",
          body: JSON.stringify({ challenge_token: challengeToken, code: form.get("code") }),
        },
      );
      storeAuthTokens(result.access_token, result.refresh_token, rememberDevice);
      router.replace("/dashboard");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Authenticator verification failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow-one" />
      <div className="auth-glow auth-glow-two" />
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
        <h1>{challengeToken ? "Verify your authenticator" : "Sign in to your account"}</h1>
        <p className="muted">{challengeToken ? "Enter the current six-digit code from your authenticator app." : "Your financial world, all in one place."}</p>
        {error && <div className="notice error">{error}</div>}
        {challengeToken ? <form className="stack-form" onSubmit={verifyMfa}>
          <label>Authenticator or recovery code<input name="code" inputMode="text" autoComplete="one-time-code" minLength={6} maxLength={32} required autoFocus /></label>
          <Button className="w-full" size="lg" disabled={busy}>{busy ? "Verifying…" : "Verify and sign in"}</Button>
          <button className="text-button" type="button" onClick={() => { setChallengeToken(""); setError(""); }}>Back to password</button>
        </form> : <form className="stack-form" onSubmit={submit}>
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
          <PasswordField
            name="password"
            label="Password"
            autoComplete="current-password"
          />
          <label className="remember-me-option">
            <input name="remember_me" type="checkbox" />
            <span>Remember me on this device</span>
          </label>
          <div className="auth-forgot-row">
            <Link href="/forgot-password">Forgot password?</Link>
          </div>
          <Button className="w-full" size="lg" disabled={busy}>
            {busy ? "Signing in…" : "Sign in securely"}
          </Button>
        </form>}
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
