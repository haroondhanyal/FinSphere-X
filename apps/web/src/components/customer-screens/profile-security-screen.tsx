"use client";

import { api, clearAuthTokens } from "@/lib/api";
import { Empty, Notice, PageTitle, StatePill } from "../screen-primitives";
import { DocumentUpload, KycForm } from "../screen-actions";
import type { CustomerScreenProps } from "./types";
import { ProfileImageManager } from "./profile-image-manager";
import { type FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { signOut } from "../workspace-sidebar";

export function ProfileSecurityScreen(props: CustomerScreenProps) {
  const { pathname, profileData, error, success, run } = props;
  const cache = useQueryClient();
  const [mfaSecret, setMfaSecret] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [mfaError, setMfaError] = useState("");
  const mfaStatus = useQuery<{ enabled: boolean }>({
    queryKey: ["mfa-status"],
    queryFn: () => api("/auth/mfa/status"),
    enabled: pathname === "/security",
  });
  const sessions = useQuery<{ sessions: { id: number; created_at: string; expires_at: string; current: boolean }[] }>({
    queryKey: ["auth-sessions"],
    queryFn: () => api("/auth/sessions"),
    enabled: pathname === "/security",
  });
  async function revokeSession(id: number) {
    try {
      const result = await api<{ current_session: boolean }>(`/auth/sessions/${id}`, { method: "DELETE" });
      if (result.current_session) {
        await signOut();
        window.location.replace("/login");
        return;
      }
      await cache.invalidateQueries({ queryKey: ["auth-sessions"] });
    } catch (cause) {
      window.alert(cause instanceof Error ? cause.message : "Could not revoke session");
    }
  }
  async function setupMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMfaError("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await api<{ secret: string; recovery_codes: string[] }>("/auth/mfa/setup", { method: "POST", body: JSON.stringify(values) });
      setMfaSecret(result.secret);
      setRecoveryCodes(result.recovery_codes);
    } catch (cause) {
      setMfaError(cause instanceof Error ? cause.message : "Could not start MFA setup");
    }
  }
  async function confirmMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMfaError("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await api("/auth/mfa/enable", { method: "POST", body: JSON.stringify(values) });
      clearAuthTokens();
      window.location.replace("/login");
    } catch (cause) {
      setMfaError(cause instanceof Error ? cause.message : "Authenticator code was not accepted");
    }
  }
  async function disableMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMfaError("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await api("/auth/mfa/disable", { method: "POST", body: JSON.stringify(values) });
      clearAuthTokens();
      window.location.replace("/login");
    } catch (cause) {
      setMfaError(cause instanceof Error ? cause.message : "Could not disable MFA");
    }
  }
  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await run(
      () => api("/customers/me", { method: "PATCH", body: JSON.stringify(values) }),
      "Profile details updated.",
    );
  }
  return (
    <>
      <PageTitle
        eyebrow="PERSONAL DETAILS"
        title={pathname === "/security" ? "Security" : "Profile & KYC"}
        copy={
          pathname === "/security"
            ? "Manage your signed-in session and review your account security."
            : "Keep your customer information and verification status up to date."
        }
      />
      <Notice error={error} success={success} />
      {pathname === "/profile" && profileData ? (
        <div className="two-column">
          <ProfileImageManager />
          <div className="panel detail-list">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">CUSTOMER PROFILE</span>
                <h3>{profileData.full_name}</h3>
              </div>
              <StatePill value={profileData.kyc_status} />
            </div>
            <p>
              <span>Email</span>
              <b>{profileData.email}</b>
            </p>
            <p>
              <span>Phone</span>
              <b>{profileData.phone || "Not provided"}</b>
            </p>
            <p>
              <span>Country / State / City</span>
              <b>{[profileData.country, profileData.state, profileData.city].filter(Boolean).join(" / ") || "Not provided"}</b>
            </p>
            <p>
              <span>Nationality</span>
              <b>{profileData.nationality || "Not provided"}</b>
            </p>
            <form className="stack-form profile-edit-form" onSubmit={saveProfile}>
              <span className="eyebrow">UPDATE PERSONAL DETAILS</span>
              <label>Full name<input name="full_name" defaultValue={profileData.full_name} minLength={2} maxLength={160} required /></label>
              <label>Phone<input name="phone" defaultValue={profileData.phone || ""} maxLength={40} /></label>
              <label>Country<input name="country" defaultValue={profileData.country || ""} maxLength={100} /></label>
              <div className="profile-location-fields">
                <label>State / Province<input name="state" defaultValue={profileData.state || ""} maxLength={100} /></label>
                <label>City<input name="city" defaultValue={profileData.city || ""} maxLength={100} /></label>
              </div>
              <button className="button primary" type="submit">Save profile</button>
            </form>
            <KycForm
              onUpdate={(nationality) =>
                run(
                  () =>
                    api("/customers/me/kyc", {
                      method: "PATCH",
                      body: JSON.stringify({ nationality }),
                    }),
                  "KYC details submitted for review.",
                )
              }
            />
          </div>
          <div className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">IDENTITY DOCUMENTS</span>
                <h3>Upload for verification</h3>
              </div>
            </div>
            <DocumentUpload
              onUpload={(form) =>
                run(
                  () =>
                    api(
                      `/customers/me/kyc/documents?document_type=${encodeURIComponent(String(form.get("document_type")))}`,
                      { method: "POST", body: form },
                    ),
                  "Document uploaded for review.",
                )
              }
            />
          </div>
        </div>
      ) : pathname === "/security" ? (
        <div className="panel detail-list">
          <span className="eyebrow">SIGNED IN</span>
          <h3>Session controls</h3>
          <p>
            <span>Access token</span>
            <b>Stored in this browser session</b>
          </p>
          <p>
            <span>Authentication</span>
            <b>Email and password</b>
          </p>
          <p>
            <span>Multi-factor authentication</span>
            <b>{mfaStatus.data?.enabled ? "Authenticator app enabled" : "Not enabled"}</b>
          </p>
          {mfaError && <div className="notice error">{mfaError}</div>}
          {mfaStatus.data?.enabled ? (
            <form className="stack-form profile-edit-form" onSubmit={disableMfa}>
              <span className="eyebrow">DISABLE AUTHENTICATOR MFA</span>
              <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
              <label>Authenticator or recovery code<input name="code" autoComplete="one-time-code" inputMode="text" minLength={6} maxLength={32} required /></label>
              <button className="button" type="submit">Disable MFA and sign out</button>
            </form>
          ) : mfaSecret ? (
            <div className="panel form-stack">
              <span className="eyebrow">AUTHENTICATOR SETUP</span>
              <p>Add this secret to an authenticator app. It is shown once.</p>
              <code className="mfa-secret">{mfaSecret}</code>
              <p>Save these one-time recovery codes somewhere private. Each code works once.</p>
              <div className="mfa-recovery-codes">{recoveryCodes.map((code) => <code key={code}>{code}</code>)}</div>
              <form className="stack-form" onSubmit={confirmMfa}>
                <label>Current authenticator code<input name="code" inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} required /></label>
                <button className="button primary" type="submit">Confirm and enable MFA</button>
              </form>
            </div>
          ) : (
            <form className="stack-form profile-edit-form" onSubmit={setupMfa}>
              <span className="eyebrow">ENABLE AUTHENTICATOR MFA</span>
              <p className="form-hint">Use a TOTP authenticator app. You will need your password and a current authenticator code.</p>
              <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
              <button className="button primary" type="submit">Set up MFA</button>
            </form>
          )}
          <div className="info-banner">
            Use a unique password. Your session expires after 30 minutes.
          </div>
          <section className="session-list" aria-labelledby="sessions-title">
            <div className="panel-heading">
              <div><span className="eyebrow">ACCOUNT ACCESS</span><h3 id="sessions-title">Active sessions</h3></div>
            </div>
            {sessions.error ? <p className="notice error">{sessions.error.message}</p> : null}
            {sessions.data?.sessions.length ? sessions.data.sessions.map((session) => (
              <div className="session-row" key={session.id}>
                <div>
                  <b>{session.current ? "This session" : "Signed-in session"}</b>
                  <small>Started {new Date(session.created_at).toLocaleString()} · Expires {new Date(session.expires_at).toLocaleString()}</small>
                </div>
                <button className="button" type="button" onClick={() => void revokeSession(session.id)}>
                  {session.current ? "Sign out" : "Revoke"}
                </button>
              </div>
            )) : !sessions.isLoading && <p className="muted">No active sessions found.</p>}
          </section>
        </div>
      ) : (
        <Empty text="Loading customer profile…" />
      )}
    </>
  );
}
