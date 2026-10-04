"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  CountrySelect,
  InternationalPhoneField,
  PasswordField,
} from "@/components/auth-fields";
import { ProfileImagePicker } from "@/components/profile-image-picker";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [countryCode, setCountryCode] = useState("pk");
  const [countryName, setCountryName] = useState("Pakistan");
  const [phone, setPhone] = useState("");
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [countrySearch, setCountrySearch] = useState("Pakistan");
  const [stateValue, setStateValue] = useState("");
  const [cityValue, setCityValue] = useState("");
  const [states, setStates] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    setStates([]);
    setCities([]);
    setStateValue("");
    setCityValue("");
    if (!countryName) return;
    fetch("https://countriesnow.space/api/v0.1/countries/states", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country: countryName }),
    }).then((response) => response.json()).then((result) => {
      if (!cancelled && Array.isArray(result.data?.states)) setStates(result.data.states.map((item: { name: string }) => item.name));
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [countryName]);

  useEffect(() => {
    let cancelled = false;
    setCities([]);
    setCityValue("");
    if (!countryName || !stateValue) return;
    fetch("https://countriesnow.space/api/v0.1/countries/state/cities", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country: countryName, state: stateValue }),
    }).then((response) => response.json()).then((result) => {
      if (!cancelled && Array.isArray(result.data)) setCities(result.data);
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [countryName, stateValue]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    if (form.get("password") !== form.get("confirm_password")) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: form.get("name"),
          email: form.get("email"),
          phone,
          country: countryName,
          state: form.get("state"),
          city: form.get("city"),
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
      if (profileImage) {
        const imageData = new FormData();
        imageData.set("file", profileImage);
        await api("/customers/me/profile-image", {
          method: "POST",
          body: imageData,
        }).catch(() => undefined);
      }
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
    <div className="auth-page auth-page-register">
      <div className="auth-glow auth-glow-one" />
      <div className="auth-glow auth-glow-two" />
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
      <main className="auth-card auth-card-wide">
        <span className="eyebrow">GET STARTED</span>
        <h1>Open your account</h1>
        <p className="muted">Create your secure FinSphere X profile.</p>
        {error && <div className="notice error">{error}</div>}
        <form className="stack-form register-form" onSubmit={submit}>
          <ProfileImagePicker file={profileImage} onChange={setProfileImage} />

          <label>
            Full name
            <input
              name="name"
              required
              minLength={2}
              maxLength={160}
              autoComplete="name"
              placeholder="Your full name"
            />
          </label>
          <label>
            Email address
            <input
              name="email"
              type="email"
              required
              autoComplete="email"
              placeholder="you@example.com"
            />
          </label>

          <div className="auth-field-grid">
            <label>
              Country
              <CountrySelect
                value={countryCode}
                onChange={(code, name, dialCode) => {
                  setCountryCode(code);
                  setCountryName(name);
                  setCountrySearch(name);
                  setPhone(`+${dialCode}`);
                }}
                search={countrySearch}
                onSearch={setCountrySearch}
              />
            </label>
            <label>
              State / province
              <input
                name="state"
                autoComplete="address-level1"
                placeholder="State or province"
                required
                maxLength={100}
                list="country-states"
                value={stateValue}
                onChange={(event) => setStateValue(event.target.value)}
              />
              <datalist id="country-states">{states.map((state) => <option key={state} value={state} />)}</datalist>
            </label>
          </div>
          <label>
            City
            <input
              name="city"
              autoComplete="address-level2"
              placeholder="Your city"
              required
              maxLength={100}
              list="country-cities"
              value={cityValue}
              onChange={(event) => setCityValue(event.target.value)}
            />
            <datalist id="country-cities">{cities.map((city) => <option key={city} value={city} />)}</datalist>
          </label>
          <label>
            Phone number
            <InternationalPhoneField
              countryCode={countryCode}
              value={phone}
              onChange={setPhone}
            />
          </label>

          <PasswordField
            name="password"
            label="Password"
            autoComplete="new-password"
          />
          <small className="form-hint">
            Use at least 12 characters for a stronger password.
          </small>
          <PasswordField
            name="confirm_password"
            label="Confirm password"
            autoComplete="new-password"
          />

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
