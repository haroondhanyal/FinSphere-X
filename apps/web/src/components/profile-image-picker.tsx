"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import { ImagePlus, Pencil, Trash2, UserRound } from "lucide-react";
import Image from "next/image";

export function ProfileImagePicker({
  file,
  onChange,
  initialImageUrl,
}: {
  file: File | null;
  onChange: (file: File | null) => void;
  initialImageUrl?: string;
}) {
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    event.target.value = "";
    if (!selected) return;
    if (!selected.type.startsWith("image/")) {
      setError("Choose an image file.");
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError("Image must be 10 MB or smaller.");
      return;
    }
    setError("");
    onChange(selected);
  }

  return (
    <div className="profile-image-picker">
      <span className="profile-image-preview">
        {preview || initialImageUrl ? (
          <Image
            src={preview || initialImageUrl || ""}
            alt="Profile photo preview"
            width={88}
            height={88}
            unoptimized
          />
        ) : (
          <UserRound size={25} />
        )}
      </span>
      <div className="profile-image-controls">
        <b>Profile photo <small>Optional</small></b>
        <span className="profile-image-buttons">
          <label className="auth-secondary-button" htmlFor="profile-photo">
            {file || initialImageUrl ? <Pencil size={14} /> : <ImagePlus size={14} />}
            {file || initialImageUrl ? "Edit image" : "Add image"}
          </label>
          {file && (
            <button className="auth-secondary-button remove-photo" type="button" onClick={() => onChange(null)}>
              <Trash2 size={14} /> Remove
            </button>
          )}
        </span>
        <small className="form-hint">JPEG, PNG or WebP · up to 10 MB</small>
        {error && <small className="photo-error">{error}</small>}
        <input
          id="profile-photo"
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={selectFile}
        />
      </div>
    </div>
  );
}
