"use client";

import { useEffect, useRef, useState } from "react";
import { api, getAuthToken } from "@/lib/api";
import { ProfileImagePicker } from "../profile-image-picker";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function ProfileImageManager() {
  const [imageUrl, setImageUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const imageUrlRef = useRef("");

  function replaceImageUrl(nextUrl: string) {
    if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    imageUrlRef.current = nextUrl;
    setImageUrl(nextUrl);
  }

  async function loadImage() {
    const token = getAuthToken();
    if (!token) return;
    const response = await fetch(`${API_URL}/customers/me/profile-image`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      if (response.status === 404) setImageUrl("");
      return;
    }
    const nextUrl = URL.createObjectURL(await response.blob());
    replaceImageUrl(nextUrl);
  }

  useEffect(() => {
    void loadImage();
    return () => {
      if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    };
    // Load once when the manager mounts; later saves reload explicitly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save() {
    if (!file) return;
    setBusy(true);
    setMessage("");
    try {
      const form = new FormData();
      form.set("file", file);
      await api("/customers/me/profile-image", { method: "POST", body: form });
      setFile(null);
      await loadImage();
      setMessage("Profile photo updated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save photo.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setMessage("");
    try {
      await api("/customers/me/profile-image", { method: "DELETE" });
      replaceImageUrl("");
      setFile(null);
      setMessage("Profile photo removed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not remove photo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel profile-photo-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">PROFILE PHOTO</span>
          <h3>Personalize your account</h3>
        </div>
      </div>
      <ProfileImagePicker file={file} onChange={setFile} initialImageUrl={imageUrl} />
      <div className="profile-photo-actions">
        <button className="photo-action primary-button" type="button" disabled={!file || busy} onClick={save}>
          {busy ? "Saving…" : "Save photo"}
        </button>
        <button className="photo-action auth-secondary-button" type="button" disabled={!imageUrl || busy} onClick={remove}>
          Remove photo
        </button>
      </div>
      {message && <small className="form-hint">{message}</small>}
    </section>
  );
}
